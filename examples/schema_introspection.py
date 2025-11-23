#!/usr/bin/env python3
"""
GraphQL schema introspection example for AI agent context.

This example demonstrates how to:
1. Introspect Jobber GraphQL schema
2. Extract field descriptions for AI context
3. Compare schema versions to detect changes
4. Use schema caching for performance

Prerequisites:
- Jobber OAuth tokens in Doppler

Usage:
    python examples/schema_introspection.py
"""

# /// script
# dependencies = []
# ///

from jobber import JobberClient
from jobber.introspection import (
    CACHE_FILE,
    clear_schema_cache,
    compare_schemas,
    extract_field_descriptions,
    get_schema,
)


def main():
    print("=" * 70)
    print("🔍 Jobber GraphQL Schema Introspection")
    print("=" * 70)
    print()

    # Step 1: Get schema (with caching)
    print("Step 1: Fetching GraphQL schema...")
    print(f"   Cache location: {CACHE_FILE}")

    try:
        client = JobberClient.from_doppler()

        # First call: fetch from API (or use cache if available)
        schema = get_schema(client, use_cache=True)

        if CACHE_FILE.exists():
            print("   ✅ Schema loaded from cache")
        else:
            print("   ✅ Schema fetched from API and cached")

        types_count = len(schema["__schema"]["types"])
        print(f"   📊 Total types in schema: {types_count}")

    except Exception as e:
        print(f"   ❌ Failed to fetch schema: {e}")
        return

    print()

    # Step 2: Extract field descriptions for AI context
    print("Step 2: Extracting field descriptions for AI context...")

    type_names = ["Client", "Quote", "Visit", "Invoice"]

    for type_name in type_names:
        try:
            fields = extract_field_descriptions(schema, type_name)
            print(f"\n   📋 {type_name} type ({len(fields)} fields):")

            # Show first 3 fields as examples
            for i, (field_name, description) in enumerate(list(fields.items())[:3]):
                desc_preview = description[:60] + "..." if len(description) > 60 else description
                print(f"      - {field_name}: {desc_preview}")

            if len(fields) > 3:
                print(f"      ... and {len(fields) - 3} more fields")

        except KeyError as e:
            print(f"   ⚠️  {e}")

    print()

    # Step 3: AI Agent Usage Pattern
    print("Step 3: AI Agent Usage Pattern")
    print()
    print("   Example: AI agent constructs GraphQL query for Client")
    print()

    try:
        client_fields = extract_field_descriptions(schema, "Client")

        # AI agent reads field descriptions to understand available fields
        print("   Available Client fields for query:")
        important_fields = ["id", "firstName", "lastName", "email", "jobberWebUri"]

        for field in important_fields:
            if field in client_fields:
                desc = client_fields[field]
                print(f"      - {field}: {desc}")

        print()
        print("   AI agent constructs query:")
        print("   query {")
        print("     clients(first: 10) {")
        print("       nodes {")
        for field in important_fields:
            if field in client_fields:
                print(f"         {field}")
        print("       }")
        print("     }")
        print("   }")

    except KeyError as e:
        print(f"   ⚠️  {e}")

    print()

    # Step 4: Schema version comparison
    print("Step 4: Comparing schema versions (detect API changes)...")

    # Clear cache and fetch fresh schema
    print("   Clearing cache and fetching fresh schema...")
    clear_schema_cache()

    try:
        fresh_schema = get_schema(client, use_cache=False)
        print("   ✅ Fresh schema fetched")

        # Compare cached vs fresh (in real use, compare old cache vs new fetch)
        changes = compare_schemas(schema, fresh_schema)

        if any(
            [
                changes["added_types"],
                changes["removed_types"],
                changes["added_fields"],
                changes["removed_fields"],
            ]
        ):
            print("   ⚠️  Schema changes detected!")

            if changes["removed_types"]:
                print(f"      Removed types: {changes['removed_types']}")
            if changes["removed_fields"]:
                print(f"      Removed fields: {changes['removed_fields']}")

        else:
            print("   ✅ No schema changes detected (schema is stable)")

    except Exception as e:
        print(f"   ❌ Failed to compare schemas: {e}")

    print()

    # Step 5: Cache performance
    print("Step 5: Cache performance demonstration...")

    import time

    # Time uncached introspection
    clear_schema_cache()
    start = time.time()
    get_schema(client, use_cache=False)
    uncached_time = time.time() - start

    # Time cached introspection
    start = time.time()
    get_schema(client, use_cache=True)
    cached_time = time.time() - start

    print(f"   ⏱️  Uncached introspection: {uncached_time:.3f}s")
    print(f"   ⏱️  Cached introspection: {cached_time:.3f}s")
    print(f"   🚀 Cache speedup: {uncached_time / cached_time:.1f}x faster")

    print()
    print("=" * 70)
    print("✅ Schema introspection complete!")
    print("=" * 70)
    print()
    print("Summary:")
    print(f"  - Schema contains {types_count} types")
    print("  - Field descriptions available for AI context")
    print(f"  - Cache location: {CACHE_FILE}")
    print(f"  - Cache provides {uncached_time / cached_time:.1f}x speedup")
    print()
    print("AI Agent Benefits:")
    print("  1. Dynamic type validation (reduce hallucinations)")
    print("  2. Field description context (understand API semantics)")
    print("  3. Schema change detection (alert on breaking changes)")
    print("  4. Performance optimization (cache prevents rate limit impact)")


if __name__ == "__main__":
    main()
