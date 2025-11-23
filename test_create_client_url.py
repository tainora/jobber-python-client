#!/usr/bin/env python3
"""
Create a Jobber client and show the clickable URL.
"""

import sys

sys.path.insert(0, "/Users/terryli/own/jobber")

from jobber import JobberClient


def main():
    print("=== Creating Jobber Client with Visual Confirmation URL ===\n")

    try:
        # Load client from Doppler
        client = JobberClient.from_doppler("claude-config", "dev")

        # Mutation with jobberWebUri field
        mutation = """
            mutation CreateClient($input: ClientCreateInput!) {
                clientCreate(input: $input) {
                    client {
                        id
                        firstName
                        lastName
                        jobberWebUri
                    }
                    userErrors {
                        message
                        path
                    }
                }
            }
        """

        variables = {
            "input": {"firstName": "Test", "lastName": "Client", "companyName": "Demo Company"}
        }

        print("Sending request to Jobber API...\n")
        result = client.execute_query(mutation, variables)

        # Check for errors
        if result["clientCreate"]["userErrors"]:
            errors = result["clientCreate"]["userErrors"]
            print(f"❌ Failed to create client:")
            for error in errors:
                print(f"   - {error['message']}")
            return 1

        # Extract client data
        created = result["clientCreate"]["client"]

        # Display results with clickable URL
        print("=" * 70)
        print("✅ CLIENT CREATED SUCCESSFULLY!")
        print("=" * 70)
        print()
        print(f"ID:        {created['id']}")
        print(f"Name:      {created['firstName']} {created['lastName']}")
        print()
        print("🔗 CLICKABLE URL (Cmd+Click or Ctrl+Click):")
        print()
        print(f"   {created['jobberWebUri']}")
        print()
        print("=" * 70)
        print()
        print("👆 Click the URL above to view this client in Jobber's web interface!")
        print()

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
