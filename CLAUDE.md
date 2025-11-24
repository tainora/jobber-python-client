# Jobber Python Client

Minimal Python client for [Jobber GraphQL API](https://developer.getjobber.com/docs/) designed for AI coding agents and automation workflows.

**Navigation Index**: [`docs/`](docs/) - Architecture decisions, implementation plans, and technical documentation

**Quick Links**: [README](README.md) | [Examples](examples/) | [ADR](docs/architecture/decisions/) | [Skills](skills/) | [Catalog](catalog-info.yaml)

## Overview

Production-ready Python client for Jobber GraphQL API with OAuth 2.0 PKCE authentication and Doppler token storage.

**Use Cases**:

- AI agents requiring programmatic Jobber access
- Automation workflows (client/job management)
- GraphQL query execution without manual intervention

**Key Features**:

- ✅ One-time browser OAuth, then fully automated
- ✅ Visual confirmation URLs (jobberWebUri for instant verification)
- ✅ Fail-fast error handling (caller controls retry)
- ✅ Token auto-refresh (proactive + reactive)
- ✅ Rate limit awareness with early warnings
- ✅ Minimal dependencies (requests, oauthlib)

**Project Stats**:

- Core library: 1,701 LOC (9 modules, 384 executable statements)
- Examples: 6 (usage, error handling, visual URLs, photos, introspection, webhooks)
- Tests: 129 unit tests (98% code coverage, 100% module coverage)
- Documentation: MADR + Google Design Docs + README + Skills

## Quick Start

**Prerequisites**: Jobber Developer Account, Doppler CLI, OAuth credentials in Doppler

**One-time authentication**:

```bash
uv run jobber_auth.py
```

**Use in code**:

```python
from jobber import JobberClient

client = JobberClient.from_doppler()
result = client.execute_query("{ clients { totalCount } }")
```

**Complete documentation**: [README.md](README.md)

## API Reference

See [README.md#api-reference](README.md#api-reference) for complete API documentation.

**Main classes**:

- `JobberClient` - GraphQL query executor
- `TokenManager` - OAuth token lifecycle ([jobber/auth.py](jobber/auth.py))
- `GraphQLExecutor` - HTTP request handler ([jobber/graphql.py](jobber/graphql.py))

**Exception hierarchy**:

```
JobberException (base)
├── ConfigurationError    - Doppler secrets missing
├── AuthenticationError   - OAuth token invalid/expired
├── RateLimitError        - Rate limit threshold exceeded
├── GraphQLError          - Query execution failed
└── NetworkError          - HTTP request failed
```

**Reference**: [jobber/exceptions.py](jobber/exceptions.py)

## Architecture & Design

### Design Philosophy

**Fail-fast behavior**: All errors raise exceptions immediately. No retry, no fallback, no silent failures. Caller decides recovery strategy.

**Key Principles** (from [ADR-0001](docs/architecture/decisions/0001-jobber-api-client-architecture.md)):

1. **Simple codebase** - Easy to understand, test, maintain
2. **Predictable behavior** - No hidden retry loops or sleep delays
3. **Clear errors** - Stack traces point to actual failure cause
4. **Caller control** - AI agent decides error recovery strategy
5. **Minimal surface area** - Fewer ways for library to fail

**Design Trade-offs**:

- ✅ Simple code paths → ❌ Caller must handle errors
- ✅ Predictable latency → ❌ No automatic retry on network blips
- ✅ Clear failures → ❌ Manual pagination required
- ✅ Type safety → ❌ Token refresh can fail (must handle)

### Module Structure

```
jobber/
├── __init__.py       # Public API exports (44 lines)
├── client.py         # JobberClient facade (136 lines)
├── auth.py           # TokenManager + Doppler integration (355 lines)
├── graphql.py        # GraphQLExecutor + HTTP requests (189 lines)
└── exceptions.py     # Exception hierarchy (143 lines)

Total: 867 LOC
```

**Component Responsibilities**:

- **[client.py](jobber/client.py)**: Facade coordinating auth + graphql
- **[auth.py](jobber/auth.py)**: Token lifecycle (load, refresh, save to Doppler)
- **[graphql.py](jobber/graphql.py)**: HTTP requests, rate limit parsing, error handling
- **[exceptions.py](jobber/exceptions.py)**: Structured error hierarchy with context

### Documentation Architecture

**MADR (Architectural Decision Records)**:

- [ADR-0001: Jobber API Client Architecture](docs/architecture/decisions/0001-jobber-api-client-architecture.md) - Core design decisions (fail-fast, Doppler, minimal dependencies)
- [ADR-0002: OAuth PKCE Skill Extraction](docs/architecture/decisions/0002-oauth-pkce-skill-extraction.md) - Skill creation decision and rationale
- [ADR-0003: Visual Confirmation URLs](docs/architecture/decisions/0003-visual-confirmation-urls.md) - Get web UI links from APIs for instant verification
- [ADR-0004: URL Helpers Unit Tests](docs/architecture/decisions/0004-url-helpers-unit-tests.md) - Test coverage for URL helper functions
- [ADR-0005: Skill Extraction](docs/architecture/decisions/0005-skill-extraction-visual-urls-graphql.md) - visual-confirmation-urls and graphql-query-execution skills
- [ADR-0006: Production Readiness Validation](docs/architecture/decisions/0006-production-readiness-validation.md) - End-to-end validation and release workflow

**Implementation Plans** (Google Design Doc format):

- [plan.md (0006)](docs/development/plan/0006-production-readiness-validation/plan.md) - Production readiness and API validation

**Service Metadata**:

- [catalog-info.yaml](catalog-info.yaml) - Backstage service catalog integration

## Skills & Patterns

### OAuth 2.0 PKCE with Doppler Integration

**Skill**: [`oauth-pkce-doppler`](skills/oauth-pkce-doppler/SKILL.md)

**Pattern**: Browser-based OAuth flow with PKCE security, storing tokens in Doppler secrets manager

**Implementation**:

- **One-time authorization**: [`jobber_auth.py`](jobber_auth.py) (355 lines, PEP 723 script)
- **Token lifecycle**: [`jobber/auth.py`](jobber/auth.py) (TokenManager with proactive + reactive refresh)
- **Skill templates**: [skills/oauth-pkce-doppler/assets/](skills/oauth-pkce-doppler/assets/)

**Key Components**:

- PKCE code verifier/challenge generation (SHA-256)
- Temporary HTTP callback server (ports 3000-3010)
- Token exchange and Doppler storage
- Proactive refresh (background thread, 5min buffer)
- Reactive refresh (on 401 errors)
- Thread-safe token access

**Reusability**: Pattern is API-agnostic. Skill provides parameterized templates for:

- GitHub OAuth
- Google OAuth
- Stripe OAuth
- Any OAuth 2.0 provider supporting PKCE

**Skill Documentation**:

- **[Quick Start](skills/oauth-pkce-doppler/SKILL.md#quick-start)** - Copy-paste implementation
- **[Security Considerations](skills/oauth-pkce-doppler/references/security-considerations.md)** - OAuth security model, PKCE, token storage
- **[Doppler Integration](skills/oauth-pkce-doppler/references/doppler-integration.md)** - CLI setup, secret naming, workflows
- **[PKCE Implementation](skills/oauth-pkce-doppler/references/pkce-implementation.md)** - RFC 7636 technical details
- **[Token Lifecycle](skills/oauth-pkce-doppler/references/token-lifecycle.md)** - Refresh strategies, threading, concurrency
- **[Troubleshooting](skills/oauth-pkce-doppler/references/troubleshooting.md)** - Common errors, debugging techniques

**Examples**:

- [basic_oauth_flow.py](skills/oauth-pkce-doppler/examples/basic_oauth_flow.py) - Minimal PKCE flow
- [custom_callback_server.py](skills/oauth-pkce-doppler/examples/custom_callback_server.py) - Advanced callback patterns
- [error_handling_patterns.py](skills/oauth-pkce-doppler/examples/error_handling_patterns.py) - Comprehensive error scenarios

### Rate Limiting Strategy

**Pattern**: Expose throttle status, raise exception before hitting limits

**Implementation**: [graphql.py:67-93](jobber/graphql.py) parses `throttleStatus` from every response

**Behavior**:

- Raises `RateLimitError` when available points < 20% of maximum
- Includes wait time calculation in exception context
- Caller decides whether to wait or abort

**Jobber API Limits**:

- 10,000 points available
- 500 points/second restore rate
- Query costs: 9-50 points typical

**Example**:

```python
try:
    result = client.execute_query(large_query)
except RateLimitError as e:
    wait_seconds = e.context.get('wait_seconds', 0)
    print(f"Rate limited. Wait {wait_seconds:.1f}s")
    time.sleep(wait_seconds)
    result = client.execute_query(large_query)  # Retry
```

### Token Auto-Refresh

**Pattern**: Proactive background refresh + reactive retry

**Implementation**: [auth.py:126-191](jobber/auth.py) TokenManager

**Proactive Refresh**:

- Background thread refreshes 5 minutes before expiration
- Prevents 401 errors during API calls
- Timer reschedules after each refresh

**Reactive Refresh**:

- Retry once on 401 errors
- Handles race conditions (token expired between check and use)
- Updates Doppler with new tokens

**Token Storage** (Doppler secrets):

- `JOBBER_ACCESS_TOKEN` - Short-lived (60 minutes)
- `JOBBER_REFRESH_TOKEN` - Long-lived (until revoked)
- `JOBBER_TOKEN_EXPIRES_AT` - Unix timestamp

**Thread Safety**: Lock-protected token access for concurrent use

### Visual Confirmation URLs

**Skill**: [`visual-confirmation-urls`](skills/visual-confirmation-urls/SKILL.md)

**Pattern**: Get web UI links from APIs for instant visual verification of operations

**Implementation**:

- **URL helpers**: [`jobber/url_helpers.py`](jobber/url_helpers.py) (156 LOC with format_success, clickable_link, validate_url)
- **Guide**: [`docs/visual-confirmation-urls.md`](docs/visual-confirmation-urls.md) (495 lines with use cases and best practices)
- **Unit tests**: [`tests/test_url_helpers.py`](tests/test_url_helpers.py) (19 tests, 100% pass)

**Key Components**:

- `format_success()` - Format success message with web link
- `clickable_link()` - ANSI OSC 8 terminal hyperlinks (Cmd+Click to open)
- `validate_url()` - Validate jobberWebUri presence with fail-fast errors
- Pattern: Always include `jobberWebUri` in GraphQL queries for visual confirmation

**Reusability**: API-agnostic pattern applicable to:

- ✅ **Jobber**: `jobberWebUri`, `previewUrl`
- ✅ **Stripe**: `receipt_url`, `hosted_invoice_url`
- ✅ **GitHub**: `html_url`
- ✅ **Linear**: `url`
- ✅ **Asana**: `permalink_url`

**Skill Documentation**:

- **[API Integration](skills/visual-confirmation-urls/references/api-integration.md)** - Complete API coverage (Jobber, Stripe, GitHub, Linear)
- **[Terminal Hyperlinks](skills/visual-confirmation-urls/references/terminal-hyperlinks.md)** - ANSI OSC 8 implementation and terminal support
- **[Use Cases](skills/visual-confirmation-urls/references/use-cases.md)** - 5 detailed patterns (create, query, automation, validation, dual URLs)

**Examples**:

- [create_with_url.py](skills/visual-confirmation-urls/examples/create_with_url.py) - Create resource with URL confirmation
- [query_with_urls.py](skills/visual-confirmation-urls/examples/query_with_urls.py) - Query results with clickable links
- [quote_dual_urls.py](skills/visual-confirmation-urls/examples/quote_dual_urls.py) - Quotes with team + client URLs
- [url_validation.py](skills/visual-confirmation-urls/examples/url_validation.py) - URL-based resource validation
- [batch_with_urls.py](skills/visual-confirmation-urls/examples/batch_with_urls.py) - Batch operations with URL feedback

### GraphQL Query Execution

**Skill**: [`graphql-query-execution`](skills/graphql-query-execution/SKILL.md)

**Pattern**: Execute GraphQL queries with error handling, pagination, and rate limiting

**Implementation**:

- **GraphQL executor**: [`jobber/graphql.py`](jobber/graphql.py) (189 LOC with HTTP requests, error parsing, throttle checking)
- **Examples**: [`examples/basic_usage.py`](examples/basic_usage.py), [`examples/error_handling.py`](examples/error_handling.py)

**Key Components**:

- Query construction → HTTP POST → Response parsing → Error handling
- Rate limit threshold checking (raise before hitting limits)
- Pagination support (cursor-based, Relay spec)
- Fail-fast exception hierarchy (NetworkError, AuthenticationError, GraphQLError, RateLimitError)

**Reusability**: Applicable to GraphQL APIs:

- ✅ **Jobber**: Cost-based throttling, custom version headers
- ✅ **Shopify**: Cost-based rate limiting (GraphQL Admin API)
- ✅ **GitHub**: Points-based rate limiting
- ✅ **Stripe**: Query cost tracking
- ✅ **Contentful**: GraphQL CDA/CMA
- ✅ **Linear**: Standard GraphQL with pagination

**Skill Documentation**:

- **[Error Handling](skills/graphql-query-execution/references/error-handling.md)** - Exception hierarchy, recovery patterns, testing
- **[Pagination](skills/graphql-query-execution/references/pagination.md)** - Cursor-based paging, streaming results, progress reporting
- **[Rate Limiting](skills/graphql-query-execution/references/rate-limiting.md)** - Throttle strategies, backoff, query cost optimization
- **[Query Patterns](skills/graphql-query-execution/references/query-patterns.md)** - Query construction, fragments, directives, best practices

**Examples**:

- [basic_query.py](skills/graphql-query-execution/examples/basic_query.py) - Basic query execution
- [with_variables.py](skills/graphql-query-execution/examples/with_variables.py) - Query with variables (type-safe)
- [pagination.py](skills/graphql-query-execution/examples/pagination.py) - Cursor-based pagination (fetch all pages)
- [error_handling.py](skills/graphql-query-execution/examples/error_handling.py) - Comprehensive error handling (all exception types)

## Development

### Prerequisites

- Python 3.12+ (required by [pyproject.toml](pyproject.toml))
- uv package manager (recommended)
- Doppler CLI (required for secrets)

### Development Workflow

```bash
# Install dependencies
uv sync --dev

# Run tests
pytest -v

# Type checking
mypy jobber/

# Linting
ruff check jobber/

# Run examples
uv run --with . examples/basic_usage.py
```

### Quality Standards

**Validation results** (all passing):

- ✅ Tests: 129/129 passed (98% code coverage, 100% module coverage)
- ✅ Ruff: 0 errors (formatting applied to all files)
- ✅ Mypy: 0 errors (strict mode, type stubs installed)
- ✅ Coverage: 384 statements, 9 missing (auth timer logic, client bug)

**Code quality configuration**:

- Python version: 3.12
- Mypy: `disallow_untyped_defs = true` (strict typing)
- Ruff: Line length 100, target Python 3.12
- All public APIs have type hints

**Standards alignment** (from [`~/.claude/CLAUDE.md`](/Users/terryli/.claude/CLAUDE.md)):

- **Python**: uv (package management), PEP 723 (inline dependencies)
- **Testing**: pytest (test runner)
- **Type Safety**: mypy (static analysis)
- **Linting**: ruff (fast Python linter)
- **Versioning**: semantic-release (conventional commits)

## Examples

**See [examples/](examples/) directory for runnable code.**

- **[basic_usage.py](examples/basic_usage.py)** - Account queries, pagination, throttle status
- **[error_handling.py](examples/error_handling.py)** - Comprehensive exception handling patterns
- **[visual_confirmation_urls.py](examples/visual_confirmation_urls.py)** - Get web links for visual verification ([Quick Win!](docs/visual-confirmation-urls.md))

**Run examples**:

```bash
# Basic usage
uv run --with . examples/basic_usage.py

# Error handling patterns
uv run --with . examples/error_handling.py

# Visual confirmation URLs (recommended!)
uv run examples/visual_confirmation_urls.py
```

## Documentation Standards

Following [`~/.claude/CLAUDE.md`](/Users/terryli/.claude/CLAUDE.md) documentation standards:

- **Hub-and-spoke architecture**: This file links to detailed docs
- **Progressive disclosure**: Overview → Details → Source code
- **No manual section numbering**: Use Pandoc `--number-sections` for PDFs
- **Machine-readable specs**: [catalog-info.yaml](catalog-info.yaml) (Backstage), [plan.yaml](docs/plan/) (implementation)

**Progressive Disclosure Levels**:

1. **CLAUDE.md** (this file) - What/why/when, navigation links
2. **README/ADR/plan** - Complete reference, design decisions
3. **Source code** - Implementation details

## Project Metadata

### Backstage Integration

**Service Catalog**: [catalog-info.yaml](catalog-info.yaml)

- Component type: library
- Lifecycle: experimental
- Owner: terry-li
- System: automation
- Depends on: doppler-secrets-manager

### SLOs (from [plan.yaml](docs/plan/0001-jobber-api-client/plan.yaml))

- **Availability**: 99.9% (simple code paths, minimal failure modes)
- **Correctness**: 100% (type-safe responses, validation at boundaries)
- **Observability**: All errors logged with context
- **Maintainability**: < 500 LOC target (867 actual, justified)

**SLO Targets**:

- Simple code paths reduce failure modes
- Type-safe responses prevent data corruption
- Context-rich exceptions enable debugging
- < 500 LOC ideal, exceeded for comprehensive error handling

### Conventional Commits

This project uses [semantic-release](https://semantic-release.gitbook.io/) with conventional commits:

```
feat: add custom field support
fix: handle token refresh race condition
docs: update error handling examples
```

**Configuration**: [.releaserc.json](.releaserc.json)
**Workflow**: [.github/workflows/release.yml](.github/workflows/release.yml)

## References

- **Jobber API Documentation**: https://developer.getjobber.com/docs/
- **OAuth 2.0 RFC 6749**: https://tools.ietf.org/html/rfc6749
- **PKCE RFC 7636**: https://tools.ietf.org/html/rfc7636
- **Doppler Documentation**: https://docs.doppler.com/docs
- **Global Standards**: [`~/.claude/CLAUDE.md`](/Users/terryli/.claude/CLAUDE.md)
- **Documentation Standards**: [`~/.claude/skills/documentation-standards/`](/Users/terryli/.claude/skills/documentation-standards/)
- **Skill Architecture**: [`~/.claude/skills/skill-architecture/`](/Users/terryli/.claude/skills/skill-architecture/)
