#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "jobber-python-client",
# ]
# ///
"""
Visual Confirmation URLs - Create Resource with URL

Create a client via API and get web URL for visual confirmation.

**Quick Win**: User can click link to see client in Jobber web UI.

Usage:
    uv run create_with_url.py
"""

from jobber import JobberClient


def main() -> int:
    """Create client with web URL confirmation."""
    print("=== Create Client with Web URL ===\n")

    client = JobberClient.from_doppler("claude-config", "dev")

    # CRITICAL: Include jobberWebUri in mutation response
    mutation = """
        mutation CreateClient($input: ClientCreate!) {
            clientCreate(input: $input) {
                client {
                    id
                    firstName
                    lastName
                    jobberWebUri  # <-- WEB UI LINK
                }
                userErrors {
                    message
                    path
                }
            }
        }
    """

    variables = {
        'input': {
            'firstName': 'John',
            'lastName': 'Doe',
            'companyName': 'Doe Industries'
        }
    }

    result = client.execute_query(mutation, variables)

    if result['clientCreate']['userErrors']:
        errors = result['clientCreate']['userErrors']
        print(f"❌ Failed to create client: {errors}")
        return 1

    created = result['clientCreate']['client']

    # Visual feedback with clickable link
    print(f"✅ Client created successfully!")
    print(f"   ID: {created['id']}")
    print(f"   Name: {created['firstName']} {created['lastName']}")
    print(f"   🔗 View in Jobber: {created['jobberWebUri']}")
    print(f"\n   👆 Click to verify in web interface")

    return 0


if __name__ == '__main__':
    exit(main())
