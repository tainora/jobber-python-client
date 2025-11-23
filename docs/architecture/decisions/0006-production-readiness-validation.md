# ADR-0006: Production Readiness and API Validation

**Status**: Accepted
**Date**: 2025-11-22
**Deciders**: Terry Li
**Technical Story**: End-to-end validation of Jobber OAuth flow and GraphQL API integration

## Context

After completing skill extraction (ADR-0005), we attempted end-to-end validation of the OAuth authentication flow and API operations. This revealed two production blockers:

1. **OAuth Token Response Handling**: `jobber_auth.py` assumed Jobber's OAuth token endpoint returns `expires_in` field, but Jobber's actual response omits this field, causing authentication failures.

2. **GraphQL Schema Accuracy**: `test_create_client_url.py` used incorrect input type `ClientCreate` instead of `ClientCreateInput`, causing mutation failures.

Both issues were discovered during live API testing with real Jobber credentials and represent the difference between theoretical implementation and production reality.

## Decision

We will implement production readiness measures before any release:

1. **Fix OAuth Token Handling**: Default `expires_in` to 3600 seconds (1 hour) when Jobber omits the field, matching Jobber's documented token lifetime.

2. **Correct GraphQL Schemas**: Update all mutations to use actual Jobber API type names discovered through API error responses.

3. **Validate All Examples**: Run every example script against live Jobber API to surface any remaining schema or integration issues.

4. **Document Production Deployment**: Create runbook for OAuth setup, token refresh, and common troubleshooting scenarios.

5. **Semantic Versioning**: Use semantic-release to tag first production-ready version after validation passes.

## Consequences

### Positive

- **Real-world validation**: All code tested against production Jobber API, not just theoretical schemas
- **Fail-fast discovery**: API errors surface immediately during development, not in production use
- **Accurate documentation**: Examples and guides reflect actual API behavior
- **Production confidence**: OAuth flow and CRUD operations validated end-to-end

### Negative

- **API dependency**: Validation requires live Jobber developer account and OAuth app
- **Schema drift risk**: Jobber API changes could break validation; need monitoring
- **Test data cleanup**: Creating test clients during validation requires manual cleanup

### Neutral

- **Documentation overhead**: Maintaining both code examples and validation reports
- **Token lifecycle**: Access tokens expire hourly; automated testing needs token refresh

## Implementation

### Bugs Fixed

**1. OAuth Token Response** (`jobber_auth.py:342`)

```python
# Before (fails when expires_in missing)
save_tokens_to_doppler(
    token_data['access_token'],
    token_data['refresh_token'],
    token_data['expires_in']  # KeyError if missing
)

# After (defaults to 1 hour)
save_tokens_to_doppler(
    token_data['access_token'],
    token_data['refresh_token'],
    token_data.get('expires_in', 3600)  # Default to 1 hour
)
```

**Rationale**: Jobber documentation states access tokens expire in 60 minutes. Defaulting to 3600 seconds maintains security (tokens refresh before expiration) while handling API response variation.

**2. GraphQL Schema** (`test_create_client_url.py:19`)

```graphql
# Before (incorrect type name)
mutation CreateClient($input: ClientCreate!) {
    clientCreate(input: $input) { ... }
}

# After (correct type name from API error)
mutation CreateClient($input: ClientCreateInput!) {
    clientCreate(input: $input) { ... }
}
```

**Rationale**: Jobber GraphQL API error message explicitly suggested `ClientCreateInput`. This is the canonical type name in Jobber's schema.

### Validation Results

**OAuth Flow** (via `jobber_auth.py`):

- ✅ Browser authorization successful
- ✅ PKCE code exchange successful
- ✅ Tokens stored in Doppler (`JOBBER_ACCESS_TOKEN`, `JOBBER_REFRESH_TOKEN`, `JOBBER_TOKEN_EXPIRES_AT`)
- ✅ `JobberClient.from_doppler()` loads credentials correctly

**GraphQL Queries** (via `list_existing_clients.py`):

- ✅ Retrieved 1 existing client (John Doe - Test Company)
- ✅ `jobberWebUri` field returned: `https://secure.getjobber.com/clients/123238532`
- ✅ URL clickable in iTerm2 (Cmd+Click opens in browser)

**GraphQL Mutations** (via `test_create_client_url.py`):

- ✅ Created new client (Test Client - Demo Company)
- ✅ `jobberWebUri` field returned: `https://secure.getjobber.com/clients/123679362`
- ✅ URL confirmed working in Jobber web interface

**Visual Confirmation Pattern**:

- ✅ ANSI OSC 8 hyperlinks render in iTerm2
- ✅ `format_success()` helper formats output correctly
- ✅ URLs open actual Jobber resources (verified manually)

## Alternatives Considered

### 1. Hard-code `expires_in` in token response

**Rejected**: Violates single source of truth. If Jobber changes token lifetime, code breaks silently. Defaulting preserves explicit API contract while handling missing field.

### 2. Use Jobber's GraphQL introspection to validate schemas

**Deferred**: Introspection would catch schema errors earlier, but adds complexity. Current approach (fix on error) works for small API surface. Consider for future if schema errors increase.

### 3. Mock Jobber API for testing

**Rejected**: Mocks can't catch real-world issues like missing `expires_in` field or schema name differences. Real API testing is the only way to validate production readiness.

## Follow-up Tasks

- [ ] Validate remaining example scripts (`examples/basic_usage.py`, `examples/error_handling.py`)
- [ ] Create client deletion script for test data cleanup
- [ ] Document OAuth troubleshooting scenarios (port conflicts, browser issues, token expiration)
- [ ] Set up proactive token refresh testing (verify refresh works before expiration)
- [ ] Add GraphQL schema validation tests (detect type name changes automatically)

## References

- [Jobber OAuth Documentation](https://developer.getjobber.com/docs/building_your_app/app_authorization/)
- [Jobber GraphQL API](https://api.getjobber.com/api/graphql)
- OAuth token response: No `expires_in` field observed in production
- GraphQL error: "ClientCreate isn't a defined input type (Did you mean ClientCreateInput?)"
- ADR-0005: Skill Extraction (prerequisite for this validation)
