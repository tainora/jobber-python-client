#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests",
# ]
# ///
"""
GraphQL Query Execution - Query with Variables

Query execution with GraphQL variables for type safety and reusability.

Usage:
    uv run with_variables.py
"""

from graphql_executor_template import GraphQLExecutor


def main() -> int:
    """Execute GraphQL query with variables."""
    print("=== GraphQL Query with Variables ===\n")

    executor = GraphQLExecutor(
        access_token="your_access_token", api_url="https://api.example.com/graphql"
    )

    # Define query with variables
    query = """
        query GetUser($id: ID!) {
            user(id: $id) {
                id
                name
                email
                createdAt
            }
        }
    """

    # Variables (type-safe)
    variables = {"id": "123"}

    print(f"Executing query with variables: {variables}\n")

    try:
        result = executor.execute(query, variables)

        user = result["user"]

        print("✅ Query successful!\n")
        print(f"User: {user['name']}")
        print(f"Email: {user['email']}")
        print(f"Created: {user['createdAt']}")

        return 0

    except Exception as e:
        print(f"❌ Query failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
