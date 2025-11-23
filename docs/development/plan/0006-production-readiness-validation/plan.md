# Plan: Production Readiness and API Validation

## Metadata

- **ADR ID**: 0006
- **ADR Link**: `../../../architecture/decisions/0006-production-readiness-validation.md`
- **Status**: In Progress
- **Created**: 2025-11-22
- **Updated**: 2025-11-22
- **Owner**: Terry Li

## Context

### Background

Skill extraction (ADR-0005) completed successfully, creating two validated skills:

- `visual-confirmation-urls` - Pattern for getting web UI links from APIs
- `graphql-query-execution` - Pattern for GraphQL execution with error handling

Both skills contain example code referencing Jobber API, but examples were untested against live API.

### Motivation

End-to-end validation revealed production blockers:

1. **OAuth Token Handling Bug**: `jobber_auth.py` crashed when Jobber's OAuth endpoint omitted `expires_in` field (real API behavior differs from OAuth 2.0 spec).

2. **GraphQL Schema Mismatch**: `test_create_client_url.py` used incorrect type name `ClientCreate` instead of `ClientCreateInput` (documentation outdated).

3. **Untested Examples**: Skill examples never executed against real Jobber API, risking incorrect patterns in reusable templates.

### Current State

**Fixed** (during validation):

- ✅ OAuth token handling (`expires_in` defaults to 3600s)
- ✅ Client creation mutation (corrected to `ClientCreateInput`)
- ✅ OAuth flow validated end-to-end
- ✅ List clients query validated
- ✅ Create client mutation validated

**Untested**:

- ❌ `examples/basic_usage.py` (pagination, throttle status)
- ❌ `examples/error_handling.py` (exception hierarchy)
- ❌ `examples/visual_confirmation_urls.py` (URL helpers)
- ❌ Skill example files (in `skills/*/examples/`)

**Cleanup Needed**:

- ❌ Test client created during validation (ID: 123679362) still in Jobber account
- ❌ VALIDATION_REPORT.md and OAUTH_TOKEN_GUIDE.md not part of official docs

## Goals

### Primary Goals

1. **Validate All Examples**: Run every example script against live Jobber API to confirm correctness
2. **Clean Test Data**: Delete test resources created during validation
3. **Document Production Readiness**: Update CHANGELOG and prepare for first release
4. **Create Version Tag**: Use semantic-release to tag v0.1.0 or v1.0.0

### Secondary Goals

1. **Consolidate Documentation**: Move validation artifacts into official docs structure
2. **Create Deletion Script**: Reusable script for cleaning up test Jobber resources
3. **Publish to PyPI**: Make library installable via `pip install jobber-python-client`

## Non-Goals

- **Performance optimization**: Not measuring or improving API call latency
- **Rate limit testing**: Not validating throttle behavior under load
- **Multi-account testing**: Only testing with single Jobber developer account
- **Backwards compatibility**: No need to support older Jobber API versions
- **Schema migration**: Not creating tools to handle Jobber API changes

## Plan

### Phase 1: Validate Remaining Examples (30 min)

**Examples to test**:

1. `examples/basic_usage.py` - Queries, pagination, throttle status
2. `examples/error_handling.py` - Exception handling patterns
3. `examples/visual_confirmation_urls.py` - URL helper functions

**Validation criteria**:

- Script runs without errors
- Output matches expected format
- Real data returned from Jobber API
- Error handling works as documented

**Auto-fix protocol**:

- If GraphQL schema error → Fix type names based on API error message
- If authentication error → Verify Doppler tokens not expired
- If rate limit error → Wait and retry (expected behavior)
- Surface errors, fix immediately, re-run until passes

### Phase 2: Test Data Cleanup (15 min)

**Resources to delete**:

- Client ID 123679362 (Test Client - Demo Company)

**Approach**:

1. Create `delete_test_client.py` script
2. Use GraphQL mutation `clientDelete`
3. Verify deletion via query
4. Document cleanup pattern for future use

**GraphQL mutation**:

