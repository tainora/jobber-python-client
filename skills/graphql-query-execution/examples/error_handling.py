#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests",
# ]
# ///
"""
GraphQL Query Execution - Comprehensive Error Handling

Demonstrates error handling for all exception types:
- NetworkError (timeout, connection, HTTP errors)
- AuthenticationError (401 unauthorized)
- GraphQLError (query execution failed)
- RateLimitError (throttle threshold exceeded)

Usage:
    uv run error_handling.py
"""

import time
from graphql_executor_template import (
    GraphQLExecutor,
    NetworkError,
    AuthenticationError,
    GraphQLError,
    RateLimitError,
)


def execute_with_comprehensive_error_handling(
    executor: GraphQLExecutor, query: str, variables: dict | None = None
) -> dict:
    """Execute query with comprehensive error handling."""
    try:
        result = executor.execute(query, variables)
        return result

    except NetworkError as e:
        # HTTP/network failure
        print(f"❌ Network error: {e.message}")
        print(f"   URL: {e.context.get('url')}")
        print(f"   Status: {e.context.get('status_code')}")
        raise  # Re-raise, let caller decide recovery

    except AuthenticationError as e:
        # Token invalid/expired
        print(f"❌ Authentication error: {e.message}")
        print("   Triggering token refresh...")
        # In production: refresh_oauth_token()
        raise

    except GraphQLError as e:
        # Query execution failed
        print(f"❌ GraphQL error: {e.message}")
        print(f"   Errors: {e.errors}")
        print(f"   Query: {e.query}")
        raise  # Re-raise, query needs fixing

    except RateLimitError as e:
        # Rate limit exceeded
        print(f"⚠️  Rate limit hit: {e.message}")
        wait_seconds = e.context["wait_seconds"]
        print(f"   Waiting {wait_seconds:.1f}s for points to restore...")

        time.sleep(wait_seconds)

        # Retry after wait
        print("   Retrying...")
        return executor.execute(query, variables)


def main() -> int:
    """Demonstrate error handling patterns."""
    print("=== GraphQL Comprehensive Error Handling ===\n")

    executor = GraphQLExecutor(
        access_token="your_access_token",
        api_url="https://api.example.com/graphql",
        rate_limit_threshold=0.20,
    )

    # Example 1: Successful query
    print("Example 1: Successful Query\n")
    query = """
        query GetUsers {
            users(first: 5) {
                nodes {
                    id
                    name
                }
            }
        }
    """

    try:
        result = execute_with_comprehensive_error_handling(executor, query)
        users = result["users"]["nodes"]
        print(f"✅ Success! Fetched {len(users)} users\n")
    except Exception as e:
        print(f"Failed: {e}\n")

    # Example 2: GraphQL Error (invalid field)
    print("Example 2: GraphQL Error (Invalid Field)\n")
    invalid_query = """
        query {
            users {
                invalidField  # This field doesn't exist
            }
        }
    """

    try:
        execute_with_comprehensive_error_handling(executor, invalid_query)
    except GraphQLError as e:
        print(f"Expected error: {e.message}\n")

    # Example 3: Rate Limit Handling
    print("Example 3: Rate Limit Handling\n")

    try:
        # Execute multiple queries to potentially hit rate limit
        for i in range(5):
            result = execute_with_comprehensive_error_handling(executor, query)

            # Check throttle status
            throttle = executor.get_throttle_status()
            if throttle:
                available = throttle["currentlyAvailable"]
                maximum = throttle["maximumAvailable"]
                pct = available / maximum * 100
                print(f"Query {i + 1}: Rate limit: {available}/{maximum} ({pct:.1f}%)")

    except RateLimitError as e:
        print(f"Rate limit exceeded: {e.message}")

    print("\n✅ Error handling demonstration complete")
    return 0


if __name__ == "__main__":
    exit(main())
