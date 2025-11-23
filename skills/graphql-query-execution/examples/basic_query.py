#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests",
# ]
# ///
"""
GraphQL Query Execution - Basic Query

Basic GraphQL query execution pattern.

Usage:
    uv run basic_query.py
"""

from graphql_executor_template import GraphQLExecutor


def main() -> int:
    """Execute basic GraphQL query."""
    print("=== Basic GraphQL Query Execution ===\n")

    # Initialize executor
    executor = GraphQLExecutor(
        access_token="your_access_token", api_url="https://api.example.com/graphql"
    )

    # Define query
    query = """
        query GetUsers {
            users(first: 5) {
                nodes {
                    id
                    name
                    email
                }
            }
        }
    """

    print("Executing query...")

    try:
        result = executor.execute(query)

        # Extract users
        users = result["users"]["nodes"]

        print(f"✅ Query successful! Found {len(users)} users:\n")

        for user in users:
            print(f"• {user['name']} ({user['email']})")

        return 0

    except Exception as e:
        print(f"❌ Query failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
