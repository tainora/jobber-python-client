# Jobber Python Client

Minimal Python client for [Jobber GraphQL API](https://developer.getjobber.com/docs/) with OAuth 2.0 support.

## Features

- **One-time authentication**: Browser-based OAuth flow stores tokens in Doppler
- **Visual confirmation URLs**: Get web links to verify API operations in Jobber UI ([Quick Win Guide](docs/visual-confirmation-urls.md))
- **Fail-fast errors**: All failures raise exceptions with context
- **Token auto-refresh**: Transparent token refresh before expiration
- **Rate limit awareness**: Exposes throttle status, raises before exceeding limits
- **Minimal dependencies**: Only `requests` and `oauthlib` required

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/jobber-python-client.git
cd jobber-python-client

# Install dependencies
uv pip install requests oauthlib
```

## Prerequisites

1. **Jobber Developer Account**: Create app at https://developer.getjobber.com/
2. **Doppler CLI**: Install from https://docs.doppler.com/docs/install-cli
3. **OAuth Credentials**: Store in Doppler:
   ```bash
   doppler secrets set JOBBER_CLIENT_ID="your_client_id" \
     JOBBER_CLIENT_SECRET="your_client_secret" \
     --project claude-config --config dev
   ```

## Quick Start

### Step 1: Authenticate (one-time)

```bash
uv run jobber_auth.py
```

This will:

1. Open browser for Jobber authorization
2. Exchange authorization code for tokens
3. Store tokens in Doppler

### Step 2: Use in AI agent code

```python
from jobber import JobberClient

# Create client (loads credentials from Doppler)
client = JobberClient.from_doppler()

# Execute GraphQL queries
result = client.execute_query("""
    query {
        clients(first: 10) {
            nodes {
                id
                firstName
                lastName
            }
            totalCount
        }
    }
""")

print(f"Total clients: {result['clients']['totalCount']}")
```

## Visual Confirmation URLs (Quick Win!)

**Problem**: API operations feel abstract. You create a client via API, but can you see it in Jobber's web interface?

**Solution**: YES! Include `jobberWebUri` in your queries to get clickable web links.

### Example: Create Client with Web Link

```python
from jobber import JobberClient

client = JobberClient.from_doppler()

# IMPORTANT: Include jobberWebUri in mutation response
mutation = """
    mutation CreateClient($input: ClientCreate!) {
        clientCreate(input: $input) {
            client {
                id
                firstName
                lastName
                jobberWebUri  # ← Returns web URL!
            }
        }
    }
"""

result = client.execute_query(mutation, {
    'input': {
        'firstName': 'John',
        'lastName': 'Doe'
    }
})

created = result['clientCreate']['client']

# Show clickable link for visual confirmation
print(f"✅ Client created: {created['firstName']} {created['lastName']}")
print(f"🔗 View in Jobber: {created['jobberWebUri']}")
# Click link → See client in Jobber web UI → Instant verification!
```

### Available URL Fields

| Field          | Available On                                 | Purpose                                  |
| -------------- | -------------------------------------------- | ---------------------------------------- |
| `jobberWebUri` | Most resources (Client, Job, Quote, Invoice) | Direct link to resource in Jobber web UI |
| `previewUrl`   | Quotes                                       | Client Hub link for customer approval    |

### Quick Start

Run the complete example:

```bash
uv run examples/visual_confirmation_urls.py
```

**Learn more**: [Visual Confirmation URLs Guide](docs/visual-confirmation-urls.md) - Comprehensive patterns, best practices, and use cases.

**Pro tip**: ALWAYS include `jobberWebUri` in mutations for instant visual verification!

## API Reference

### JobberClient

Main client for executing GraphQL queries.

#### `JobberClient.from_doppler(project, config)`

Create client loading credentials from Doppler.

**Parameters:**

- `project` (str): Doppler project name (default: "claude-config")
- `config` (str): Doppler config name (default: "dev")

**Returns:** `JobberClient` instance

**Raises:**

- `ConfigurationError`: Doppler secrets not found
- `AuthenticationError`: Token loading fails

**Example:**

```python
client = JobberClient.from_doppler("claude-config", "dev")
```

#### `client.execute_query(query, variables=None, operation_name=None)`

Execute GraphQL query.

**Parameters:**

- `query` (str): GraphQL query string
- `variables` (dict, optional): Query variables
- `operation_name` (str, optional): Operation name for multi-operation queries

**Returns:** `dict` - Response data (response['data'])

**Raises:**

- `AuthenticationError`: Token invalid or expired
- `RateLimitError`: Rate limit threshold exceeded (< 20% points available)
- `GraphQLError`: Query execution failed
- `NetworkError`: HTTP request failed

**Example:**

```python
result = client.execute_query(
    query="""
        query GetClients($first: Int!) {
            clients(first: $first) {
                nodes { id firstName }
            }
        }
    """,
    variables={'first': 50}
)
```

#### `client.get_throttle_status()`

Get last known rate limit status.

**Returns:** `dict` or `None`

- `currentlyAvailable`: Points available now
- `maximumAvailable`: Total capacity (typically 10,000)
- `restoreRate`: Points restored per second (typically 500)

**Example:**

```python
status = client.get_throttle_status()
if status:
    print(f"{status['currentlyAvailable']} points available")
```

## Error Handling

All methods raise exceptions on failure. Handle appropriately:

```python
from jobber import (
    JobberClient,
    AuthenticationError,
    RateLimitError,
    GraphQLError,
    NetworkError,
)

try:
    client = JobberClient.from_doppler()
    result = client.execute_query("{ clients { totalCount } }")

except AuthenticationError as e:
    # Resolution: Run jobber_auth.py
    print(f"Auth error: {e}")

except RateLimitError as e:
    # Resolution: Wait for points to restore
    wait_seconds = e.context.get('wait_seconds', 0)
    print(f"Rate limited. Wait {wait_seconds:.1f}s")

except GraphQLError as e:
    # Resolution: Check query syntax
    print(f"Query error: {e.errors}")

except NetworkError as e:
    # Resolution: Check connectivity
    print(f"Network error: {e}")
```

## Examples

See [`examples/`](examples/) directory:

- [`basic_usage.py`](examples/basic_usage.py): Simple queries and pagination
- [`error_handling.py`](examples/error_handling.py): Comprehensive error handling patterns

Run examples:

```bash
uv run --with . examples/basic_usage.py
```

## Architecture

See [ADR-0001: Jobber API Client Architecture](docs/decisions/0001-jobber-api-client-architecture.md) for design decisions.

### Key Principles

1. **Fail-fast**: Raise exceptions immediately, no retry or fallback
2. **Caller control**: AI agent decides error recovery strategy
3. **Minimal abstraction**: Thin wrapper over GraphQL HTTP requests
4. **Explicit configuration**: No default values or silent assumptions

### Module Structure

```
jobber/
├── __init__.py       # Public API exports
├── client.py         # JobberClient class
├── auth.py           # TokenManager (Doppler integration)
├── graphql.py        # GraphQLExecutor (HTTP requests)
└── exceptions.py     # Exception hierarchy
```

## Rate Limiting

Jobber API limits:

- **10,000 points** available
- **500 points/second** restore rate
- **Query costs** vary (9-50 points typical)

This library:

- Raises `RateLimitError` when available points < 20% of maximum
- Exposes `throttle_status` in exception context
- Caller decides when to wait or abort

## Token Management

Tokens expire after **60 minutes**. This library:

- **Proactively refreshes** 5 minutes before expiration (background thread)
- **Reactively refreshes** on 401 errors (retry once)
- **Updates Doppler** with new tokens automatically

Token storage in Doppler:

```
JOBBER_ACCESS_TOKEN=eyJhbGc...
JOBBER_REFRESH_TOKEN=def502...
JOBBER_TOKEN_EXPIRES_AT=1731873600
```

## SLOs

- **Availability**: Simple code paths, minimal failure modes
- **Correctness**: Type-safe responses, validation at boundaries
- **Observability**: Exceptions include full context and stack traces
- **Maintainability**: < 500 LOC core library, clear contracts

## Development

### Running Tests

```bash
pytest -v
```

### Type Checking

```bash
mypy jobber/
```

### Linting

```bash
ruff check jobber/
```

## Contributing

This project uses [Conventional Commits](https://www.conventionalcommits.org/) and [semantic-release](https://semantic-release.gitbook.io/).

Commit format:

```
feat: add custom field support
fix: handle token refresh race condition
docs: update error handling examples
```

## License

MIT

## Support

- **Jobber API Docs**: https://developer.getjobber.com/docs/
- **API Support**: api-support@getjobber.com
- **Issues**: https://github.com/yourusername/jobber-python-client/issues

## Changelog

See [CHANGELOG.md](CHANGELOG.md) (auto-generated by semantic-release).
