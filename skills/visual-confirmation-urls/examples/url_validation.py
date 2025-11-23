#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "jobber-python-client",
# ]
# ///
"""
Visual Confirmation URLs - URL-Based Validation

Check resource exists by testing web URL presence.

**Quick Win Validation**: If jobberWebUri returns valid URL,
resource was created successfully.

Usage:
    uv run url_validation.py
"""

from jobber import JobberClient


def main() -> int:
    """URL-based validation pattern."""
    print("=== URL-Based Validation Pattern ===\n")

    client = JobberClient.from_doppler("claude-config", "dev")

    query = """
        query GetClient($id: ID!) {
            client(id: $id) {
                id
                firstName
                jobberWebUri
            }
        }
    """

    # Example with hypothetical ID
    example_id = "gid://jobber/Client/123456"

    print(f"Validating client ID: {example_id}\n")

    try:
        result = client.execute_query(query, variables={'id': example_id})

        if result['client'] and result['client']['jobberWebUri']:
            print("✅ Validation passed:")
            print(f"   Resource exists: {result['client']['firstName']}")
            print(f"   Web URL present: {result['client']['jobberWebUri']}")
            print(f"   Status: CONFIRMED")
            return 0
        else:
            print("❌ Validation failed: No web URL returned")
            return 1

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
