#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "jobber-python-client",
# ]
# ///
"""
Visual Confirmation URLs - Query with URLs

Query clients and show web URLs for each result.

**Use Case**: Automation reports with clickable links.

Usage:
    uv run query_with_urls.py
"""

from jobber import JobberClient


def main() -> int:
    """Query clients with web URLs."""
    print("=== Query Clients with Web URLs ===\n")

    client = JobberClient.from_doppler("claude-config", "dev")

    # CRITICAL: Include jobberWebUri in query
    query = """
        query GetRecentClients {
            clients(first: 5) {
                nodes {
                    id
                    firstName
                    lastName
                    jobberWebUri  # <-- WEB UI LINK
                }
            }
        }
    """

    result = client.execute_query(query)

    print("Recent clients:\n")
    for client_data in result['clients']['nodes']:
        print(f"• {client_data['firstName']} {client_data['lastName']}")
        print(f"  🔗 {client_data['jobberWebUri']}\n")

    return 0


if __name__ == '__main__':
    exit(main())
