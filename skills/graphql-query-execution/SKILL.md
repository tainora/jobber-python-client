---
name: graphql-query-execution
description: Execute GraphQL queries with error handling, pagination, and rate limiting. Use when integrating GraphQL APIs (Shopify, GitHub, Stripe) or building GraphQL clients.
---

# GraphQL Query Execution

Execute GraphQL queries with comprehensive error handling, pagination, and rate limiting.

## Problem Statement

GraphQL API integration requires:
- **Error handling**: Network errors, authentication failures, query errors
- **Rate limiting**: Respect API quotas, avoid throttling
- **Pagination**: Handle large result sets efficiently
- **Response parsing**: Extract data, handle missing fields

Building this from scratch for every GraphQL API leads to:
- Duplicated error handling logic
- Inconsistent rate limit management
- Fragile response parsing
- Poor error messages

## Solution

Reusable GraphQL executor pattern implementing:

1. **HTTP POST** → GraphQL endpoint
2. **Error parsing** → Raise specific exceptions
3. **Rate limit check** → Prevent quota exhaustion
4. **Response extraction** → Return clean data
5. **Pagination support** → Handle cursor-based paging

This pattern works across GraphQL APIs:
- ✅ **Jobber**: Cost-based rate limiting
- ✅ **Shopify**: Cost-based throttling (GraphQL Admin API)
- ✅ **GitHub**: Points-based rate limiting
- ✅ **Stripe**: Query cost tracking
- ✅ **Contentful**: GraphQL query execution
- ✅ **Any GraphQL API** with standard error format

## Quick Start

### Basic Usage

```python
from graphql_executor import GraphQLExecutor

# Initialize with access token
executor = GraphQLExecutor(access_token="your_token")

# Execute query
query = """
    query GetUsers {
        users(first: 10) {
            nodes {
                id
                name
                email
            }
        }
    }
"""

result = executor.execute(query)
users = result['users']['nodes']

for user in users:
    print(f"{user['name']} ({user['email']})")
```

### With Variables

```python
query = """
    query GetUser($id: ID!) {
        user(id: $id) {
            id
            name
            createdAt
        }
    }
"""

variables = {'id': 'user_123'}
result = executor.execute(query, variables)
user = result['user']
```

### Error Handling

```python
from graphql_executor import GraphQLExecutor, GraphQLError, RateLimitError

executor = GraphQLExecutor(access_token)

try:
    result = executor.execute(query, variables)
except GraphQLError as e:
    print(f"Query failed: {e.message}")
    print(f"Errors: {e.errors}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e.message}")
    print(f"Wait {e.context['wait_seconds']}s")
except AuthenticationError as e:
    print(f"Auth failed: {e.message}")
```

## GraphQL Execution Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Construct Query                                          │
│    - GraphQL query string                                   │
│    - Variables (optional)                                   │
│    - Operation name (optional)                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. HTTP POST Request                                        │
│    - POST to GraphQL endpoint                               │
│    - Authorization header (Bearer token)                    │
│    - Content-Type: application/json                         │
│    - Custom headers (API version, etc.)                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Error Handling                                           │
│    - NetworkError: Timeout, connection failed               │
│    - AuthenticationError: 401 unauthorized                  │
│    - GraphQLError: Query execution failed                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Rate Limit Check                                         │
│    - Extract throttle status from response                  │
│    - Check available points vs. threshold                   │
│    - Raise RateLimitError if low                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Response Parsing                                         │
│    - Extract data from response['data']                     │
│    - Return clean result dict                               │
└─────────────────────────────────────────────────────────────┘
```

## API-Specific Configuration

### Jobber GraphQL

```python
JOBBER_CONFIG = {
    "api_url": "https://api.getjobber.com/api/graphql",
    "api_version": "2023-11-15",  # X-JOBBER-GRAPHQL-VERSION header
    "rate_limit_threshold": 0.20,  # 20% threshold
    "throttle_path": "extensions.cost.throttleStatus"
}

executor = GraphQLExecutor(
    access_token=token,
    api_url=JOBBER_CONFIG["api_url"],
    custom_headers={"X-JOBBER-GRAPHQL-VERSION": JOBBER_CONFIG["api_version"]}
)
```

### Shopify GraphQL Admin API

```python
SHOPIFY_CONFIG = {
    "api_url": "https://{shop}.myshopify.com/admin/api/2024-01/graphql.json",
    "api_version": "2024-01",
    "rate_limit_threshold": 0.25,  # 25% threshold
    "throttle_path": "extensions.cost.throttleStatus"
}

