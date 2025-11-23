# 1. Jobber API Client Architecture

Date: 2025-11-17

## Status

Accepted

## Context

AI coding agents require programmatic access to Jobber's GraphQL API for automation workflows. The Jobber API uses OAuth 2.0 Authorization Code flow, which requires browser-based user authorization. After initial authorization, agents need to execute GraphQL operations without manual intervention.

### Requirements

1. **One-time OAuth authorization**: Browser-based flow stores tokens in secrets manager
2. **Programmatic access**: Python library for AI agent import and use
3. **Fail-fast behavior**: Errors propagate to caller; no silent failures or automatic retry
4. **Token lifecycle**: Automatic refresh before expiration
5. **Rate limit awareness**: Surface throttle status to caller
6. **Minimal dependencies**: Leverage existing OSS libraries

### Constraints

- OAuth requires browser access (cannot be fully automated)
- Access tokens expire (60 minutes typical)
- Rate limits exist (10,000 points, restore at 500/second)
- AI agents cannot handle interactive prompts
- Secrets must not be stored in code or version control

## Decision

Build a minimal Python library with two components:

1. **One-time authorization script** (`jobber_auth.py`): Handles OAuth flow, stores tokens in Doppler
2. **GraphQL client library** (`jobber/`): Loads tokens, executes queries, refreshes when expired

### Key Architectural Choices

**Token Storage**: Use Doppler CLI for secrets management

- Rationale: Already deployed, supports fallback files, encrypted at rest
- Alternative considered: Local encrypted files (rejected - no cross-machine sync)

**Error Handling**: Raise and propagate all errors

- Rationale: Caller decides retry strategy; library stays simple
- Alternative considered: Automatic retry with exponential backoff (rejected - complexity, opaque failures)

**Rate Limiting**: Expose throttle status, raise exception when low

- Rationale: Caller controls when to wait or abort
- Alternative considered: Auto-sleep until points available (rejected - unpredictable latency)

**Pagination**: Manual cursor handling

- Rationale: Caller controls page size and stopping condition
- Alternative considered: Auto-fetch all pages (rejected - unbounded operations)

**Token Refresh**: Proactive background refresh + reactive on 401

- Rationale: Prevents mid-operation failures while failing fast on error
- Alternative considered: Only reactive (rejected - causes operation interruption)

## Consequences

### Positive

- **Simple codebase**: Easy to understand, test, and maintain
- **Predictable behavior**: No hidden retry loops or sleep delays
- **Clear errors**: Stack traces point to actual failure cause
- **Caller control**: AI agent decides error recovery strategy
- **Minimal surface area**: Fewer ways for library to fail

### Negative

- **Caller must handle errors**: Every API call can raise exceptions
- **No automatic recovery**: Network blips require caller retry
- **Manual pagination**: Caller implements page iteration
- **Token refresh can fail**: Must handle refresh errors explicitly

### Mitigations

- Comprehensive exception hierarchy with error context
- Helper methods for common patterns (but not automatic)
- Clear documentation on expected errors per operation
- Examples showing proper error handling

## Implementation

### Module Structure

```
jobber/
├── __init__.py          # Exports: JobberClient, exceptions
├── client.py            # Main GraphQL client
├── auth.py              # Token manager (Doppler integration)
├── graphql.py           # GraphQL request executor
├── exceptions.py        # Exception hierarchy
└── models.py            # Pydantic response models (optional)
```

### Dependency Selection

- **requests**: HTTP client (battle-tested, synchronous)
- **oauthlib**: PKCE generation (OAuth 2.0 standard library)
- **pydantic**: Response validation (optional, for type safety)
- **subprocess**: Doppler CLI integration (stdlib)

Rejected:

- **httpx**: Async-focused, unnecessary complexity
- **gql/sgqlc**: Opinionated GraphQL clients, too heavy
- **authlib**: Full OAuth suite, overkill for client_credentials

### SLO Alignment

**Availability**: Simple code path, fewer failure modes
**Correctness**: Type-safe models, validation at boundaries
**Observability**: Structured exceptions with context
**Maintainability**: Minimal abstraction layers, clear contracts

## Validation

Auto-validate on build:

1. OAuth script successfully exchanges code for token
2. Client can load tokens from Doppler
3. GraphQL queries execute and parse responses
4. Token refresh succeeds when expired
5. Rate limit exception raised at threshold
6. All errors include actionable context

## References

- Jobber API Documentation: https://developer.getjobber.com/docs/
- OAuth 2.0 RFC 6749: https://tools.ietf.org/html/rfc6749
- PKCE RFC 7636: https://tools.ietf.org/html/rfc7636
- MADR Template: https://adr.github.io/madr/
