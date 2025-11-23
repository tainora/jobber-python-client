#!/usr/bin/env python3
"""
Basic usage example for Jobber Python client.

Prerequisites:
    1. Run jobber_auth.py to authenticate
    2. Ensure Doppler has JOBBER_* secrets

Usage:
    uv run --with /path/to/jobber examples/basic_usage.py
"""

from jobber import JobberClient, JobberException
from jobber.url_helpers import clickable_link


def main():
    """Demonstrate basic API operations"""

    # Create client (loads credentials from Doppler)
    client = JobberClient.from_doppler()

    # Query 1: Get account info
    print("Querying account info...")
    result = client.execute_query("""
        query {
            account {
                id
                createdAt
            }
        }
    """)
    print(f"Account ID: {result['account']['id']}")
    print(f"Created: {result['account']['createdAt']}")

    # Query 2: Get clients with pagination
    print("\nQuerying clients...")
    result = client.execute_query(
        """
        query GetClients($first: Int!) {
            clients(first: $first) {
                nodes {
                    id
                    firstName
                    lastName
                    companyName
                    jobberWebUri
                }
                totalCount
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
    """,
        variables={"first": 5},
    )

    clients = result["clients"]
    print(f"Total clients: {clients['totalCount']}")
    print(f"Retrieved: {len(clients['nodes'])} clients")

    for client_data in clients["nodes"]:
        name = f"{client_data['firstName']} {client_data['lastName']}"
        company = client_data.get("companyName", "N/A")
        # Include clickable web link for visual confirmation
        web_link = clickable_link(client_data["jobberWebUri"], "🔗 View")
        print(f"  - {name} ({company}) - {web_link}")

    # Query 3: Check rate limit status
    print("\nRate limit status:")
    throttle = client.get_throttle_status()
    if throttle:
        print(f"  Available: {throttle['currentlyAvailable']} points")
        print(f"  Maximum: {throttle['maximumAvailable']} points")
        print(f"  Restore rate: {throttle['restoreRate']} points/second")


if __name__ == "__main__":
    try:
        main()
    except JobberException as e:
        print(f"Error: {e}")
        if e.context:
            print(f"Context: {e.context}")
        exit(1)
