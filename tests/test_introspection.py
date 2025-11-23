"""Unit tests for jobber.introspection module (GraphQL schema introspection)."""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from jobber.introspection import (
    clear_schema_cache,
    compare_schemas,
    extract_field_descriptions,
    get_schema,
)


class TestGetSchema:
    """Test GraphQL schema introspection with caching."""

    @patch("jobber.introspection.CACHE_FILE")
    def test_fetches_schema_from_api_when_no_cache(self, mock_cache_file: Mock) -> None:
        """get_schema() fetches from API when cache doesn't exist."""
        # Mock Path object methods
        mock_cache_file.exists.return_value = False
        mock_cache_file.parent.mkdir = Mock()
        mock_cache_file.write_text = Mock()

        mock_client = Mock()
        mock_client.execute_query.return_value = {
            "data": {
                "__schema": {
                    "queryType": {"name": "Query"},
                    "mutationType": {"name": "Mutation"},
                    "types": [
                        {
                            "kind": "OBJECT",
                            "name": "Client",
                            "fields": [
                                {"name": "id", "description": "Client ID"},
                                {"name": "firstName", "description": "First name"},
                            ],
                        }
                    ],
                }
            }
        }

        schema = get_schema(mock_client, use_cache=True)

        # Verify API was called
        mock_client.execute_query.assert_called_once()

        # Verify cache directory created
        mock_cache_file.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)

        # Verify schema written to cache
        mock_cache_file.write_text.assert_called_once()
        written_data = json.loads(mock_cache_file.write_text.call_args[0][0])
        assert written_data["__schema"]["queryType"]["name"] == "Query"

        # Verify schema returned
        assert schema["__schema"]["queryType"]["name"] == "Query"
        assert schema["__schema"]["types"][0]["name"] == "Client"

    @patch("jobber.introspection.CACHE_FILE")
    def test_returns_cached_schema_when_available(self, mock_cache_file: Mock) -> None:
        """get_schema() returns cached schema without API call."""
        cached_schema = {
            "__schema": {
                "queryType": {"name": "Query"},
                "types": [{"name": "Client", "fields": [{"name": "id"}]}],
            }
        }

        # Mock Path object methods
        mock_cache_file.exists.return_value = True
        mock_cache_file.read_text.return_value = json.dumps(cached_schema)

        mock_client = Mock()

        schema = get_schema(mock_client, use_cache=True)

        # Verify API NOT called (cache hit)
        mock_client.execute_query.assert_not_called()

        # Verify cache was read
        mock_cache_file.read_text.assert_called_once()

        # Verify schema from cache
        assert schema["__schema"]["queryType"]["name"] == "Query"
        assert schema["__schema"]["types"][0]["name"] == "Client"

    @patch("jobber.introspection.CACHE_FILE")
    def test_fetches_fresh_schema_when_cache_corrupted(self, mock_cache_file: Mock) -> None:
        """get_schema() fetches fresh schema when cache is corrupted JSON."""
        # Mock Path object methods
        mock_cache_file.exists.return_value = True
        mock_cache_file.read_text.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_cache_file.parent.mkdir = Mock()
        mock_cache_file.write_text = Mock()

        mock_client = Mock()
        mock_client.execute_query.return_value = {
            "data": {"__schema": {"queryType": {"name": "Query"}, "types": []}}
        }

        schema = get_schema(mock_client, use_cache=True)

        # Verify API was called (cache invalid)
        mock_client.execute_query.assert_called_once()

        # Verify fresh schema written to cache
        mock_cache_file.write_text.assert_called_once()

        # Verify schema returned
        assert schema["__schema"]["queryType"]["name"] == "Query"

    @patch("jobber.introspection.CACHE_FILE")
    def test_bypasses_cache_when_use_cache_false(self, mock_cache_file: Mock) -> None:
        """get_schema() bypasses cache when use_cache=False."""
        # Mock Path object methods (should not be called)
        mock_cache_file.exists.return_value = False
        mock_cache_file.parent.mkdir = Mock()
        mock_cache_file.write_text = Mock()

        mock_client = Mock()
        mock_client.execute_query.return_value = {
            "data": {"__schema": {"queryType": {"name": "Query"}, "types": []}}
        }

        schema = get_schema(mock_client, use_cache=False)

        # Verify API was called
        mock_client.execute_query.assert_called_once()

        # Verify schema returned
        assert schema["__schema"]["queryType"]["name"] == "Query"


class TestExtractFieldDescriptions:
    """Test field description extraction from schema."""

    def test_extracts_field_descriptions_for_type(self) -> None:
        """extract_field_descriptions() returns field name → description mapping."""
        schema = {
            "__schema": {
                "types": [
                    {
                        "name": "Client",
                        "fields": [
                            {"name": "id", "description": "Client ID"},
                            {"name": "firstName", "description": "Client first name"},
                            {"name": "lastName", "description": "Client last name"},
                        ],
                    }
                ]
            }
        }

        descriptions = extract_field_descriptions(schema, "Client")

        assert descriptions == {
            "id": "Client ID",
            "firstName": "Client first name",
            "lastName": "Client last name",
        }

    def test_handles_fields_without_descriptions(self) -> None:
        """extract_field_descriptions() handles fields missing description."""
        schema = {
            "__schema": {
                "types": [
                    {
                        "name": "Quote",
                        "fields": [
                            {"name": "id", "description": "Quote ID"},
                            {"name": "total"},  # No description
                        ],
                    }
                ]
            }
        }

        descriptions = extract_field_descriptions(schema, "Quote")

        assert descriptions["id"] == "Quote ID"
        assert descriptions["total"] == "No description available"

    def test_raises_keyerror_when_type_not_found(self) -> None:
        """extract_field_descriptions() raises KeyError for unknown type."""
        schema = {"__schema": {"types": [{"name": "Client", "fields": []}]}}

        with pytest.raises(KeyError, match="Type 'Invoice' not found"):
            extract_field_descriptions(schema, "Invoice")

    def test_handles_type_without_fields(self) -> None:
        """extract_field_descriptions() handles types without fields (scalars, enums)."""
        schema = {
            "__schema": {
                "types": [
                    {"name": "String", "kind": "SCALAR"},  # No fields
                ]
            }
        }

        descriptions = extract_field_descriptions(schema, "String")

        assert descriptions == {}