executor = GraphQLExecutor(
    access_token=token,
    api_url=SHOPIFY_CONFIG["api_url"].format(shop="your-shop")
)
```

### GitHub GraphQL API

```python
GITHUB_CONFIG = {
    "api_url": "https://api.github.com/graphql",
    "rate_limit_threshold": 0.30,  # 30% threshold
    "throttle_path": "data.rateLimit"
}

executor = GraphQLExecutor(
    access_token=token,
    api_url=GITHUB_CONFIG["api_url"]
)
```

### Stripe GraphQL API

```python
STRIPE_CONFIG = {
    "api_url": "https://api.stripe.com/graphql",
    "rate_limit_threshold": 0.20
}

executor = GraphQLExecutor(
    access_token=token,
    api_url=STRIPE_CONFIG["api_url"]
)
```

## Pagination

GraphQL pagination typically uses cursor-based paging:

```python
def fetch_all_pages(executor, base_query, path_to_nodes, path_to_page_info):
    """Fetch all pages of results."""
    all_nodes = []
    cursor = None
    has_next_page = True

    while has_next_page:
        variables = {'cursor': cursor} if cursor else {}
        result = executor.execute(base_query, variables)

        # Extract nodes and pageInfo
        nodes = result[path_to_nodes]
        page_info = result[path_to_page_info]

        all_nodes.extend(nodes)

        has_next_page = page_info['hasNextPage']
        cursor = page_info['endCursor']

    return all_nodes
```

See [`references/pagination.md`](references/pagination.md) for detailed patterns.

## Rate Limiting

Proactive rate limit management prevents throttling:

```python
# Check throttle status after each query
throttle = executor.get_throttle_status()

if throttle:
    available = throttle['currentlyAvailable']
    maximum = throttle['maximumAvailable']
    print(f"Rate limit: {available}/{maximum} ({available/maximum*100:.1f}%)")
```

See [`references/rate-limiting.md`](references/rate-limiting.md) for advanced strategies.

## Error Handling

Fail-fast error handling with specific exceptions:

```python
try:
    result = executor.execute(query, variables)
except NetworkError as e:
    # HTTP request failed (timeout, connection error)
    print(f"Network error: {e.message}")
    print(f"Context: {e.context}")
except AuthenticationError as e:
    # 401 Unauthorized (token invalid/expired)
    print(f"Auth error: {e.message}")
    # Trigger token refresh
except GraphQLError as e:
    # GraphQL query execution failed
    print(f"Query error: {e.message}")
    print(f"Errors: {e.errors}")
    print(f"Query: {e.query}")
except RateLimitError as e:
    # Rate limit threshold exceeded
    print(f"Rate limit: {e.message}")
    wait_seconds = e.context['wait_seconds']
    print(f"Wait {wait_seconds:.1f}s")
```

**No fallbacks, defaults, or silent failures.** Caller controls recovery strategy.

See [`references/error-handling.md`](references/error-handling.md) for exception hierarchy.

## Template

See [`assets/graphql_executor_template.py`](assets/graphql_executor_template.py) for parameterized implementation:

- Configurable API URL
- Custom headers support
- Pluggable rate limit strategies
- Exception hierarchy
- Type hints (mypy compatible)

## Examples

Runnable examples with inline dependencies (PEP 723):

- [`examples/basic_query.py`](examples/basic_query.py) - Basic query execution
- [`examples/with_variables.py`](examples/with_variables.py) - Query with variables
- [`examples/pagination.py`](examples/pagination.py) - Cursor-based pagination
- [`examples/error_handling.py`](examples/error_handling.py) - Comprehensive error handling
- [`examples/rate_limiting.py`](examples/rate_limiting.py) - Rate limit management

## References

- [Error Handling](references/error-handling.md) - Exception hierarchy and patterns
- [Pagination](references/pagination.md) - Cursor-based paging strategies
- [Rate Limiting](references/rate-limiting.md) - Throttle management and backoff
- [Query Patterns](references/query-patterns.md) - Common query structures

## Validation

This pattern is production-validated:

- **ADR-0001**: Jobber API client architecture (fail-fast errors, minimal dependencies)
- **Implementation**: `jobber/graphql.py` (189 LOC)
- **Examples**: `examples/basic_usage.py`, `examples/error_handling.py`

## Reusability

This pattern is broadly applicable to GraphQL APIs:

- ✅ **Jobber**: Cost-based throttling, custom version headers
- ✅ **Shopify**: Cost-based rate limiting, Admin API
- ✅ **GitHub**: Points-based rate limiting, standard GraphQL
- ✅ **Stripe**: Query cost tracking
- ✅ **Contentful**: GraphQL CDA/CMA
- ✅ **Linear**: Standard GraphQL with pagination
- ✅ **Any GraphQL API** following spec
