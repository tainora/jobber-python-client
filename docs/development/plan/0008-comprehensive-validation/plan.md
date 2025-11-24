# Plan: Comprehensive Validation Strategy

**Metadata**:

- **ADR ID**: 0008
- **Plan ID**: 0008-comprehensive-validation
- **Status**: In Progress
- **Created**: 2025-11-22
- **Owner**: terry-li
- **Related Plans**: 0006 (Production Readiness), 0007 (AI Agent Enhancements)

---

## Context

### Background

v0.2.0 released with manual validation approach (ADR-0006) but post-release audit revealed significant automated validation gaps. Six specialized agents investigated different validation perspectives and identified:

**Test Coverage Gaps**:

- 37.5% module coverage (3/8 modules tested)
- 5 critical modules untested: `auth.py` (355 LOC), `graphql.py` (189 LOC), `photos.py` (257 LOC), `introspection.py` (288 LOC), `client.py` (136 LOC)
- Zero integration tests (42 unit tests, all isolated)
- Zero automated example validation (6 examples, manual testing only)

**Code Quality Issues**:

- 2 ruff F541 errors (f-strings without placeholders in `url_helpers.py`)
- 35/40 files need `ruff format` (87.5% unformatted)
- 26 I001 errors (unsorted imports)
- CHANGELOG.md false claim: "Linting clean (ruff 0 errors)"

**Documentation Accuracy Issues**:

- CLAUDE.md outdated stats: claims 867 LOC (actually 1,721 LOC), 2 examples (actually 6), 4 modules (actually 9)
- Incomplete test reporting: mentions 16 webhook tests, omits 42 total tests
- Unvalidated performance claims: "70% → 90% autonomy", "real-time vs 5-minute polling"

### Motivation

**Risk Drivers**:

