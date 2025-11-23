# GraphQL Pagination

Cursor-based pagination patterns for GraphQL APIs (Relay specification).

## Cursor-Based Pagination

GraphQL APIs typically use cursor-based pagination following the Relay specification:

```graphql
query {
  users(first: 10, after: "cursor") {
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
```

**Components**:
- `first`: Number of items to fetch
- `after`: Cursor pointing to start position
- `nodes`: Array of results
- `pageInfo`: Pagination metadata
  - `hasNextPage`: Whether more results exist
  - `endCursor`: Cursor for next page

## Basic Pagination Pattern

```python
def fetch_all_pages(executor, query_template):
    """Fetch all pages of results."""
    all_nodes = []
    cursor = None
    has_next_page = True

    while has_next_page:
        # Build query with cursor
        query = query_template.format(cursor=f'after: "{cursor}"' if cursor else '')

        result = executor.execute(query)

        # Extract nodes and pageInfo
        nodes = result['users']['nodes']
        page_info = result['users']['pageInfo']

        all_nodes.extend(nodes)

        # Update pagination state
        has_next_page = page_info['hasNextPage']
        cursor = page_info['endCursor']

    return all_nodes
```

## Parameterized Query Pagination

```python
def fetch_with_pagination(executor, page_size=100):
    """Fetch results using GraphQL variables for pagination."""
    query = """
        query GetClients($first: Int!, $after: String) {
            clients(first: $first, after: $after) {
                nodes {
                    id
                    firstName
                    lastName
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
    """

    all_clients = []
    cursor = None
    has_next_page = True

    while has_next_page:
        variables = {
            'first': page_size,
            'after': cursor
        }

        result = executor.execute(query, variables)

        # Extract data
        clients = result['clients']['nodes']
        page_info = result['clients']['pageInfo']

        all_clients.extend(clients)

        # Update pagination state
        has_next_page = page_info['hasNextPage']
        cursor = page_info['endCursor']

    return all_clients
```

## Pagination with Error Handling

```python
from graphql_executor import GraphQLExecutor, RateLimitError, GraphQLError
import time

def fetch_with_retry(executor, query, max_pages=None):
    """Fetch paginated results with error handling and retry."""
    all_nodes = []
    cursor = None
    page_count = 0

    while True:
        # Check max_pages limit
        if max_pages and page_count >= max_pages:
            break

        variables = {'first': 100, 'after': cursor}

        try:
            result = executor.execute(query, variables)

        except RateLimitError as e:
            # Wait for rate limit to restore
            wait_seconds = e.context['wait_seconds']
            print(f"Rate limit hit. Waiting {wait_seconds:.1f}s...")
            time.sleep(wait_seconds)
            continue  # Retry same page

        except GraphQLError as e:
            # Query error - log and abort
            print(f"Query failed: {e.message}")
            raise

        # Extract nodes and pageInfo
        nodes = result['resource']['nodes']
        page_info = result['resource']['pageInfo']

        all_nodes.extend(nodes)
        page_count += 1

        # Check if more pages exist
        if not page_info['hasNextPage']:
            break

        cursor = page_info['endCursor']

    return all_nodes
```

## Bidirectional Pagination

Relay supports both forward and backward pagination:

```graphql
query {
  # Forward pagination
  users(first: 10, after: "cursor") {
    nodes { id }
    pageInfo {
      hasNextPage
      hasPreviousPage
      startCursor
      endCursor
    }
  }

  # Backward pagination
  users(last: 10, before: "cursor") {
    nodes { id }
    pageInfo {
      hasNextPage
      hasPreviousPage
      startCursor
      endCursor
    }
  }
}
```

**Implementation**:
```python
def fetch_previous_page(executor, cursor):
    """Fetch previous page using backward pagination."""
    query = """
        query GetPreviousPage($cursor: String!) {
            users(last: 10, before: $cursor) {
                nodes {
                    id
                    name
                }
                pageInfo {
                    hasPreviousPage
                    startCursor
                }
            }
        }
    """

    result = executor.execute(query, {'cursor': cursor})
    return result['users']
```

## Offset-Based Pagination (Rare)

Some GraphQL APIs use offset-based pagination:

```graphql
query {
  users(limit: 10, offset: 20) {
    id
    name
  }
  usersCount
}
```

**Implementation**:
```python
def fetch_with_offset(executor, page_size=100):
    """Fetch using offset-based pagination."""
    query = """
        query GetUsers($limit: Int!, $offset: Int!) {
            users(limit: $limit, offset: $offset) {
                id
                name
            }
            usersCount
        }
    """

    all_users = []
    offset = 0

    # Get total count
    result = executor.execute(query, {'limit': 1, 'offset': 0})
    total_count = result['usersCount']

    while offset < total_count:
        variables = {
            'limit': page_size,
            'offset': offset
        }

        result = executor.execute(query, variables)
        all_users.extend(result['users'])

        offset += page_size

    return all_users
```

## Progress Reporting

```python
def fetch_with_progress(executor, query, total_expected=None):
    """Fetch paginated results with progress reporting."""
    all_nodes = []
    cursor = None
    page_count = 0

    while True:
        variables = {'first': 100, 'after': cursor}
        result = executor.execute(query, variables)

        nodes = result['resource']['nodes']
        page_info = result['resource']['pageInfo']

        all_nodes.extend(nodes)
        page_count += 1

        # Progress reporting
        if total_expected:
            progress = len(all_nodes) / total_expected * 100
            print(f"Progress: {len(all_nodes)}/{total_expected} ({progress:.1f}%)")
        else:
            print(f"Fetched {len(all_nodes)} items ({page_count} pages)")

        if not page_info['hasNextPage']:
            break

        cursor = page_info['endCursor']

    return all_nodes
```

## Streaming Results

For very large result sets, stream results instead of collecting in memory:

```python
def fetch_streaming(executor, query, callback):
    """Stream paginated results via callback function."""
    cursor = None

    while True:
        variables = {'first': 100, 'after': cursor}
        result = executor.execute(query, variables)

        nodes = result['resource']['nodes']
        page_info = result['resource']['pageInfo']

        # Process each node via callback
        for node in nodes:
            callback(node)

        if not page_info['hasNextPage']:
            break

        cursor = page_info['endCursor']

# Usage
def process_user(user):
    print(f"Processing {user['name']}")
    # Save to database, send to queue, etc.

fetch_streaming(executor, query, callback=process_user)
```

## Related References

- [Error Handling](error-handling.md) - Handle errors during pagination
- [Rate Limiting](rate-limiting.md) - Manage rate limits across pages
- [Query Patterns](query-patterns.md) - Pagination query construction
- [SKILL.md](../SKILL.md) - Hub document with quick start
