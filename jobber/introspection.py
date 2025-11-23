"""
GraphQL schema introspection for Jobber API.

Provides schema queries, field description extraction, and caching to support
AI agents with dynamic type validation and reduced hallucination.

Example usage:
    from jobber import JobberClient
    from jobber.introspection import get_schema, extract_field_descriptions

    client = JobberClient.from_doppler()

    # Get schema (uses cache if available)
    schema = get_schema(client)

    # Extract field descriptions for AI context
    client_fields = extract_field_descriptions(schema, "Client")
    print(client_fields["firstName"])  # "The client's first name"
"""

import json
from pathlib import Path
from typing import Any

# GraphQL introspection query (standard __schema query)
INTROSPECTION_QUERY = """
    query IntrospectionQuery {
        __schema {
            queryType { name }
            mutationType { name }
            subscriptionType { name }
            types {
                kind
                name
                description
                fields(includeDeprecated: true) {
                    name
                    description
                    args {
                        name
                        description
                        type {
                            kind
                            name
                            ofType {
                                kind
                                name
                            }
                        }
                    }
                    type {
                        kind
                        name
                        ofType {
                            kind
                            name
                        }
                    }
                    isDeprecated
                    deprecationReason
                }
                inputFields {
                    name
                    description
                    type {
                        kind
                        name
                        ofType {
                            kind
                            name
                        }
                    }
                }
                interfaces {
                    kind
                    name
                }
                enumValues(includeDeprecated: true) {
                    name
                    description
                    isDeprecated
                    deprecationReason
                }
                possibleTypes {
                    kind
                    name
                }
            }
            directives {
                name
                description
                locations
                args {
                    name
                    description
                }
            }
        }
    }
"""

# Default cache location
CACHE_FILE = Path.home() / ".cache" / "jobber" / "schema.json"


def get_schema(client: Any, use_cache: bool = True) -> dict[str, Any]:
    """
    Get Jobber GraphQL schema via introspection.

    Executes __schema query against Jobber API to retrieve complete schema
    including types, fields, descriptions, and directives. Caches result to
    disk to avoid repeated introspection calls.

    Args:
        client: JobberClient instance
        use_cache: Use cached schema if available (default: True)

    Returns:
        Dictionary with schema data (includes 'types', 'queryType', 'mutationType')

    Raises:
        JobberException: If introspection query fails

    Example:
        >>> from jobber import JobberClient
        >>> client = JobberClient.from_doppler()
        >>> schema = get_schema(client)
        >>> len(schema['__schema']['types'])
        150  # Approximate number of types in Jobber schema
    """
    # Check cache if enabled
    if use_cache and CACHE_FILE.exists():
        try:
            cached_schema = json.loads(CACHE_FILE.read_text())
            return cached_schema  # type: ignore[no-any-return]
        except (json.JSONDecodeError, OSError):
            # Cache corrupted or unreadable, fetch fresh schema
            pass

    # Fetch schema from API
    result = client.execute_query(INTROSPECTION_QUERY)
    schema = result["data"]  # type: ignore[assignment]

    # Cache to disk
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(schema, indent=2))

    return schema  # type: ignore[no-any-return]


def extract_field_descriptions(schema: dict[str, Any], type_name: str) -> dict[str, str]:
    """
    Extract field descriptions for a specific GraphQL type.

    Parses schema to find type and extract field names + descriptions for
    AI context. Useful for providing AI agents with field-level documentation.

    Args:
        schema: GraphQL schema from get_schema()
        type_name: Type name to extract fields from (e.g., "Client", "Quote")

    Returns:
        Dictionary mapping field names to descriptions

    Raises:
        KeyError: If type not found in schema

    Example:
        >>> schema = get_schema(client)
        >>> client_fields = extract_field_descriptions(schema, "Client")
        >>> client_fields["firstName"]
        'The first name of the client'
        >>> client_fields["jobberWebUri"]
        'URL to view client in Jobber web interface'
    """
    # Find type in schema
    types = schema["__schema"]["types"]
    target_type = None

    for t in types:
        if t["name"] == type_name:
            target_type = t
            break

    if not target_type:
        raise KeyError(f"Type '{type_name}' not found in schema")

    # Extract field descriptions
    field_descriptions = {}

    if target_type.get("fields"):
        for field in target_type["fields"]:
            field_name = field["name"]
            description = field.get("description", "No description available")
            field_descriptions[field_name] = description

    return field_descriptions


def compare_schemas(old_schema: dict[str, Any], new_schema: dict[str, Any]) -> dict[str, Any]:
    """
    Compare two schemas to detect breaking changes.

    Identifies added/removed types and fields between schema versions. Useful
    for detecting when Jobber API updates break existing queries.

    Args:
        old_schema: Previous schema from get_schema()
        new_schema: Current schema from get_schema()

    Returns:
        Dictionary with 'added_types', 'removed_types', 'added_fields', 'removed_fields'

    Example:
        >>> old_schema = get_schema(client, use_cache=True)
        >>> new_schema = get_schema(client, use_cache=False)  # Fresh from API
        >>> changes = compare_schemas(old_schema, new_schema)
        >>> if changes['removed_fields']:
        ...     print("Warning: Fields removed from schema!")
        ...     print(changes['removed_fields'])
    """
    old_types = {t["name"]: t for t in old_schema["__schema"]["types"]}
    new_types = {t["name"]: t for t in new_schema["__schema"]["types"]}

    # Detect type changes
    added_types = set(new_types.keys()) - set(old_types.keys())
    removed_types = set(old_types.keys()) - set(new_types.keys())

    # Detect field changes (for types that exist in both schemas)
    added_fields: dict[str, list[str]] = {}
    removed_fields: dict[str, list[str]] = {}

    common_types = set(old_types.keys()) & set(new_types.keys())

    for type_name in common_types:
        old_type = old_types[type_name]
        new_type = new_types[type_name]

        # Only compare types with fields (OBJECT and INTERFACE kinds)
        if old_type.get("fields") and new_type.get("fields"):
            old_field_names = {f["name"] for f in old_type["fields"]}
            new_field_names = {f["name"] for f in new_type["fields"]}

            added = new_field_names - old_field_names
            removed = old_field_names - new_field_names

            if added:
                added_fields[type_name] = list(added)
            if removed:
                removed_fields[type_name] = list(removed)

    return {
        "added_types": list(added_types),
        "removed_types": list(removed_types),
        "added_fields": added_fields,
        "removed_fields": removed_fields,
    }


def clear_schema_cache() -> bool:
    """
    Delete cached schema file.

    Forces next get_schema() call to fetch fresh schema from API.

    Returns:
        True if cache file was deleted, False if it didn't exist

    Example:
        >>> clear_schema_cache()
        True
        >>> schema = get_schema(client)  # Fetches fresh from API
    """
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
        return True
    return False


__all__ = [
    "INTROSPECTION_QUERY",
    "CACHE_FILE",
    "get_schema",
    "extract_field_descriptions",
    "compare_schemas",
    "clear_schema_cache",
]