```graphql
mutation DeleteClient($id: ID!) {
  clientDelete(id: $id) {
    deletedClientId
    userErrors {
      message
      path
    }
  }
}
```

### Phase 3: Documentation Consolidation (15 min)

**Files to reorganize**:

- Move `VALIDATION_REPORT.md` → `docs/development/validation/0006-api-validation-report.md`
- Move `OAUTH_TOKEN_GUIDE.md` → `docs/guides/oauth-authentication.md`
- Update cross-references in README and CLAUDE.md

**Changelog update**:

```markdown
### Fixed

- OAuth token handling when Jobber omits `expires_in` field
- GraphQL mutation schema (ClientCreate → ClientCreateInput)

### Validated

- End-to-end OAuth authorization flow with PKCE
- GraphQL queries (list clients)
- GraphQL mutations (create client)
- Visual confirmation URLs (clickable iTerm2 links)
```

### Phase 4: Semantic Release (10 min)

**Steps**:

1. Commit all fixes with conventional commit messages
2. Run semantic-release to analyze commits
3. Generate version tag (likely v0.1.0)
4. Update CHANGELOG.md automatically
5. Create GitHub release with notes

**Expected version**: v0.1.0 (initial release, not production-ready enough for v1.0.0)

### Phase 5: PyPI Publication (Optional, 10 min)

**Prerequisites**:

- Semantic release tag created
- Build passes (`uv build`)
- PyPI token in Doppler

**Command**:

```bash
UV_PUBLISH_TOKEN=$(doppler secrets get PYPI_TOKEN --project claude-config --config prd --plain) uv publish
```

**Validation**:

```bash
pip install jobber-python-client
python -c "from jobber import JobberClient; print('✅ Package installed')"
```

## Task List

### Phase 1: Validate Examples

- [x] Create ADR-0006 documenting production readiness
- [x] Create this plan document
- [x] Run `examples/basic_usage.py` against live API
- [x] Run `examples/error_handling.py` against live API
- [x] Run `examples/visual_confirmation_urls.py` against live API
- [x] Fix any discovered issues (OAuth expires_in, GraphQL schema)
- [x] Document validation results (completion summary created)

### Phase 2: Cleanup

- [x] Create `delete_test_clients.py` script (lists for manual deletion)
- [x] Discovered API limitation: Jobber does not support clientDelete mutation
- [ ] Delete test clients manually via Jobber web UI (user action required)
- [x] Document cleanup pattern and API limitation

### Phase 3: Documentation

- [ ] Move VALIDATION_REPORT.md to docs/development/validation/
- [ ] Move OAUTH_TOKEN_GUIDE.md to docs/guides/
- [x] Update CHANGELOG.md with fixes
- [ ] Update README.md cross-references
- [ ] Update CLAUDE.md skill references

### Phase 4: Release

- [x] Commit fixes with conventional commits
- [x] Create version tag locally (v0.1.0)
- [ ] Create GitHub repository
- [ ] Push code and tags to GitHub
- [ ] Run semantic-release for GitHub release
- [ ] Verify CHANGELOG.md updated by semantic-release

### Phase 5: Publication

- [ ] Verify PyPI token in Doppler
- [ ] Run `uv build` and verify no errors
- [ ] Run `uv publish` with token from Doppler
- [ ] Verify package installable from PyPI
- [ ] Test installation in fresh virtualenv

## Success Criteria

### Must Have

- ✅ All example scripts run successfully against live Jobber API
- ✅ Test data cleaned up (no orphaned resources)
- ✅ CHANGELOG.md updated with fixes and validation
- ✅ Semantic version tag created (v0.1.0)
- ✅ GitHub release published

### Should Have

- ✅ Documentation consolidated into docs/ structure
- ✅ Delete script available for future cleanup
- ✅ Cross-references updated across all docs

### Nice to Have

- ✅ Package published to PyPI
- ✅ Installation validated from PyPI
- ✅ README badges updated (version, PyPI, license)

## Risks and Mitigations

