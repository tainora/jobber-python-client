#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests",
# ]
# ///
"""
GraphQL Query Execution - Cursor-Based Pagination

Fetch all pages of results using cursor-based pagination (Relay spec).

Usage:
    uv run pagination.py
"""

from graphql_executor_template import GraphQLExecutor


def fetch_all_pages(executor: GraphQLExecutor) -> list[dict]:
    """Fetch all pages of users."""
    query = """
        query GetUsers($first: Int!, $after: String) {
            users(first: $first, after: $after) {
                nodes {
                    id
                    name
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
    """

    all_users = []
    cursor = None
    page_count = 0

    while True:
        variables = {"first": 100, "after": cursor}

        result = executor.execute(query, variables)

        # Extract nodes and pageInfo
        users = result["users"]["nodes"]
        page_info = result["users"]["pageInfo"]

        all_users.extend(users)
        page_count += 1

        print(f"Page {page_count}: Fetched {len(users)} users")

        # Check if more pages exist
        if not page_info["hasNextPage"]:
            break

        cursor = page_info["endCursor"]

    return all_users


def main() -> int:
    """Demonstrate cursor-based pagination."""
    print("=== GraphQL Cursor-Based Pagination ===\n")

    executor = GraphQLExecutor(
        access_token="your_access_token", api_url="https://api.example.com/graphql"
    )

    try:
        users = fetch_all_pages(executor)

        print(f"\n✅ Fetched all {len(users)} users")

        return 0

    except Exception as e:
        print(f"\n❌ Pagination failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
