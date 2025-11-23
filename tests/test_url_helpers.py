"""
Unit tests for jobber.url_helpers module.

Tests verify:
- Happy path behavior
- Error cases (TypeError, KeyError, ValueError)
- Edge cases (None, empty strings, encoding)
- ANSI formatting (OSC 8 standard)
"""

import pytest

from jobber.url_helpers import clickable_link, format_success, validate_url


class TestFormatSuccess:
    """Tests for format_success() function"""

    def test_valid_input_returns_formatted_message(self):
        """Happy path: valid input returns formatted success message"""
        resource_data = {
            "id": "123",
            "name": "John Doe",
            "jobberWebUri": "https://secure.getjobber.com/clients/123",
        }

        result = format_success("Client", resource_data, name_field="name")

        assert result == (
            "✅ Client created: John Doe\n"
            "🔗 View in Jobber: https://secure.getjobber.com/clients/123"
        )

    def test_name_field_fallback_to_id_when_missing(self):
        """When name_field missing, falls back to id"""
        resource_data = {"id": "123", "jobberWebUri": "https://secure.getjobber.com/clients/123"}

        result = format_success("Client", resource_data, name_field="name")

        assert "Client created: 123" in result

    def test_custom_name_field_parameter(self):
        """Custom name_field parameter uses correct field"""
        resource_data = {
            "id": "123",
            "firstName": "John",
            "jobberWebUri": "https://secure.getjobber.com/clients/123",
        }

        result = format_success("Client", resource_data, name_field="firstName")

        assert "Client created: John" in result

    def test_raises_typeerror_when_resource_data_not_dict(self):
        """TypeError when resource_data is not a dict"""
        with pytest.raises(TypeError, match="resource_data must be dict"):
            format_success("Client", "not_a_dict")

        with pytest.raises(TypeError, match="resource_data must be dict"):
            format_success("Client", None)

        with pytest.raises(TypeError, match="resource_data must be dict"):
            format_success("Client", ["list"])

    def test_raises_keyerror_when_id_missing(self):
        """KeyError when id field missing"""
        resource_data = {"name": "John", "jobberWebUri": "https://secure.getjobber.com/clients/123"}

        with pytest.raises(KeyError, match="missing required field: 'id'"):
            format_success("Client", resource_data)

    def test_raises_keyerror_when_jobberweb_uri_missing(self):
        """KeyError when jobberWebUri missing with helpful message"""
        resource_data = {"id": "123", "name": "John"}

        with pytest.raises(KeyError, match="missing required field: 'jobberWebUri'"):
            format_success("Client", resource_data)

        # Verify helpful message suggests including field in query
        with pytest.raises(KeyError, match="Include this field in your GraphQL query"):
            format_success("Client", resource_data)


class TestClickableLink:
    """Tests for clickable_link() function"""

    def test_produces_ansi_osc8_format(self):
        """ANSI OSC 8 hyperlink format correctly generated"""
        result = clickable_link("https://example.com", "Example")

        # OSC 8 format: \033]8;;URL\033\\TEXT\033]8;;\033\\
        expected = "\033]8;;https://example.com\033\\Example\033]8;;\033\\"
        assert result == expected

    def test_text_defaults_to_url_when_not_provided(self):
        """When text=None, uses URL as display text"""
        result = clickable_link("https://example.com")

        # Should use URL as text
        assert "https://example.com" in result
        # Should still have ANSI codes
        assert "\033]8;;" in result

    def test_text_defaults_to_url_when_explicitly_none(self):
        """When text explicitly None, uses URL as display text"""
        result = clickable_link("https://example.com", None)

        expected = "\033]8;;https://example.com\033\\https://example.com\033]8;;\033\\"
        assert result == expected

    def test_raises_typeerror_when_url_not_string(self):
        """TypeError when url is not a string"""
        with pytest.raises(TypeError, match="url must be str"):
            clickable_link(123, "text")

        with pytest.raises(TypeError, match="url must be str"):
            clickable_link(None, "text")

    def test_raises_typeerror_when_text_not_string_or_none(self):
        """TypeError when text is not string or None"""
        with pytest.raises(TypeError, match="text must be str or None"):
            clickable_link("https://example.com", 123)

        with pytest.raises(TypeError, match="text must be str or None"):
            clickable_link("https://example.com", ["list"])


class TestValidateUrl:
    """Tests for validate_url() function"""

    def test_valid_jobberweb_uri_returns_url(self):
        """Happy path: valid jobberWebUri returns URL string"""
        resource_data = {"id": "123", "jobberWebUri": "https://secure.getjobber.com/clients/123"}

        result = validate_url(resource_data)

        assert result == "https://secure.getjobber.com/clients/123"

    def test_custom_field_parameter(self):
        """Custom field parameter validates different URL field"""
        resource_data = {"id": "123", "previewUrl": "https://clienthub.getjobber.com/quotes/123"}

        result = validate_url(resource_data, field="previewUrl")

        assert result == "https://clienthub.getjobber.com/quotes/123"

    def test_raises_typeerror_when_resource_data_not_dict(self):
        """TypeError when resource_data is not a dict"""
        with pytest.raises(TypeError, match="resource_data must be dict"):
            validate_url("not_a_dict")

        with pytest.raises(TypeError, match="resource_data must be dict"):
            validate_url(None)

    def test_raises_keyerror_when_field_missing(self):
        """KeyError when URL field missing"""
        resource_data = {"id": "123"}

        with pytest.raises(KeyError, match="jobberWebUri field missing or null"):
            validate_url(resource_data)

        # Verify helpful message
        with pytest.raises(KeyError, match="Include 'jobberWebUri' in your GraphQL query"):
            validate_url(resource_data)

    def test_raises_keyerror_when_field_is_none(self):
        """KeyError when URL field is None"""
        resource_data = {"id": "123", "jobberWebUri": None}

        with pytest.raises(KeyError, match="jobberWebUri field missing or null"):
            validate_url(resource_data)

    def test_raises_valueerror_when_field_is_empty_string(self):
        """ValueError when URL field is empty string"""
        resource_data = {"id": "123", "jobberWebUri": ""}

        with pytest.raises(ValueError, match="jobberWebUri is empty string"):
            validate_url(resource_data)

    def test_raises_valueerror_when_field_is_whitespace_only(self):
        """ValueError when URL field is whitespace only"""
        resource_data = {"id": "123", "jobberWebUri": "   "}

        with pytest.raises(ValueError, match="jobberWebUri is empty string"):
            validate_url(resource_data)

    def test_raises_typeerror_when_field_value_not_string(self):
        """TypeError when URL field value is not a string"""
        resource_data = {
            "id": "123",
            "jobberWebUri": 12345,  # Not a string
        }

        with pytest.raises(TypeError, match="jobberWebUri must be str"):
            validate_url(resource_data)