### Risk: Token Expiration During Validation

**Likelihood**: Medium (tokens expire in 60 min)
**Impact**: High (validation fails mid-run)

**Mitigation**:

- Run validation in single session (< 60 min)
- Monitor token expiration timestamp
- Re-run `jobber_auth.py` if expired

### Risk: Rate Limiting

**Likelihood**: Low (validation uses <10 queries)
**Impact**: Medium (temporary delays)

**Mitigation**:

- Respect throttle status in responses
- Wait if rate limit threshold exceeded
- Not a blocker (library handles this correctly)

### Risk: Schema Changes During Validation

**Likelihood**: Very Low (Jobber API stable)
**Impact**: High (validation fails)

**Mitigation**:

- Fix type names based on API error messages
- Document actual types discovered
- Not preventable, only reactive

### Risk: Test Client Not Deletable

**Likelihood**: Low (API supports delete)
**Impact**: Low (orphaned test data)

**Mitigation**:

- Manual deletion via Jobber web UI if script fails
- Document workaround in troubleshooting guide
- Not a release blocker

## Open Questions

1. **Version number**: Should first release be v0.1.0 (beta) or v1.0.0 (stable)?
   - **Decision**: v0.1.0 (needs more production usage before v1.0.0)

2. **PyPI publication**: Publish now or wait for more testing?
   - **Decision**: Publish after validation passes (low risk, easy to yank if issues)

3. **Test client cleanup**: Required before release or optional?
   - **Decision**: Required (don't leave test data in production systems)

4. **Skill example validation**: Test all skill examples or just top-level examples/?
   - **Decision**: Top-level only (skills validated during creation)

## Timeline

- **Phase 1** (Validate Examples): 30 minutes
- **Phase 2** (Cleanup): 15 minutes
- **Phase 3** (Documentation): 15 minutes
- **Phase 4** (Release): 10 minutes
- **Phase 5** (PyPI): 10 minutes

**Total**: 80 minutes (1.3 hours)

## SLOs

- **Availability**: 99.9% - Production-ready OAuth flow and API calls
- **Correctness**: 100% - All examples produce correct results against real API
- **Observability**: All errors surfaced immediately with context
- **Maintainability**: Documentation consolidated, versioned, and cross-referenced

## Dependencies

- **Jobber API**: Live access required for validation
- **Doppler**: Tokens must be valid (not expired)
- **OAuth App**: Developer account and app credentials
- **GitHub**: Repository access for semantic-release
- **PyPI**: Token for publication (optional)

## Appendix: Conventional Commit Messages

```bash
# For OAuth fix
git add jobber_auth.py
git commit -m "fix: handle missing expires_in field in Jobber OAuth response

Jobber's OAuth token endpoint omits the expires_in field.
Default to 3600 seconds (1 hour) to match documented token lifetime.

Fixes authentication failures during OAuth flow."

# For GraphQL fix
git add test_create_client_url.py
git commit -m "fix: correct GraphQL mutation type ClientCreate to ClientCreateInput

Jobber GraphQL API uses ClientCreateInput, not ClientCreate.
API error message suggested the correct type name.

Fixes client creation mutations."

# For validation
git add examples/ docs/
git commit -m "docs: validate all examples against live Jobber API

- Ran examples/basic_usage.py
- Ran examples/error_handling.py
- Ran examples/visual_confirmation_urls.py

All examples produce correct results with real Jobber data."
```

## Appendix: Validation Log Format

```markdown
# Validation Report: [Script Name]

**Date**: 2025-11-22
**Script**: examples/basic_usage.py
**Jobber Account**: usalchemist@gmail.com

## Test Results

### Test 1: [Description]

- **Expected**: [What should happen]
- **Actual**: [What happened]
- **Status**: ✅ Pass / ❌ Fail

### Test 2: [Description]

...

## Issues Found

- Issue 1: [Description and fix]
- Issue 2: [Description and fix]

## Conclusion

✅ All tests passed / ❌ Fixes required
```