class TestCompareSchemas:
    """Test schema comparison for breaking changes."""

    def test_detects_added_types(self) -> None:
        """compare_schemas() detects newly added types."""
        old_schema = {
            "__schema": {
                "types": [
                    {"name": "Client", "fields": []},
                    {"name": "Quote", "fields": []},
                ]
            }
        }

        new_schema = {
            "__schema": {
                "types": [
                    {"name": "Client", "fields": []},
                    {"name": "Quote", "fields": []},
                    {"name": "Invoice", "fields": []},  # Added
                ]
            }
        }

        changes = compare_schemas(old_schema, new_schema)

        assert "Invoice" in changes["added_types"]
        assert changes["removed_types"] == []

    def test_detects_removed_types(self) -> None:
        """compare_schemas() detects removed types (breaking change)."""
        old_schema = {
            "__schema": {
                "types": [
                    {"name": "Client", "fields": []},
                    {"name": "Quote", "fields": []},
                    {"name": "LegacyType", "fields": []},
                ]
            }
        }

        new_schema = {
            "__schema": {
                "types": [
                    {"name": "Client", "fields": []},
                    {"name": "Quote", "fields": []},
                    # LegacyType removed
                ]
            }
        }

        changes = compare_schemas(old_schema, new_schema)

        assert "LegacyType" in changes["removed_types"]
        assert changes["added_types"] == []

    def test_detects_added_fields(self) -> None:
        """compare_schemas() detects newly added fields."""
        old_schema = {
            "__schema": {
                "types": [
                    {
                        "name": "Client",
                        "fields": [
                            {"name": "id"},
                            {"name": "firstName"},
                        ],
                    }
                ]
            }
        }

        new_schema = {
            "__schema": {
                "types": [
                    {
                        "name": "Client",
                        "fields": [
                            {"name": "id"},
                            {"name": "firstName"},
                            {"name": "email"},  # Added
                        ],
                    }
                ]
            }
        }

        changes = compare_schemas(old_schema, new_schema)

        assert "Client" in changes["added_fields"]
        assert "email" in changes["added_fields"]["Client"]

    def test_detects_removed_fields(self) -> None:
        """compare_schemas() detects removed fields (breaking change)."""
        old_schema = {
            "__schema": {
                "types": [
                    {
                        "name": "Client",
                        "fields": [
                            {"name": "id"},
                            {"name": "firstName"},
                            {"name": "legacyField"},
                        ],
                    }
                ]
            }
        }

        new_schema = {
            "__schema": {
                "types": [
                    {
                        "name": "Client",
                        "fields": [
                            {"name": "id"},
                            {"name": "firstName"},
                            # legacyField removed
                        ],
                    }
                ]
            }
        }

        changes = compare_schemas(old_schema, new_schema)

        assert "Client" in changes["removed_fields"]
        assert "legacyField" in changes["removed_fields"]["Client"]

    def test_ignores_types_without_fields(self) -> None:
        """compare_schemas() ignores scalars and enums (no fields)."""
        old_schema = {
            "__schema": {
                "types": [
                    {"name": "String", "kind": "SCALAR"},  # No fields
                    {"name": "Client", "fields": [{"name": "id"}]},
                ]
            }
        }

        new_schema = {
            "__schema": {
                "types": [
                    {"name": "String", "kind": "SCALAR"},
                    {"name": "Client", "fields": [{"name": "id"}]},
                ]
            }
        }

        changes = compare_schemas(old_schema, new_schema)

        assert changes["added_fields"] == {}
        assert changes["removed_fields"] == {}


class TestClearSchemaCache:
    """Test schema cache clearing."""

    @patch("jobber.introspection.CACHE_FILE")
    def test_deletes_cache_file_when_exists(self, mock_cache_file: Mock) -> None:
        """clear_schema_cache() deletes cache file and returns True."""
        mock_cache_file.exists.return_value = True
        mock_cache_file.unlink = Mock()

        result = clear_schema_cache()

        mock_cache_file.unlink.assert_called_once()
        assert result is True

    @patch("jobber.introspection.CACHE_FILE")
    def test_returns_false_when_cache_not_exists(self, mock_cache_file: Mock) -> None:
        """clear_schema_cache() returns False when cache doesn't exist."""
        mock_cache_file.exists.return_value = False
        mock_cache_file.unlink = Mock()

        result = clear_schema_cache()

        mock_cache_file.unlink.assert_not_called()
        assert result is False
