# GraphQL Rate Limiting

Proactive rate limit management strategies for GraphQL APIs.

## Rate Limit Concepts

### Cost-Based Rate Limiting

Many GraphQL APIs use cost-based rate limiting:

- Each query has a **cost** (calculated by complexity)
- API provides **maximum points** (quota capacity)
- **Currently available points** decrease with each query
- Points **restore** at a fixed rate (e.g., 500 points/second)

**Example Response**:
```json
{
  "data": { ... },
  "extensions": {
    "cost": {
      "requestedQueryCost": 152,
      "actualQueryCost": 152,
      "throttleStatus": {
        "maximumAvailable": 10000,
        "currentlyAvailable": 8500,
        "restoreRate": 500
      }
    }
  }
}
```

### Threshold-Based Monitoring

Check available points after each query:

```python
executor = GraphQLExecutor(
    access_token=token,
    rate_limit_threshold=0.20  # Raise error if < 20% available
)

try:
    result = executor.execute(query)
except RateLimitError as e:
    # Available points < 20% threshold
    wait_seconds = e.context['wait_seconds']
    print(f"Rate limit low. Wait {wait_seconds:.1f}s")
```

## Rate Limit Strategies

### Strategy 1: Proactive Monitoring

Check throttle status after each query:

```python
def execute_with_monitoring(executor, query, variables=None):
    """Execute query with proactive rate limit monitoring."""
    result = executor.execute(query, variables)

    # Check throttle status
    throttle = executor.get_throttle_status()
    if throttle:
        available = throttle['currentlyAvailable']
        maximum = throttle['maximumAvailable']
        pct = available / maximum * 100

        print(f"Rate limit: {available}/{maximum} ({pct:.1f}%)")

        if pct < 30:
            print(f"⚠️  Rate limit low!")

    return result
```

### Strategy 2: Wait and Retry

Wait for points to restore when rate limit hit:

```python
import time

def execute_with_wait(executor, query, variables=None):
    """Execute query, wait if rate limit hit."""
    try:
        result = executor.execute(query, variables)
        return result

    except RateLimitError as e:
        wait_seconds = e.context['wait_seconds']
        print(f"Rate limit hit. Waiting {wait_seconds:.1f}s...")
        time.sleep(wait_seconds)

        # Retry after wait
        return executor.execute(query, variables)
```

### Strategy 3: Exponential Backoff

Increase wait time with each retry:

```python
def execute_with_backoff(executor, query, variables=None, max_retries=5):
    """Execute query with exponential backoff."""
    for attempt in range(max_retries):
        try:
            result = executor.execute(query, variables)
            return result

        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise  # Max retries exceeded

            wait_seconds = e.context['wait_seconds']
            backoff = wait_seconds * (2 ** attempt)

            print(f"Retry {attempt+1}/{max_retries}. Waiting {backoff:.1f}s...")
            time.sleep(backoff)

    raise RuntimeError("Max retries exceeded")
```

### Strategy 4: Queue for Later

Enqueue queries when rate limit hit:

```python
from queue import Queue
import threading
import time

class RateLimitedExecutor:
    """Execute queries with rate limit queue."""

    def __init__(self, executor, queue_max_size=100):
        self.executor = executor
        self.queue = Queue(maxsize=queue_max_size)
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def execute_async(self, query, variables=None, callback=None):
        """Enqueue query for asynchronous execution."""
        self.queue.put((query, variables, callback))

    def _worker(self):
        """Worker thread to process queued queries."""
        while True:
            query, variables, callback = self.queue.get()

            try:
                result = self.executor.execute(query, variables)
                if callback:
                    callback(result, None)

            except RateLimitError as e:
                # Wait and retry
                wait_seconds = e.context['wait_seconds']
                time.sleep(wait_seconds)
                self.queue.put((query, variables, callback))  # Re-queue

            except Exception as e:
                if callback:
                    callback(None, e)

            finally:
                self.queue.task_done()

# Usage
rate_limited = RateLimitedExecutor(executor)

def handle_result(result, error):
    if error:
        print(f"Error: {error}")
    else:
        print(f"Result: {result}")

rate_limited.execute_async(query, variables, callback=handle_result)
```

### Strategy 5: Adaptive Rate Limiting

Adjust query rate based on available points:

```python
class AdaptiveExecutor:
    """Execute queries with adaptive rate limiting."""

    def __init__(self, executor):
        self.executor = executor
        self.last_throttle = None

    def execute(self, query, variables=None):
        """Execute with adaptive delay."""
        # Calculate delay based on last throttle status
        if self.last_throttle:
            available = self.last_throttle['currentlyAvailable']
            maximum = self.last_throttle['maximumAvailable']
            pct = available / maximum

            if pct < 0.50:
                # Low points - wait before next query
                delay = 1.0 / (pct + 0.1)  # More delay when fewer points
                time.sleep(delay)

        # Execute query
        result = self.executor.execute(query, variables)

        # Update throttle status
        self.last_throttle = self.executor.get_throttle_status()

        return result
```

