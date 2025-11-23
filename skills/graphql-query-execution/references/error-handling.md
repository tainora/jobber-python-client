# GraphQL Error Handling

Comprehensive error handling patterns for GraphQL APIs with fail-fast exception hierarchy.

## Exception Hierarchy

```
GraphQLException (base)
├── NetworkError
│   ├── Timeout (30s)
│   ├── ConnectionError (DNS, network)
│   └── HTTPError (4xx, 5xx)
├── AuthenticationError (401)
├── GraphQLError (query execution failed)
└── RateLimitError (throttle threshold exceeded)
```

## Exception Details

### GraphQLException (Base)

All exceptions inherit from this base class.

```python
class GraphQLException(Exception):
    def __init__(self, message: str, context: dict[str, Any] | None = None):
        self.message = message
        self.context = context or {}
```

**Attributes**:
- `message`: Human-readable error message
- `context`: Additional error context (dict)

### NetworkError

HTTP request failed (timeout, connection, HTTP error).

**Causes**:
- Request timeout (>30s)
- DNS resolution failed
- Connection refused
- HTTP 4xx/5xx errors (except 401)

**Example**:
```python
try:
    result = executor.execute(query)
except NetworkError as e:
    print(f"Network error: {e.message}")
    print(f"URL: {e.context.get('url')}")
    print(f"Status: {e.context.get('status_code')}")
```

**Context Fields**:
- `url`: API endpoint URL
- `status_code`: HTTP status code (if applicable)
- `response`: Raw response text

### AuthenticationError

Authentication failed (401 Unauthorized).

**Causes**:
- Access token invalid
- Access token expired
- Insufficient permissions

**Example**:
```python
try:
    result = executor.execute(query)
except AuthenticationError as e:
    print(f"Auth failed: {e.message}")
    # Trigger token refresh
    new_token = refresh_oauth_token()
    executor = GraphQLExecutor(new_token)
    result = executor.execute(query)  # Retry
```

**Context Fields**:
- `status_code`: 401

**Recovery Strategy**:
- Refresh OAuth access token
- Re-authenticate user
- Check token scopes/permissions

### GraphQLError

GraphQL query execution failed.

**Causes**:
- Syntax error in query
- Invalid field name
- Missing required arguments
- Permission denied (resource-level)
- Validation error

**Example**:
```python
try:
    result = executor.execute(query, variables)
except GraphQLError as e:
    print(f"Query failed: {e.message}")
    print(f"Errors: {e.errors}")
    print(f"Query: {e.query}")
    print(f"Variables: {e.context.get('variables')}")
```

**Attributes**:
- `message`: First error message
- `errors`: List of GraphQL error objects
- `query`: GraphQL query string
- `context['variables']`: Query variables

**Error Format** (standard GraphQL):
```json
{
  "errors": [
    {
      "message": "Field 'invalidField' doesn't exist on type 'User'",
      "locations": [{"line": 3, "column": 5}],
      "path": ["user", "invalidField"]
    }
  ]
}
```

**Recovery Strategy**:
- Fix query syntax
- Check field names against schema
- Provide missing required arguments
- Handle permission errors gracefully

### RateLimitError

Rate limit threshold exceeded.

**Causes**:
- Available points < threshold (default: 20%)
- Too many requests in short time
- Cost of query exceeds available points

**Example**:
```python
try:
    result = executor.execute(query)
except RateLimitError as e:
    print(f"Rate limit: {e.message}")
    wait_seconds = e.context['wait_seconds']
    print(f"Wait {wait_seconds:.1f}s for points to restore")

    # Option 1: Wait and retry
    import time
    time.sleep(wait_seconds)
    result = executor.execute(query)

    # Option 2: Queue for later
    queue.enqueue_delayed(query, delay=wait_seconds)
```

**Attributes**:
- `throttle_status`: Throttle status dict
  - `currentlyAvailable`: Points available now
  - `maximumAvailable`: Total point capacity
  - `restoreRate`: Points restored per second
- `context['wait_seconds']`: Calculated wait time
- `context['threshold_pct']`: Threshold percentage (e.g., 0.20)

**Recovery Strategies**:
1. **Wait and Retry**: Sleep for `wait_seconds`, then retry
2. **Queue**: Enqueue query for delayed execution
3. **Backoff**: Exponential backoff between retries
4. **Circuit Breaker**: Stop sending requests if threshold repeatedly hit

## Error Handling Patterns

### Pattern 1: Comprehensive Try-Except

```python
from graphql_executor import (
    GraphQLExecutor,
    NetworkError,
    AuthenticationError,
    GraphQLError,
    RateLimitError
)

def execute_with_error_handling(executor, query, variables=None):
    """Execute query with comprehensive error handling."""
    try:
        result = executor.execute(query, variables)
        return result

    except NetworkError as e:
        # HTTP/network failure
        logger.error(f"Network error: {e.message}", extra=e.context)
        raise  # Re-raise, let caller decide recovery

    except AuthenticationError as e:
        # Token invalid/expired
        logger.warning(f"Auth failed: {e.message}")
        # Trigger token refresh
        new_token = refresh_token()
        executor = GraphQLExecutor(new_token)
        return executor.execute(query, variables)  # Retry once

    except GraphQLError as e:
        # Query execution failed
        logger.error(f"GraphQL error: {e.message}")
        logger.debug(f"Query: {e.query}")
        logger.debug(f"Errors: {e.errors}")
        raise  # Re-raise, query needs fixing

    except RateLimitError as e:
        # Rate limit exceeded
        logger.warning(f"Rate limit: {e.message}")
        wait_seconds = e.context['wait_seconds']
        logger.info(f"Waiting {wait_seconds:.1f}s...")
        time.sleep(wait_seconds)
        return executor.execute(query, variables)  # Retry after wait
```

