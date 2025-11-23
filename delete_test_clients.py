#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "jobber-python-client",
# ]
# ///
"""
List Test Clients for Manual Deletion

⚠️  IMPORTANT: Jobber GraphQL API does not support client deletion.
   The 'clientDelete' mutation does not exist (only 'clientDeleteNote').

   Clients must be deleted manually via Jobber web interface.

This script lists test clients and provides clickable URLs for manual deletion.

Usage:
    python delete_test_clients.py

Test clients created during validation:
- Test Client (ID: 123679362) - from test_create_client_url.py
- John Doe (ID: 123679485) - from visual_confirmation_urls.py

Manual deletion steps:
1. Cmd+Click URLs below
2. In Jobber web UI: Actions → Archive Client
3. Archived clients can be permanently deleted from Settings
"""

import base64
from jobber import JobberClient, GraphQLError


def format_clickable_url(url: str, text: str) -> str:
    """Format URL as ANSI OSC 8 hyperlink for terminal click."""
    return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"


def decode_global_id(encoded_id: str) -> int:
    """Decode base64-encoded GraphQL global ID to numeric ID."""
    try:
        # Decode from base64
        decoded = base64.b64decode(encoded_id).decode("utf-8")
        # Format: gid://Jobber/Client/123456
        numeric_id = int(decoded.split("/")[-1])
        return numeric_id
    except Exception:
        return None


def main():
    print("=" * 70)
    print("⚠️  MANUAL DELETION REQUIRED")
    print("=" * 70)
    print("\nJobber API does not support programmatic client deletion.")
    print("Follow the steps below to delete test clients manually.\n")

    # Initialize client from Doppler
    client = JobberClient.from_doppler("claude-config", "dev")

    # Query all clients
    query = """
        query GetClients {
            clients(first: 10) {
                nodes {
                    id
                    firstName
                    lastName
                    companyName
                    jobberWebUri
                }
            }
        }
    """

    result = client.execute_query(query)
    all_clients = result["clients"]["nodes"]

    # Test clients to identify (numeric ID, name pattern)
    test_patterns = [
        (123679362, "Test Client", "Demo Company"),
        (123679485, "John Doe", "Doe Industries"),
    ]

    print("=" * 70)
    print(f"ALL CLIENTS IN ACCOUNT ({len(all_clients)} total)")
    print("=" * 70)
    print()

    test_client_count = 0
    for c in all_clients:
        # Extract numeric ID from encoded global ID
        encoded_id = c["id"]  # Z2lkOi8vSm9iYmVyL0NsaWVudC8xMjM0NTY=
        numeric_id = decode_global_id(encoded_id)

        if numeric_id is None:
            continue

        # Check if this is a test client
        is_test = any(numeric_id == test_id for test_id, _, _ in test_patterns)

        marker = "🧪 TEST" if is_test else "✅ KEEP"
        if is_test:
            test_client_count += 1

        name = f"{c['firstName']} {c['lastName']}"
        company = c.get("companyName", "No company")
        url = c.get("jobberWebUri", "No URL")

        print(f"{marker}: {name} ({company})")
        print(f"       ID: {numeric_id}")
        print(f"       {format_clickable_url(url, '🔗 Delete in web UI')}")
        print()

    print("=" * 70)
    print(f"SUMMARY: {test_client_count} test clients identified")
    print("=" * 70)
    print()

    if test_client_count > 0:
        print("DELETION STEPS:")
        print("1. Cmd+Click (or Ctrl+Click) each 🔗 link above")
        print("2. In Jobber web UI: Click 'Actions' → 'Archive Client'")
        print("3. Archived clients can be permanently deleted from Settings")
        print()
        print("⚠️  Keep 'John Doe (Test Company)' if it's your real client!")
    else:
        print("✅ No test clients found - cleanup may be complete")


if __name__ == "__main__":
    main()