1. **Authentication Risk** - `auth.py` handles OAuth token lifecycle (proactive/reactive refresh, Doppler integration) with zero automated tests
2. **S3 Integration Risk** - `photos.py` crosses 3 external systems (Doppler → AWS S3 → Jobber API) with zero automated tests, blocks 20% autonomy improvement
3. **API Client Risk** - `graphql.py` handles rate limiting and error parsing without automated validation
4. **Regression Risk** - No automated safety net for future changes (manual validation doesn't scale)
5. **Documentation Credibility** - False claims undermine release quality perception

**Business Impact**:

- AI agent production deployment blocked pending comprehensive validation
- Roof cleaning business automation (target: 95% autonomy) requires validated photo upload workflow
- Open-source credibility depends on accurate documentation and testing

### Current State

**Test Infrastructure**:

- pytest configured with strict type checking (`disallow_untyped_defs = true`)
- 3 existing test files: `test_exceptions.py` (7 tests), `test_url_helpers.py` (19 tests), `test_webhooks.py` (16 tests)
- Test quality: GOOD to EXCELLENT (comprehensive edge case + error path coverage)
- No pytest-cov installed (coverage measurement unavailable)
- No integration test markers configured

**Code Quality Tooling**:

- ruff configured with E,F,I,N,W,UP rules (line length 100, target Python 3.12+)
- mypy strict mode enabled (0 errors across 9 modules)
- No pre-commit hooks (local-first philosophy, manual quality checks)

**Example Scripts**:

- 6 examples exist: `basic_usage.py`, `error_handling.py`, `visual_confirmation_urls.py`, `webhook_handler.py`, `photo_upload_workflow.py`, `schema_introspection.py`
- 2 validated against live API (documented in ADR-0006)
- 4 unvalidated (v0.2.0 additions)
- No syntax or import validation automation

### Success Criteria

**Test Coverage**:

- ✅ 100% module coverage (9/9 modules have unit tests)
- ✅ 80%+ code coverage (measured with pytest-cov)
- ✅ All critical workflows have integration tests (OAuth, token refresh, GraphQL, S3, webhooks, schema)
- ✅ Examples pass automated syntax + import validation

**Code Quality**:

- ✅ 0 ruff errors (`ruff check` exit code 0)
- ✅ 0 mypy errors (`mypy jobber/` exit code 0)
- ✅ Consistent formatting (`ruff format --check` exit code 0)
- ✅ Clean git diff (formatted code committed)

**Documentation Accuracy**:

- ✅ CLAUDE.md stats match reality (LOC, module count, example count, test count)
- ✅ CHANGELOG.md quality claims backed by evidence
- ✅ No false or unvalidated claims
- ✅ Validation checklist documented for future releases

**Production Readiness**:

- ✅ All tests passing (unit + integration)
- ✅ Coverage report generated and reviewed
- ✅ Examples validated against live API
- ✅ Ready for v0.2.1 release via semantic-release

---

## Goals

### Primary Goals

1. **Achieve 100% Module Test Coverage** - Add unit tests for 5 untested modules with 80%+ code coverage
2. **Establish Integration Testing** - Create pytest integration test infrastructure with markers for external dependencies
3. **Automate Example Validation** - Prevent syntax/import errors in user-facing code
4. **Fix Code Quality Issues** - Apply ruff auto-fixes and consistent formatting
5. **Correct Documentation** - Update stats and remove false claims

### Secondary Goals

1. **Generate Coverage Report** - Measure and document actual test coverage
2. **Create Validation Workflow** - Document quality gates for future releases
3. **Maintain Test Quality** - Follow existing patterns from `test_webhooks.py`, `test_url_helpers.py`

---

## Non-Goals

1. **Performance Testing** - No load testing, latency benchmarks, or throughput measurements (out of scope per SLO focus)
2. **Security Testing** - No penetration testing, vulnerability scanning beyond existing HMAC validation (handled separately)
3. **E2E UI Testing** - No browser automation or visual regression testing (API client library, no UI)
4. **CI/CD Integration** - No GitHub Actions test execution (local-first philosophy per `~/.claude/CLAUDE.md`)
5. **Backward Compatibility** - No legacy code support or deprecation handling (greenfield project)

---

## Plan

### Phase 1: Code Quality Auto-Fix (5 minutes)

**Objective**: Resolve all automated code quality issues

**Steps**:

1. Run `ruff check --fix jobber/ examples/ tests/` (fix F541, I001, F401 errors)
2. Run `ruff format .` (format 35/40 files)
3. Verify quality: `mypy jobber/`, `ruff check jobber/`, `pytest -v`
4. Commit changes: `git add . && git commit -m "fix: apply ruff auto-fixes and consistent formatting"`

**Expected Output**:

- 0 ruff errors
- 40/40 files formatted
- All existing tests still passing (42/42)

**Validation**: `ruff check jobber/ && ruff format --check . && pytest -v`

---

### Phase 2: Unit Tests for Untested Modules (2-3 hours)

**Objective**: Achieve 100% module coverage with comprehensive unit tests

#### Phase 2.1: `tests/test_auth.py` (45 minutes)

**Test Coverage**:

- `TokenManager.__init__()` - Client initialization
- `TokenManager.load_tokens_from_doppler()` - Success, missing secrets (ConfigurationError), invalid JSON
- `TokenManager.save_tokens_to_doppler()` - Success, subprocess failure (JobberException)
- `TokenManager._start_proactive_refresh()` - Timer creation, refresh triggered before expiration
- `TokenManager._proactive_refresh_worker()` - Successful refresh, API failure, token update, timer rescheduled
- `TokenManager.get_valid_token()` - Fresh token (no refresh), expired token (reactive refresh), 401 retry
- `TokenManager._stop_proactive_refresh()` - Timer cancellation
- Thread safety - Concurrent `get_valid_token()` calls

**Mocking Strategy**:

- Mock `subprocess.run` for Doppler CLI calls
- Mock `time.time()` for expiration simulation
- Mock `requests.post` for OAuth token refresh
- Mock `threading.Timer` for proactive refresh

**Target**: 15-20 tests

#### Phase 2.2: `tests/test_graphql.py` (30 minutes)

**Test Coverage**:

- `GraphQLExecutor.__init__()` - Initialization with token manager
- `GraphQLExecutor.execute()` - Successful query, variables support, HTTP errors (401, 500, timeout)
- `GraphQLExecutor._check_throttle_status()` - Under threshold (OK), at threshold (warning), over threshold (RateLimitError)
- Throttle status parsing - Valid response, missing throttle data, malformed data
- Error response handling - GraphQL errors, network errors, AuthenticationError on 401
- Request formatting - Headers (Authorization, X-Jobber-GraphQL-Version), payload structure

**Mocking Strategy**:

- Mock `requests.post` for HTTP calls
- Mock throttle status responses (various point levels)
- Mock error responses (401, 500, timeout)

**Target**: 10-12 tests

#### Phase 2.3: `tests/test_photos.py` (45 minutes)

**Test Coverage**:

- `get_s3_credentials_from_doppler()` - Success, missing AWS_ACCESS_KEY_ID, missing AWS_SECRET_ACCESS_KEY, subprocess failure
- `generate_presigned_upload_url()` - Success with credentials, success with Doppler, invalid bucket, ClientError, BotoCoreError, expiration parameter
- `attach_photos_to_visit()` - Single photo, multiple photos, empty list, GraphQL mutation failure
- `format_photo_urls_markdown()` - Single URL, multiple URLs, empty list, URL extraction

**Mocking Strategy**:

- Mock `subprocess.run` for Doppler CLI
- Mock `boto3.client` for S3 operations
- Mock `s3_client.generate_presigned_url` for URL generation
- Mock JobberClient for `attach_photos_to_visit()`

**Target**: 12-15 tests

#### Phase 2.4: `tests/test_introspection.py` (30 minutes)

**Test Coverage**:

- `get_schema()` - Cache hit (use_cache=True), cache miss (fetch + save), cache corruption (JSONDecodeError), no cache (use_cache=False)
- `extract_field_descriptions()` - Valid type with fields, missing type (KeyError), type with no fields, fields without descriptions
- `compare_schemas()` - Added fields, removed fields, modified fields, no changes
- `clear_schema_cache()` - Cache exists (deleted), cache doesn't exist (no error)
- Cache path handling - Directory creation, file permissions

**Mocking Strategy**:

- Mock JobberClient for introspection queries
- Mock `Path.read_text()` for cache reads
- Mock `Path.write_text()` for cache writes
- Mock `Path.exists()` for cache existence checks

**Target**: 10-12 tests

#### Phase 2.5: `tests/test_client.py` (20 minutes)

**Test Coverage**:

- `JobberClient.__init__()` - Direct initialization with token manager + executor
- `JobberClient.from_doppler()` - Success, missing Doppler credentials (ConfigurationError)
- `JobberClient.execute_query()` - Successful query, AuthenticationError (propagated), RateLimitError (propagated), GraphQLError (propagated)
- Integration between TokenManager and GraphQLExecutor

**Mocking Strategy**:

- Mock TokenManager for authentication
- Mock GraphQLExecutor for query execution
- Mock exceptions for error propagation tests

**Target**: 6-8 tests

**Phase 2 Deliverables**:

- 5 new test files (50-60 tests total)
- All modules have unit test coverage
- Commit: `git commit -m "test: add comprehensive unit tests for untested modules"`

---

### Phase 3: Integration Tests (2-4 hours)

**Objective**: Create end-to-end validation for critical workflows

#### Phase 3.1: Integration Test Infrastructure (30 minutes)

**Setup**:

1. Create `tests/integration/conftest.py` with pytest markers
2. Update `pyproject.toml` with marker configuration
3. Install pytest plugins: `pytest-cov` (for coverage), optionally `pytest-timeout` (for slow tests)

**Pytest Markers**:

- `@pytest.mark.integration` - Slow tests requiring external systems
- `@pytest.mark.requires_doppler` - Tests needing Doppler CLI + secrets
- `@pytest.mark.requires_browser` - Tests needing browser for OAuth
- `@pytest.mark.requires_s3` - Tests needing AWS S3 bucket

**Running Tests**:

```bash
pytest -v -m "not integration"                    # Fast unit tests only (~1s)
pytest -v -m integration                          # Integration tests only (~2min)
pytest -v -m "integration and requires_doppler"   # Doppler-dependent tests
pytest -v                                         # All tests
```

#### Phase 3.2: OAuth Flow Integration Test (45 minutes)

**File**: `tests/integration/test_oauth_flow.py`

**Tests**:

- `test_complete_pkce_flow()` - Full OAuth flow (requires browser)
- `test_token_storage_in_doppler()` - Verify token saved correctly
- `test_token_retrieval_from_doppler()` - Verify token loaded correctly
- `test_invalid_credentials_handling()` - Test error cases

**Markers**: `@pytest.mark.integration`, `@pytest.mark.requires_doppler`, `@pytest.mark.requires_browser`

#### Phase 3.3: GraphQL Operations Integration Test (30 minutes)

**File**: `tests/integration/test_graphql_operations.py`

**Tests**:

- `test_account_query()` - Query account against live API
- `test_client_pagination()` - Cursor-based pagination
- `test_rate_limit_detection()` - Verify threshold warnings
- `test_invalid_query_error()` - Test GraphQL error handling

**Markers**: `@pytest.mark.integration`, `@pytest.mark.requires_doppler`

#### Phase 3.4: Photo Upload Integration Test (60 minutes)

**File**: `tests/integration/test_photo_upload.py`

**Tests**:

- `test_presigned_url_generation()` - Generate S3 presigned URL
- `test_photo_upload_to_s3()` - Upload test image to S3
- `test_note_attachment_to_visit()` - Attach photos to Jobber visit
- `test_complete_workflow()` - End-to-end photo upload workflow

**Markers**: `@pytest.mark.integration`, `@pytest.mark.requires_doppler`, `@pytest.mark.requires_s3`

**Test Data**: Create `tests/integration/fixtures/test-photo.jpg` (1x1 pixel image)

#### Phase 3.5: Webhook Integration Test (30 minutes)

**File**: `tests/integration/test_webhook_validation.py`

**Tests**:

- `test_flask_app_creation()` - Verify Flask app initializes
- `test_signature_validation_with_real_payload()` - Test HMAC with actual webhook payload
- `test_event_routing()` - Verify event handlers called correctly

**Markers**: `@pytest.mark.integration`

#### Phase 3.6: Schema Introspection Integration Test (20 minutes)

**File**: `tests/integration/test_schema_introspection.py`

**Tests**:

- `test_schema_fetch_from_api()` - Fetch schema from live Jobber API
- `test_cache_persistence()` - Verify schema saved to disk
- `test_field_extraction()` - Extract field descriptions from real schema
- `test_schema_comparison()` - Compare cached vs fresh schema

**Markers**: `@pytest.mark.integration`, `@pytest.mark.requires_doppler`

**Phase 3 Deliverables**:

- 6 integration test files (20-25 tests total)
- Pytest markers configured
- Integration test documentation
- Commit: `git commit -m "test: add integration tests with pytest markers"`

---

### Phase 4: Example Validation (30 minutes)

**Objective**: Automate validation of user-facing example code

#### Phase 4.1: Syntax Validation Script (10 minutes)

**File**: `scripts/validate-examples.sh`

**Functionality**:

- Iterate over all `examples/*.py` files
- Run `python3 -m py_compile` on each
- Exit with error code 1 on first failure
- Report validation status

**Usage**: `./scripts/validate-examples.sh`

#### Phase 4.2: Import Validation Tests (20 minutes)

**File**: `tests/test_examples_imports.py`

**Test Coverage**:

- `test_basic_usage_imports()` - Verify basic_usage.py imports resolve
- `test_error_handling_imports()` - Verify error_handling.py imports resolve
- `test_visual_confirmation_urls_imports()` - Verify visual_confirmation_urls.py imports resolve
- `test_webhook_handler_imports()` - Verify webhook_handler.py imports resolve (Flask dependency)
- `test_photo_upload_workflow_imports()` - Verify photo_upload_workflow.py imports resolve (boto3 dependency)
- `test_schema_introspection_imports()` - Verify schema_introspection.py imports resolve

**Test Pattern**:

```python
def test_webhook_handler_imports():
    from examples import webhook_handler
    assert hasattr(webhook_handler, 'app')  # Verify Flask app exists
    assert hasattr(webhook_handler, 'main')  # Verify main() function exists
```

**Phase 4 Deliverables**:

- `scripts/validate-examples.sh` (executable)
- `tests/test_examples_imports.py` (6 tests)
- Commit: `git commit -m "test: add example validation (syntax + imports)"`

---

### Phase 5: Documentation Updates (15 minutes)

**Objective**: Correct false claims and update stats to match reality

#### Phase 5.1: Fix CLAUDE.md Outdated Stats (5 minutes)

**File**: `/Users/terryli/own/jobber/CLAUDE.md`

**Updates**:

- Line 30: `Core library: 867 LOC (4 modules)` → `Core library: 1,721 LOC (9 modules)`
- Line 31: `Examples: 2 (basic usage, error handling)` → `Examples: 6 (basic usage, error handling, webhooks, photos, schema, visual URLs)`
- Line 32: `Tests: Unit tests with pytest` → `Tests: 90+ tests with pytest (unit + integration)`
- Lines 351-355: Update Quality Standards section with v0.2.1 validation results

#### Phase 5.2: Fix CHANGELOG.md False Claims (5 minutes)

**File**: `/Users/terryli/own/jobber/CHANGELOG.md`

**Create v0.2.1 Section**:

```markdown
## [0.2.1] - 2025-11-22

### Testing

#### Comprehensive Unit Test Coverage

- Add `tests/test_auth.py` (15+ tests for TokenManager)
- Add `tests/test_graphql.py` (10+ tests for GraphQLExecutor)
- Add `tests/test_photos.py` (12+ tests for S3 integration)
- Add `tests/test_introspection.py` (10+ tests for schema caching)
- Add `tests/test_client.py` (6+ tests for JobberClient)
- Achieve 100% module coverage (9/9 modules tested)
- Achieve 80%+ code coverage (measured with pytest-cov)

#### Integration Test Infrastructure

- Add pytest markers (@pytest.mark.integration, @pytest.mark.requires_doppler, etc.)
- Add 6 integration test files (20+ tests)
- Enable selective test execution (unit-only, integration-only, dependency-based)

#### Example Validation

- Add `scripts/validate-examples.sh` for syntax validation
- Add `tests/test_examples_imports.py` (6 import tests)
- Prevent example code regressions

### Code Quality

- Fix 2 ruff F541 errors (f-strings without placeholders)
- Fix 26 I001 errors (import sorting)
- Apply consistent formatting to 35 files (ruff format)
- Maintain mypy 0 errors (all 9 modules type-safe)

### Documentation

- Update CLAUDE.md with accurate project stats
- Fix CHANGELOG.md v0.2.0 false linting claim
- Add validation evidence section
- Create testing documentation

### Quality Assurance

- ✅ All unit tests pass (90+ tests)
- ✅ All integration tests pass (20+ tests)
- ✅ Type checking clean (mypy 0 errors)
- ✅ Linting clean (ruff 0 errors)
- ✅ Formatting consistent (ruff format applied)
- ✅ Code coverage 80%+ (pytest-cov)
- ✅ Example validation passing (syntax + imports)
```

**Update v0.2.0 Section**:

- Line 53: ~~`✅ Linting clean (ruff 0 errors)`~~ → `⚠️ Linting: 2 fixable warnings (fixed in v0.2.1)`

#### Phase 5.3: Update ADR-0007 Validation Status (5 minutes)

**File**: `/Users/terryli/own/jobber/docs/architecture/decisions/0007-ai-agent-enhancements.md`

**Add Section** (after Line 271):

```markdown
### Post-Release Validation (v0.2.1)

**Comprehensive Testing Added**:

- Unit tests: 90+ tests (100% module coverage)
- Integration tests: 20+ tests (OAuth, GraphQL, S3, webhooks, schema)
- Example validation: Automated syntax + import checks
- Code coverage: 80%+ (pytest-cov)

**Code Quality**:

- Ruff errors: 0 (auto-fixed 2 f-strings, 26 imports)
- Formatting: Consistent (ruff format applied to 35 files)
- Type safety: Maintained (mypy 0 errors)

**Documentation**:

- Corrected false claims in CHANGELOG.md v0.2.0
- Updated CLAUDE.md with accurate stats
- Added validation evidence section

**Reference**: ADR-0008 (Comprehensive Validation Strategy)
```

**Phase 5 Deliverables**:

- Updated CLAUDE.md, CHANGELOG.md, ADR-0007
- Commit: `git commit -m "docs: update validation claims and project stats"`

---

### Phase 6: Final Validation (10 minutes)

**Objective**: Verify all quality gates pass

#### Phase 6.1: Run Complete Test Suite (5 minutes)

```bash
# Unit tests (fast, no external deps)
pytest -v -m "not integration"
# Expected: 70+ tests passing in ~1s

# Integration tests (slow, requires Doppler/S3)
pytest -v -m integration
# Expected: 20+ tests passing in ~2min

# Full test suite
pytest -v
# Expected: 90+ tests passing
```

#### Phase 6.2: Quality Gates (3 minutes)

```bash
mypy jobber/                      # Expect: 0 errors
ruff check jobber/ examples/      # Expect: 0 errors
ruff format --check .             # Expect: 0 files need formatting
scripts/validate-examples.sh      # Expect: All pass
```

#### Phase 6.3: Generate Coverage Report (2 minutes)

```bash
pytest --cov=jobber --cov-report=term-missing --cov-report=html
# Expected: 80%+ coverage
# Output: htmlcov/index.html (detailed coverage report)
```

**Phase 6 Deliverables**:

- Coverage report (pytest-cov output)
- Quality gate confirmation
- Commit: `git commit -m "chore: final validation - 90+ tests, 80%+ coverage"`

---

### Phase 7: Release v0.2.1 (15 minutes)

**Objective**: Release validated version via semantic-release

#### Phase 7.1: Semantic Release (10 minutes)

**Process**:

1. Verify all commits follow conventional commit format
2. Push all commits to main branch
3. Invoke `semantic-release` skill with GH token
4. Verify GitHub release created with changelog

**Expected Version**: v0.2.1 (PATCH bump for test additions)

**Phase 7 Deliverables**:

- GitHub release: v0.2.1
- Todo: Mark complete

---

## Task List

### Phase 1: Code Quality Auto-Fix

- [x] Create ADR-0008 (MADR format)
- [x] Create plan-0008 (Google Design Doc format)
- [ ] Run `ruff check --fix` on all code
- [ ] Run `ruff format .` on all code
- [ ] Verify quality gates (mypy, ruff, pytest)
- [ ] Commit: "fix: apply ruff auto-fixes and consistent formatting"

### Phase 2: Unit Tests

- [ ] Create `tests/test_auth.py` (15-20 tests for TokenManager)
- [ ] Create `tests/test_graphql.py` (10-12 tests for GraphQLExecutor)
- [ ] Create `tests/test_photos.py` (12-15 tests for S3 integration)
- [ ] Create `tests/test_introspection.py` (10-12 tests for schema caching)
- [ ] Create `tests/test_client.py` (6-8 tests for JobberClient)
- [ ] Verify all tests pass (pytest -v)
- [ ] Commit: "test: add comprehensive unit tests for untested modules"

### Phase 3: Integration Tests

- [ ] Create `tests/integration/conftest.py` (pytest markers)
- [ ] Update `pyproject.toml` (marker configuration)
- [ ] Create `tests/integration/test_oauth_flow.py`
- [ ] Create `tests/integration/test_graphql_operations.py`
- [ ] Create `tests/integration/test_photo_upload.py`
- [ ] Create `tests/integration/test_webhook_validation.py`
- [ ] Create `tests/integration/test_schema_introspection.py`
- [ ] Verify integration tests pass (pytest -v -m integration)
- [ ] Commit: "test: add integration tests with pytest markers"

### Phase 4: Example Validation

- [ ] Create `scripts/validate-examples.sh` (syntax validation)
- [ ] Create `tests/test_examples_imports.py` (6 import tests)
- [ ] Make script executable (chmod +x)
- [ ] Verify examples pass validation
- [ ] Commit: "test: add example validation (syntax + imports)"

### Phase 5: Documentation Updates

- [ ] Update CLAUDE.md project stats (LOC, examples, tests)
- [ ] Update CHANGELOG.md with v0.2.1 section
- [ ] Fix CHANGELOG.md v0.2.0 false linting claim
- [ ] Update ADR-0007 with post-release validation
- [ ] Commit: "docs: update validation claims and project stats"

### Phase 6: Final Validation

- [ ] Run unit tests (pytest -v -m "not integration")
- [ ] Run integration tests (pytest -v -m integration)
- [ ] Run quality gates (mypy, ruff, example validation)
- [ ] Generate coverage report (pytest-cov)
- [ ] Review coverage report (target: 80%+)
- [ ] Commit: "chore: final validation - 90+ tests, 80%+ coverage"

### Phase 7: Release

- [ ] Push all commits to main branch
- [ ] Invoke semantic-release skill (create v0.2.1 tag + GitHub release)

---

## Risks & Mitigation

### Risk: Test Suite Becomes Slow

**Likelihood**: Medium
**Impact**: Medium (developer productivity)
**Mitigation**: Use pytest markers to separate fast unit tests (<1s) from slow integration tests (~2min). Default pytest run excludes integration tests.

### Risk: Mocked Dependencies Diverge from Real APIs

**Likelihood**: Medium
**Impact**: High (false confidence)
**Mitigation**: Run integration tests weekly against live API. Document expected behaviors in mock assertions.

### Risk: Integration Tests Require Manual Setup

**Likelihood**: High
**Impact**: Low (one-time cost)
**Mitigation**: Document setup steps in `tests/integration/README.md`. Provide example Doppler secrets configuration.

### Risk: Coverage Metrics Create False Confidence

**Likelihood**: Low
**Impact**: Medium (quality perception)
**Mitigation**: Combine coverage metrics (80%+) with manual validation (as in ADR-0006). Review uncovered lines for risk assessment.

### Risk: Test Maintenance Overhead

**Likelihood**: High
**Impact**: Medium (long-term cost)
**Mitigation**: Follow existing test quality patterns (see `test_webhooks.py`, `test_url_helpers.py`). Comprehensive mocking reduces brittleness.

---

## Dependencies

**External**:

- pytest-cov (for coverage measurement) - Install: `uv add --dev pytest-cov`
- Doppler CLI (for integration tests) - Already installed
- AWS S3 bucket (for photo upload integration tests) - User-configured
- GitHub CLI (for semantic-release) - Already installed

**Internal**:

- Existing test quality patterns (test_webhooks.py, test_url_helpers.py)
- ADR-0006 manual validation workflow (complement, not replace)
- ADR-0007 AI agent enhancements (features being validated)

---

## SLOs

**Correctness**:

- Target: 100% module coverage (9/9 modules tested)
- Measurement: pytest collection (verify test files for all modules)
- Success: All modules listed in pytest discovery

**Maintainability**:

- Target: 80%+ code coverage
- Measurement: `pytest --cov=jobber --cov-report=term-missing`
- Success: Coverage report shows ≥80% across all modules

**Observability**:

- Target: All test failures have actionable error messages
- Measurement: Manual review of test output
- Success: Error messages include context (expected vs actual, mock call details)

**Availability** (Test Performance):

- Target: Unit tests <10s, integration tests <2min
- Measurement: `pytest --durations=10`
- Success: 95% of unit tests complete in <1s

---

## Progress Log

**2025-11-22 00:00**: Plan created, ADR-0008 written, todo list initialized
**2025-11-22 00:05**: Phase 1 in progress - Code quality auto-fix

---

## References

- **ADR-0008**: Comprehensive Validation Strategy (this plan's ADR)
- **ADR-0006**: Production Readiness Validation (manual validation workflow)
- **ADR-0007**: AI Agent Enhancements (features being validated)
- **Test Coverage Report**: Validation investigation (2025-11-22)
- **Documentation Accuracy Report**: False claim analysis (2025-11-22)
- **pytest Documentation**: https://docs.pytest.org/en/stable/
- **pytest-cov Documentation**: https://pytest-cov.readthedocs.io/
- **Existing Test Examples**: `tests/test_webhooks.py`, `tests/test_url_helpers.py`