### Pattern 2: Fail-Fast (No Recovery)

```python
def execute_fail_fast(executor, query, variables=None):
    """Execute query with fail-fast error handling."""
    # No try-except - let exceptions propagate
    # Caller decides recovery strategy
    result = executor.execute(query, variables)
    return result
```

**When to Use**: When caller has better context for recovery decisions.

### Pattern 3: Rate Limit Backoff

```python
import time

def execute_with_backoff(executor, query, variables=None, max_retries=3):
    """Execute query with exponential backoff on rate limit."""
    for attempt in range(max_retries):
        try:
            result = executor.execute(query, variables)
            return result

        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise  # Max retries exceeded

            wait_seconds = e.context['wait_seconds']
            backoff = wait_seconds * (2 ** attempt)  # Exponential backoff
            logger.info(f"Rate limit hit. Waiting {backoff:.1f}s (attempt {attempt+1}/{max_retries})")
            time.sleep(backoff)

    raise RuntimeError("Max retries exceeded")
```

### Pattern 4: Circuit Breaker

```python
class CircuitBreaker:
    """Circuit breaker to prevent repeated rate limit errors."""

    def __init__(self, threshold=5, timeout=60):
        self.failure_count = 0
        self.threshold = threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.is_open = False

    def execute(self, executor, query, variables=None):
        """Execute query with circuit breaker."""
        if self.is_open:
            elapsed = time.time() - self.last_failure_time
            if elapsed < self.timeout:
                raise RuntimeError(f"Circuit breaker open. Wait {self.timeout - elapsed:.1f}s")
            else:
                # Timeout elapsed, try half-open state
                self.is_open = False
                self.failure_count = 0

        try:
            result = executor.execute(query, variables)
            self.failure_count = 0  # Reset on success
            return result

        except RateLimitError as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.threshold:
                self.is_open = True
                logger.error(f"Circuit breaker opened after {self.failure_count} failures")

            raise

# Usage
breaker = CircuitBreaker(threshold=5, timeout=60)
result = breaker.execute(executor, query, variables)
```

## Response Validation

### Missing Data Field

```python
if 'data' not in result:
    raise GraphQLError(
        "Response missing 'data' field",
        errors=[],
        query=query,
        context={'response': result}
    )
```

### Null Results

```python
result = executor.execute(query, variables)

if result['user'] is None:
    # User not found or access denied
    logger.warning(f"User not found: {variables['id']}")
    return None

return result['user']
```

### Partial Errors

Some GraphQL APIs return partial data with errors:

```json
{
  "data": {
    "user": {
      "id": "123",
      "name": "John"
    }
  },
  "errors": [
    {
      "message": "Field 'email' failed due to permissions",
      "path": ["user", "email"]
    }
  ]
}
```

**Handling**:
```python
# Current implementation raises on ANY errors
# For partial errors, you may want to:

try:
    result = executor.execute(query)
except GraphQLError as e:
    # Check if partial data present
    if e.context.get('response', {}).get('data'):
        logger.warning(f"Partial data with errors: {e.errors}")
        return e.context['response']['data']
    else:
        raise  # No data, re-raise
```

## Logging Best Practices

```python
import logging

logger = logging.getLogger(__name__)

try:
    result = executor.execute(query, variables)
except GraphQLException as e:
    # Log with structured context
    logger.error(
        f"{type(e).__name__}: {e.message}",
        extra={
            'error_type': type(e).__name__,
            'context': e.context,
            'query': getattr(e, 'query', None),
            'variables': variables
        }
    )
    raise
```

## Testing Error Handling

```python
import pytest
from unittest.mock import Mock, patch

def test_network_error_handling():
    """Test NetworkError is raised on timeout."""
    executor = GraphQLExecutor(access_token="token")

    with patch('requests.post') as mock_post:
        mock_post.side_effect = requests.Timeout()

        with pytest.raises(NetworkError, match="timeout"):
            executor.execute("query { test }")

def test_authentication_error_handling():
    """Test AuthenticationError is raised on 401."""
    executor = GraphQLExecutor(access_token="invalid_token")

    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 401

        with pytest.raises(AuthenticationError, match="invalid or expired"):
            executor.execute("query { test }")

def test_graphql_error_handling():
    """Test GraphQLError is raised on query errors."""
    executor = GraphQLExecutor(access_token="token")

    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = {
            'errors': [{'message': 'Field not found'}]
        }

        with pytest.raises(GraphQLError, match="Field not found"):
            executor.execute("query { invalidField }")
```

## Related References

- [Rate Limiting](rate-limiting.md) - Rate limit strategies and backoff
- [Pagination](pagination.md) - Handle pagination with error handling
- [Query Patterns](query-patterns.md) - Query construction best practices
- [SKILL.md](../SKILL.md) - Hub document with quick start
