# ADR-0008: Comprehensive Validation Strategy

**Status**: Accepted
**Date**: 2025-11-22
**Deciders**: terry-li
**Related**: ADR-0006 (Production Readiness), ADR-0007 (AI Agent Enhancements)

## Context

Post-v0.2.0 validation audit revealed significant gaps:

**Test Coverage Analysis**:
- 42/42 unit tests passing (100% pass rate)
- 3/8 modules tested (37.5% module coverage)
- 5 critical modules untested: `auth.py`, `graphql.py`, `photos.py`, `introspection.py`, `client.py`
- 0 integration tests (only unit tests exist)
- 0 automated example validation

**Code Quality Issues**:
- 2 ruff linting errors (f-strings without placeholders)
- 35/40 files need formatting (`ruff format`)
- False claim in CHANGELOG.md: "Linting clean (ruff 0 errors)"

**Documentation Accuracy**:
- CLAUDE.md Project Stats outdated (claims 867 LOC, actually 1,721 LOC)
- Example count incorrect (claims 2, actually 6)
- Test count incomplete (reports 16 webhook tests, omits 42 total)

**Risk Assessment**:
- HIGH risk: Core authentication (`auth.py`) and API client (`graphql.py`) untested
- CRITICAL risk: Photo upload (`photos.py`) crosses 3 external systems (Doppler, S3, Jobber) with zero automated tests
- MEDIUM risk: No automated regression detection (manual validation only)

**Business Impact**:
- v0.2.0 relies on manual validation documented in ADR-0006
- AI agent autonomy claims (70% → 90%) lack empirical validation
- Production deployment risks authentication/S3 integration failures

## Decision

Implement comprehensive validation strategy across 6 phases:

1. **Code Quality Auto-Fix** - Apply ruff linting fixes and consistent formatting
2. **Unit Test Coverage** - Add tests for all 5 untested modules (target: 80%+ coverage)
3. **Integration Testing** - Create pytest integration tests with markers for external dependencies
4. **Example Validation** - Automate syntax and import validation for 6 examples
5. **Documentation Accuracy** - Correct false claims, update stats to match reality
6. **Continuous Validation** - Establish quality gates for future releases

**Approach**:
- Mock external dependencies (Doppler subprocess, boto3 S3, requests)
- Use pytest markers for integration tests (`@pytest.mark.integration`, `@pytest.mark.requires_doppler`)
- Create validation scripts (`scripts/validate-examples.sh`)
- Generate coverage reports (`pytest-cov`)
- Update documentation with evidence-based claims

## Consequences

### Positive

**Test Coverage**:
- 100% module coverage (9/9 modules tested)
- 80%+ code coverage (measured with pytest-cov)
- Automated regression detection (catch bugs before production)
- Fast unit tests (~1s) + comprehensive integration tests

**Code Quality**:
- Consistent formatting (ruff format applied to all files)
- Zero linting errors (ruff check passes)
- Maintained type safety (mypy 0 errors)
- Clean codebase for future contributors

**Documentation Accuracy**:
- Evidence-based validation claims
- Accurate project statistics
- Clear distinction between capabilities and proven outcomes
- Validation checklist for future releases

**Production Readiness**:
- Critical workflows validated (OAuth, token refresh, GraphQL, S3, webhooks, schema introspection)
- External dependency mocking prevents flaky tests
- Integration tests provide end-to-end confidence
- Example validation ensures user-facing code works

### Negative

**Implementation Effort**:
- 4-6 hours initial investment
- 90+ new tests to maintain
- Integration test infrastructure (markers, fixtures, mocks)

**Maintenance Burden**:
- Update tests when API changes
- Maintain mocks for external dependencies
- Keep documentation synchronized with code

**Trade-offs**:
- Mocked dependencies ≠ real API behavior (integration tests mitigate)
- Coverage metrics ≠ quality (manual review still required)
- Test maintenance overhead (accepted for regression protection)

### Risks & Mitigation

**Risk**: Test suite becomes slow
**Mitigation**: Separate unit tests (fast, no markers) from integration tests (slow, marked)

**Risk**: Mocks diverge from real APIs
**Mitigation**: Periodic integration test runs against live API (weekly/manual)

**Risk**: False confidence from high coverage
**Mitigation**: Combine coverage metrics with manual validation (as in ADR-0006)

**Risk**: Test maintenance overhead
**Mitigation**: Follow existing test quality patterns (see `test_webhooks.py`, `test_url_helpers.py`)

## Implementation Notes

### Test Organization

```
tests/
├── test_auth.py              # TokenManager (proactive/reactive refresh, Doppler)
├── test_client.py            # JobberClient facade
├── test_exceptions.py        # Exception hierarchy (existing)
├── test_graphql.py           # GraphQLExecutor (rate limiting, errors)
├── test_introspection.py     # Schema introspection (caching, field extraction)
├── test_photos.py            # S3 presigned URLs (boto3 mocking)
├── test_url_helpers.py       # URL formatting (existing)
├── test_webhooks.py          # Webhook validation (existing)
├── test_examples_imports.py  # Example import validation
└── integration/
    ├── conftest.py           # Pytest markers configuration
    ├── test_oauth_flow.py    # @pytest.mark.requires_browser
    ├── test_graphql_operations.py
    ├── test_photo_upload.py  # @pytest.mark.requires_s3
    ├── test_webhook_validation.py
    └── test_schema_introspection.py
```

### Quality Gates (Local Validation)

```bash
# Auto-fix formatting and linting
ruff format .
ruff check --fix .

# Run unit tests (fast, no external deps)
pytest -v -m "not integration"

# Run integration tests (slow, requires Doppler/S3)
pytest -v -m integration

# Type checking
mypy jobber/

# Example validation
scripts/validate-examples.sh

# Coverage report (target: 80%+)
pytest --cov=jobber --cov-report=term-missing
```

### Documentation Update Requirements

1. **CLAUDE.md** - Update Project Stats (LOC, example count, test count)
2. **CHANGELOG.md** - Fix false linting claim, add comprehensive test counts
3. **ADR-0007** - Update validation status with actual evidence
4. **README.md** - Add testing section with pytest markers documentation

### SLOs

**Correctness**:
- Target: 100% module test coverage (9/9)
- Actual: Measured after Phase 2
- Validation: `pytest --cov=jobber --cov-report=term-missing`

**Maintainability**:
- Target: 80%+ code coverage
- Actual: Measured after Phase 2
- Validation: Coverage report

**Observability**:
- Target: All external dependencies mocked with clear error messages
- Actual: Mock assertions fail with actionable diagnostics
- Validation: Manual review of test output

**Availability**:
- Target: Test suite runs in <10s (unit tests), <2min (integration tests)
- Actual: Measured after Phase 6
- Validation: `pytest --durations=10`

## References

- **ADR-0006**: Production Readiness Validation (manual validation approach)
- **ADR-0007**: AI Agent Enhancements (features requiring validation)
- **Test Coverage Report**: Validation investigation findings (2025-11-22)
- **Documentation Accuracy Report**: False claim analysis (2025-11-22)
- **pytest Best Practices**: https://docs.pytest.org/en/stable/
- **pytest-cov**: https://pytest-cov.readthedocs.io/

---

**Next Steps**: See `docs/development/plan/0008-comprehensive-validation/plan.md` for implementation plan.
