#!/usr/bin/env python3
"""
Error handling example for Jobber Python client.

Demonstrates proper exception handling for all error types.

Usage:
    uv run --with /path/to/jobber examples/error_handling.py
"""

from jobber import (
    JobberClient,
    AuthenticationError,
    RateLimitError,
    GraphQLError,
    NetworkError,
    ConfigurationError,
)
from jobber.url_helpers import validate_url


def handle_query_with_errors(client: JobberClient, query: str):
    """
    Execute query with comprehensive error handling.

    Args:
        client: JobberClient instance
        query: GraphQL query string

    Returns:
        Query result or None if error
    """
    try:
        result = client.execute_query(query)
        return result

    except AuthenticationError as e:
        print(f"Authentication error: {e}")
        print("Resolution: Run 'uv run jobber_auth.py' to re-authenticate")
        return None

    except RateLimitError as e:
        print(f"Rate limit error: {e}")
        if e.throttle_status:
            available = e.throttle_status.get('currentlyAvailable', 0)
            restore_rate = e.throttle_status.get('restoreRate', 500)
            wait_seconds = e.context.get('wait_seconds', 0)
            print(f"  Available points: {available}")
            print(f"  Restore rate: {restore_rate} points/second")
            print(f"  Suggested wait: {wait_seconds:.1f} seconds")
        return None

    except GraphQLError as e:
        print(f"GraphQL error: {e}")
        print(f"  Query: {e.query[:100]}...")
        print(f"  Errors: {e.errors}")
        return None

    except NetworkError as e:
        print(f"Network error: {e}")
        print("Resolution: Check network connectivity and Jobber API status")
        return None

    except ConfigurationError as e:
        print(f"Configuration error: {e}")
        print("Resolution: Verify Doppler project/config and run jobber_auth.py")
        return None


def main():
    """Demonstrate error handling patterns"""

    print("Example 1: Normal query")
    print("-" * 50)
    try:
        client = JobberClient.from_doppler()
        result = handle_query_with_errors(client, "{ account { id } }")
        if result:
            print(f"✓ Success: {result}")
    except ConfigurationError as e:
        print(f"✗ Cannot create client: {e}")

    print("\nExample 2: Invalid query (GraphQL error)")
    print("-" * 50)
    try:
        client = JobberClient.from_doppler()
        # This query has invalid field 'invalidField'
        result = handle_query_with_errors(client, "{ account { invalidField } }")
        if result:
            print(f"✓ Success: {result}")
    except ConfigurationError as e:
        print(f"✗ Cannot create client: {e}")

    print("\nExample 3: Manual pagination with error handling")
    print("-" * 50)
    try:
        client = JobberClient.from_doppler()

        cursor = None
        page_num = 0
        total_fetched = 0

        while True:
            query = """
            query GetClients($first: Int!, $after: String) {
                clients(first: $first, after: $after) {
                    nodes {
                        id
                        firstName
                        lastName
                        jobberWebUri
                    }
                    pageInfo { hasNextPage endCursor }
                }
            }
            """

            variables = {'first': 50}
            if cursor:
                variables['after'] = cursor

            result = handle_query_with_errors(client, query)
            if not result:
                print("✗ Error fetching page, stopping pagination")
                break

            clients = result['clients']
            page_num += 1
            total_fetched += len(clients['nodes'])

            # Show URLs for visual verification (first 3 clients on each page)
            urls_sample = []
            for client_data in clients['nodes'][:3]:
                try:
                    url = validate_url(client_data)
                    urls_sample.append(url)
                except (KeyError, ValueError):
                    pass  # URL not available, skip

            print(f"Page {page_num}: {len(clients['nodes'])} clients")
            if urls_sample:
                print(f"  Sample URLs for verification: {urls_sample[0][:50]}...")

            # Check for more pages
            if not clients['pageInfo']['hasNextPage']:
                break

            cursor = clients['pageInfo']['endCursor']

        print(f"✓ Total fetched: {total_fetched} clients over {page_num} pages")

    except ConfigurationError as e:
        print(f"✗ Cannot create client: {e}")


if __name__ == '__main__':
    main()