## Query Cost Optimization

### Minimize Query Cost

Reduce query cost by:

1. **Fetch only required fields** (avoid over-fetching)
2. **Limit result set size** (`first: 10` instead of `first: 100`)
3. **Avoid deep nesting** (reduce complexity)
4. **Use fragments** (reduce duplication)

**Example**:
```graphql
# ❌ High cost (over-fetching, large result set)
query {
  clients(first: 100) {
    nodes {
      id
      firstName
      lastName
      emails
      phoneNumbers
      addresses
      jobs {
        nodes {
          id
          title
          visits {
            nodes {
              id
              startAt
            }
          }
        }
      }
    }
  }
}

# ✅ Low cost (minimal fields, small result set)
query {
  clients(first: 10) {
    nodes {
      id
      firstName
    }
  }
}
```

### Query Cost Introspection

Some APIs support query cost introspection:

```graphql
query {
  __schema {
    queryType {
      name
    }
  }
  # Check if API provides cost estimation
}
```

## Batching Strategies

### Sequential Batching

Execute queries sequentially to avoid overwhelming rate limit:

```python
def execute_batch_sequential(executor, queries, delay=0.1):
    """Execute batch of queries sequentially with delay."""
    results = []

    for query in queries:
        result = executor.execute(query)
        results.append(result)

        # Small delay between queries
        time.sleep(delay)

    return results
```

### Concurrent with Rate Limit

Use concurrent execution with rate limit monitoring:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def execute_batch_concurrent(executor, queries, max_workers=5):
    """Execute batch with concurrent workers and rate limit handling."""
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(execute_with_wait, executor, q): q for q in queries}

        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Query failed: {e}")

    return results
```

## Monitoring and Alerts

### Real-Time Monitoring

```python
class MonitoredExecutor:
    """Execute queries with real-time rate limit monitoring."""

    def __init__(self, executor, alert_threshold=0.30):
        self.executor = executor
        self.alert_threshold = alert_threshold
        self.query_count = 0

    def execute(self, query, variables=None):
        """Execute with monitoring."""
        result = self.executor.execute(query, variables)
        self.query_count += 1

        # Check throttle status
        throttle = self.executor.get_throttle_status()
        if throttle:
            available = throttle['currentlyAvailable']
            maximum = throttle['maximumAvailable']
            pct = available / maximum

            # Alert if below threshold
            if pct < self.alert_threshold:
                self._send_alert(pct, available, maximum)

        return result

    def _send_alert(self, pct, available, maximum):
        """Send rate limit alert."""
        print(f"🚨 RATE LIMIT ALERT: {available}/{maximum} ({pct*100:.1f}%)")
        # Send to monitoring system (Datadog, CloudWatch, etc.)
```

### Metrics Collection

```python
import time

class MetricsExecutor:
    """Execute queries with metrics collection."""

    def __init__(self, executor):
        self.executor = executor
        self.metrics = {
            'queries': 0,
            'errors': 0,
            'rate_limit_hits': 0,
            'total_duration': 0
        }

    def execute(self, query, variables=None):
        """Execute with metrics."""
        start_time = time.time()

        try:
            result = self.executor.execute(query, variables)
            self.metrics['queries'] += 1
            return result

        except RateLimitError as e:
            self.metrics['rate_limit_hits'] += 1
            self.metrics['errors'] += 1
            raise

        except Exception as e:
            self.metrics['errors'] += 1
            raise

        finally:
            duration = time.time() - start_time
            self.metrics['total_duration'] += duration

    def get_metrics(self):
        """Get collected metrics."""
        avg_duration = self.metrics['total_duration'] / max(self.metrics['queries'], 1)
        return {
            **self.metrics,
            'avg_duration': avg_duration,
            'success_rate': (self.metrics['queries'] - self.metrics['errors']) / max(self.metrics['queries'], 1)
        }
```

## API-Specific Rate Limits

### Jobber

- **Max points**: 10,000
- **Restore rate**: 500 points/second
- **Recommended threshold**: 20%

### Shopify

- **Max points**: Varies by plan (typically 1,000-10,000)
- **Restore rate**: 50 points/second
- **Recommended threshold**: 25%

### GitHub

- **Max points**: 5,000 points/hour
- **Restore rate**: ~1.4 points/second
- **Recommended threshold**: 30%

## Related References

- [Error Handling](error-handling.md) - Handle RateLimitError exceptions
- [Pagination](pagination.md) - Rate limit management during pagination
- [Query Patterns](query-patterns.md) - Optimize query cost
- [SKILL.md](../SKILL.md) - Hub document with quick start
