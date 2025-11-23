#!/usr/bin/env python3
"""
List existing Jobber clients with their clickable URLs.
"""

import sys

sys.path.insert(0, "/Users/terryli/own/jobber")

from jobber import JobberClient


def main():
    print("=== Fetching Existing Jobber Clients ===\n")

    try:
        # Load client from Doppler
        client = JobberClient.from_doppler("claude-config", "dev")

        # Query existing clients with URLs
        query = """
            query GetClients {
                clients(first: 5) {
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

        print("Fetching your existing clients...\n")
        result = client.execute_query(query)

        clients = result["clients"]["nodes"]

        if not clients:
            print("❌ No clients found in your Jobber account.")
            print("\nTo create a client and get a URL:")
            print("  1. Run: uv run python test_create_client_url.py")
            print("  2. Cmd+Click the returned URL")
            return 0

        print("=" * 80)
        print(f"✅ FOUND {len(clients)} CLIENTS IN YOUR JOBBER ACCOUNT")
        print("=" * 80)
        print()

        for i, client_data in enumerate(clients, 1):
            name = f"{client_data.get('firstName', '')} {client_data.get('lastName', '')}"
            company = client_data.get("companyName", "")

            print(f"{i}. {name.strip()}")
            if company:
                print(f"   Company: {company}")
            print(f"   ID: {client_data['id']}")
            print(f"   🔗 {client_data['jobberWebUri']}")
            print()

        print("=" * 80)
        print("👆 Cmd+Click any URL above to view in Jobber!")
        print("=" * 80)

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure you've authenticated first:")
        print("  uv run jobber_auth.py")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
