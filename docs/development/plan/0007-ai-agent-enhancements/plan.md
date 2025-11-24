# Plan: AI Agent Enhancements for Autonomous Operations

## Metadata

- **ADR ID**: 0007
- **ADR Link**: `../../../architecture/decisions/0007-ai-agent-enhancements.md`
- **Status**: In Progress
- **Created**: 2025-11-22
- **Updated**: 2025-11-22
- **Owner**: Terry Li

---

## Context

### Background

The comprehensive Jobber API AI Readiness Report (completed 2025-11-22) assessed the Jobber GraphQL API for autonomous roof cleaning business operations. The analysis involved 5 parallel sub-agents examining API schema, workflows, integration patterns, production constraints, and existing codebase.

**Key Findings**:

- **Overall AI-Agent Readiness Score**: 8.5/10
- **Workflow Autonomy**: 85% achievable with current implementation
- **Target Autonomy**: 95%+ achievable with strategic enhancements
- **Production Status**: Library (v0.1.1) is functional but missing three high-priority features

### Motivation

Analysis of the complete lead-to-payment workflow revealed autonomy gaps:

| Phase               | Current Autonomy | Target Autonomy | Blocker                          |
| ------------------- | ---------------- | --------------- | -------------------------------- |
| Lead Capture        | 100%             | 100%            | None                             |
| Quoting             | 95%              | 95%             | Human pricing rules (acceptable) |
| Job Scheduling      | 80%              | 80%             | Route optimization (deferred)    |
| **Work Completion** | **70%**          | **90%**         | **Photo upload missing**         |
| Invoicing           | 100%             | 100%            | None                             |
| Payment             | 100%             | 100%            | None                             |
| Follow-up           | 95%              | 95%             | Human cadence rules (acceptable) |

**Three immediate enhancements identified**:

1. **Webhook Support** (HIGH Priority)
   - **Gap**: Polling for state changes causes 5-minute latency
   - **Impact**: Real-time automation (quote approvals, invoice payments)
   - **Complexity**: MEDIUM (webhook endpoint hosting required)

2. **Photo Upload Workaround** (HIGH Priority)
   - **Gap**: No photo upload API for before/after roof photos
   - **Impact**: Unblocks Work Completion phase (70% → 90% autonomy)
   - **Complexity**: MEDIUM (S3 bucket setup required)

3. **Schema Introspection** (MEDIUM Priority)
   - **Gap**: AI agents construct queries without dynamic type validation
   - **Impact**: Reduced hallucination risk
   - **Complexity**: LOW (single introspection query + caching)

### Current State

**Implemented** (v0.1.1):

- ✅ OAuth 2.0 PKCE authentication
- ✅ GraphQL query execution
- ✅ Rate limit awareness (`throttleStatus`)
- ✅ Visual confirmation URLs (`jobberWebUri`)
- ✅ Automatic token refresh
- ✅ Fail-fast error handling

**Missing**:

- ❌ Webhook signature validation
- ❌ S3 photo upload integration
- ❌ GraphQL schema introspection

**Documentation**:

- ✅ ADR-0001 through ADR-0006
- ✅ Skills: `oauth-pkce-doppler`, `visual-confirmation-urls`, `graphql-query-execution`
- ✅ Examples: `basic_usage.py`, `error_handling.py`, `visual_confirmation_urls.py`
- ✅ AI Readiness Report: `docs/analysis/jobber-api-ai-readiness-report.md`

### Success Criteria

Implementation is complete when:

1. ✅ Webhook signature validation working (unit tests pass)
2. ✅ Webhook events parseable into Python dataclasses
3. ✅ Example webhook handler receives real Jobber events
4. ✅ Photos uploadable to S3 via presigned URLs
5. ✅ Photos linkable to visits via `noteCreate` notes
6. ✅ Schema introspection returns complete GraphQL schema
7. ✅ Field descriptions extractable for AI context
8. ✅ All examples run successfully against live API
9. ✅ Documentation updated (README, CHANGELOG, CLAUDE.md)
10. ✅ Ready for v0.2.0 release via semantic-release

---

## Goals

### Primary Goals

1. **Enable Real-time Automation**: Implement webhook signature validation and event parsing to eliminate 5-minute polling latency

2. **Unblock Photo Workflows**: Implement S3 presigned URL generation and note attachment to achieve 90% autonomy for Work Completion phase

3. **Improve Query Accuracy**: Implement GraphQL schema introspection with caching to reduce AI hallucination risk

4. **Maintain Quality Standards**: All modules follow fail-fast error handling, include type hints, have unit tests, and maintain <200 LOC

### Secondary Goals

1. **Provide Production Examples**: Create runnable examples for webhook handlers, photo uploads, and schema introspection

2. **Document Setup Requirements**: Provide detailed guides for webhook endpoint hosting and S3 bucket configuration

3. **Release v0.2.0**: Use semantic-release skill to tag version, generate changelog, create GitHub release

## Non-Goals

- **Google Routes Integration**: Deferred to Month 1 (short-term roadmap)
- **AI Pricing Model**: Deferred to Month 1 (short-term roadmap)
- **Multi-Tenant Support**: Deferred to Quarter 1 (long-term roadmap)
- **Performance Optimization**: Not measuring or improving API call latency (SLO excludes speed/perf)
- **Security Hardening**: Focus on correctness, not security (SLO excludes security)
- **Backward Compatibility**: No legacy code support needed

---

## Plan

### Phase 1: Webhook Support (2-3 hours)

**Deliverables**:

- `jobber/webhooks.py` - HMAC signature validation, event parsing
- `examples/webhook_handler.py` - Flask webhook endpoint example
- `tests/test_webhooks.py` - Unit tests for signature validation
- Updated `README.md` - Webhook setup documentation

**Implementation Steps**:

1. Create `jobber/webhooks.py` module
   - `validate_signature(payload, signature, secret)` function (HMAC-SHA256)
   - `parse_event(payload)` function (JSON → dict)
   - Event type constants (`CLIENT_CREATE`, `QUOTE_APPROVED`, etc.)

2. Create example webhook handler
   - Flask app with `/webhook` POST endpoint
   - Signature validation middleware
   - Event type routing (different handlers per event)
   - Example: `QUOTE_APPROVED` → print client notification

3. Write unit tests
   - Test signature validation (valid signature passes)
   - Test signature validation (invalid signature fails)
   - Test event parsing (valid JSON → dict)
   - Test event parsing (invalid JSON → GraphQLError)

4. Update documentation
   - README: Add "Webhook Integration" section
   - Document available webhook events
   - Document webhook secret configuration (Doppler)
   - Document ngrok setup for local development

**Auto-Validation**:

- Run `pytest tests/test_webhooks.py -v`
- Run example webhook handler locally
- Test with curl: `curl -X POST -H "X-Jobber-Signature: ..." -d '...' http://localhost:5000/webhook`

---

### Phase 2: Photo Upload Integration (3-4 hours)

**Deliverables**:

- `jobber/photos.py` - S3 presigned URL generation, note attachment
- `examples/photo_upload_workflow.py` - Complete mobile upload flow
- `tests/test_photos.py` - Unit tests for URL generation
- Updated `README.md` - S3 setup documentation

**Implementation Steps**:

1. Create `jobber/photos.py` module
   - `generate_presigned_upload_url(bucket, key, expires_in=3600)` function (boto3)
   - `attach_photos_to_visit(client, visit_id, photo_urls)` function (uses `noteCreate`)
   - Photo URL formatting helpers (markdown links for notes)

2. Create example workflow
   - Step 1: Generate presigned URL for mobile upload
   - Step 2: Upload photo to S3 (simulated with requests.put)
   - Step 3: Create note on visit with photo links
   - Step 4: Print `jobberWebUri` for verification

3. Write unit tests
   - Test presigned URL generation (valid boto3 call)
   - Test note attachment (GraphQL mutation structure)
   - Test photo URL formatting (markdown links)

4. Update documentation
   - README: Add "Photo Upload Integration" section
   - Document S3 bucket setup (CORS, permissions)
   - Document Doppler secrets (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME)
   - Provide Terraform/CloudFormation templates for S3 bucket

**Auto-Validation**:

- Run `pytest tests/test_photos.py -v`
- Run example workflow against live API (requires S3 bucket)
- Verify photo visible in Jobber visit note

---

### Phase 3: Schema Introspection (1-2 hours)

**Deliverables**:

- `jobber/introspection.py` - Schema queries, field descriptions
- `examples/schema_introspection.py` - AI context usage example
- `tests/test_introspection.py` - Unit tests for caching
- Updated `README.md` - Introspection documentation

**Implementation Steps**:

1. Create `jobber/introspection.py` module
   - `INTROSPECTION_QUERY` constant (GraphQL \_\_schema query)
   - `get_schema(client, use_cache=True)` function (execute query + cache to disk)
   - `extract_field_descriptions(schema, type_name)` function (parse schema dict)
   - `compare_schemas(old_schema, new_schema)` function (detect breaking changes)

2. Create example usage
   - Load schema (use cache if available)
   - Extract field descriptions for `Client` type
   - Print descriptions for AI context
   - Example: "Field `firstName` is a String (non-null) representing the client's first name"

3. Write unit tests
   - Test schema caching (cache hit avoids GraphQL call)
   - Test field description extraction (correct parsing)
   - Test schema comparison (detect added/removed fields)

4. Update documentation
   - README: Add "Schema Introspection" section
   - Document cache location (~/.cache/jobber/schema.json)
   - Document cache invalidation (delete file or use `use_cache=False`)
   - Document AI usage pattern (validate query before execution)

**Auto-Validation**:

- Run `pytest tests/test_introspection.py -v`
- Run example against live API (introspect once, use cache second time)
- Verify cache file created at `~/.cache/jobber/schema.json`

---

### Phase 4: Documentation & Examples (2 hours)

**Deliverables**:

- Updated `README.md` - All three features documented
- Updated `CHANGELOG.md` - v0.2.0 release notes
- Updated `CLAUDE.md` - Skill references updated
- Updated `pyproject.toml` - Add boto3 dependency

**Implementation Steps**:

1. Update README.md
   - Add "Webhook Integration" section (setup, examples, security)
   - Add "Photo Upload Integration" section (S3 setup, workflow, costs)
   - Add "Schema Introspection" section (caching, AI usage, limitations)
   - Update "Quick Start" with new features
   - Update "API Reference" with new modules

2. Update CHANGELOG.md
   - Add v0.2.0 section with release date
   - Features: webhooks, photos, introspection
   - Document breaking changes (none expected)
   - Document migration guide (none needed - additive changes)

3. Update CLAUDE.md
   - Add references to new examples
   - Update module structure diagram
   - Link to ADR-0007
   - Update "Skills & Patterns" section

4. Update pyproject.toml
   - Add `boto3>=1.35.0` to dependencies
   - Add `flask>=3.0.0` to dev dependencies (optional, for webhook example)
   - Bump version to 0.2.0 (semantic-release will do this automatically)

**Auto-Validation**:

- Run `uv sync` to verify dependencies resolve
- Run `mypy jobber/` to verify type hints
- Run `ruff check jobber/` to verify code style
- Render README.md in Markdown viewer to verify formatting

---

### Phase 5: Testing & Validation (2 hours)

**Deliverables**:

- All unit tests passing
- All examples validated against live API
- Validation log: `logs/0007-ai-agent-enhancements-20251122_<timestamp>.log`

**Implementation Steps**:

1. Run all unit tests
   - `pytest tests/ -v`
   - Fix any failures immediately
   - Achieve 100% pass rate

2. Validate examples against live API
   - `uv run examples/webhook_handler.py` (start server, test with curl)
   - `uv run examples/photo_upload_workflow.py` (requires S3 bucket)
   - `uv run examples/schema_introspection.py` (run twice to test caching)
   - Log all outputs to validation log file

3. Validate existing examples still work
   - `uv run examples/basic_usage.py`
   - `uv run examples/error_handling.py`
   - `uv run examples/visual_confirmation_urls.py`

4. Run type checking and linting
   - `mypy jobber/`
   - `ruff check jobber/`
   - `ruff format jobber/`

**Auto-Validation**:

- All tests pass (pytest exit code 0)
- All examples run without errors
- Type checking passes (mypy exit code 0)
- Linting passes (ruff exit code 0)

---

### Phase 6: Release & Publish (1 hour)

**Deliverables**:

- v0.2.0 tag on GitHub
- v0.2.0 GitHub release with changelog

**Implementation Steps**:

1. Commit all changes with conventional commits
   - `git add .`
   - `git commit -m "feat(webhooks): add HMAC signature validation for Jobber events"`
   - `git commit -m "feat(photos): add S3 presigned URL helpers for photo uploads"`
   - `git commit -m "feat(introspection): add GraphQL schema introspection utility"`
   - `git commit -m "docs: update README with webhook, photo, introspection examples"`

2. Run semantic-release skill
   - Skill will analyze commits
   - Generate changelog entry for v0.2.0
   - Create git tag v0.2.0
   - Create GitHub release
   - Push to remote

**Auto-Validation**:

- Verify tag created: `git tag -l v0.2.0`
- Verify GitHub release exists: `gh release view v0.2.0`

---

## Task List

### Phase 1: Webhook Support

- [ ] Create `jobber/webhooks.py` with HMAC validation function
- [ ] Create `jobber/webhooks.py` with event parsing function
- [ ] Create `jobber/webhooks.py` with event type constants
- [ ] Create `examples/webhook_handler.py` Flask example
- [ ] Create `tests/test_webhooks.py` with signature tests
- [ ] Update README.md with webhook documentation

### Phase 2: Photo Upload

- [ ] Create `jobber/photos.py` with presigned URL function
- [ ] Create `jobber/photos.py` with attach photos function
- [ ] Create `examples/photo_upload_workflow.py` complete flow
- [ ] Create `tests/test_photos.py` with unit tests
- [ ] Update README.md with S3 setup guide

### Phase 3: Schema Introspection

- [ ] Create `jobber/introspection.py` with introspection query
- [ ] Create `jobber/introspection.py` with caching logic
- [ ] Create `jobber/introspection.py` with field description extraction
- [ ] Create `examples/schema_introspection.py` AI usage example
- [ ] Create `tests/test_introspection.py` with cache tests
- [ ] Update README.md with introspection documentation

### Phase 4: Documentation

- [ ] Update README.md with all three features
- [ ] Update CHANGELOG.md with v0.2.0 notes
- [ ] Update CLAUDE.md with skill references
- [ ] Update pyproject.toml with boto3 dependency

### Phase 5: Testing

- [ ] Run pytest on all modules (achieve 100% pass)
- [ ] Validate webhook_handler.py against curl test
- [ ] Validate photo_upload_workflow.py against live API + S3
- [ ] Validate schema_introspection.py against live API (cache test)
- [ ] Validate all existing examples still work
- [ ] Run mypy type checking (0 errors)
- [ ] Run ruff linting (0 errors)
- [ ] Create validation log file

### Phase 6: Release

- [ ] Commit changes with conventional commit messages
- [ ] Run semantic-release skill (tag v0.2.0)
- [ ] Verify GitHub release created

---

## Risks & Mitigation

### Risk 1: Webhook Endpoint Hosting (MEDIUM Impact)

**Issue**: Webhooks require HTTPS endpoint accessible by Jobber. Local development requires ngrok, production requires hosting.

**Mitigation**:

- Provide ngrok setup guide for local development
- Provide deployment guides for common platforms (Heroku, Railway, Fly.io)
- Document webhook URL configuration in Jobber Developer Portal

**Contingency**: If webhook hosting too complex, continue with polling strategy (5-minute latency acceptable for MVP).

---

### Risk 2: S3 Bucket Setup Complexity (MEDIUM Impact)

**Issue**: S3 bucket setup requires AWS account, CORS configuration, IAM permissions.

**Mitigation**:

- Provide step-by-step S3 setup guide
- Provide Terraform template for one-command setup
- Provide CloudFormation template as alternative

**Contingency**: If S3 too complex, skip photo upload (Work Completion stays at 70% autonomy).

---

### Risk 3: Schema Changes Breaking Queries (LOW Impact)

**Issue**: Jobber may update GraphQL schema without notice, breaking existing queries.

**Mitigation**:

- Implement schema diff utility to detect changes
- Cache schema with timestamp, alert if >30 days old
- Recommend periodic schema refresh (weekly)

**Contingency**: If schema changes frequently, implement automatic schema refresh on GraphQL errors.

---

### Risk 4: Dependency Version Conflicts (LOW Impact)

**Issue**: Adding boto3 may conflict with existing dependencies.

**Mitigation**:

- Use version ranges in pyproject.toml (e.g., `boto3>=1.35.0`)
- Test dependency resolution with `uv sync`
- Pin versions if conflicts arise

**Contingency**: If boto3 conflicts, vendor minimal S3 client code (avoid full boto3 dependency).

---

## SLOs

Following global SLO standards (availability, correctness, observability, maintainability):

### Availability

- **Target**: 98% uptime for webhook endpoint
- **Measurement**: Webhook endpoint responds to health checks
- **Rationale**: Webhooks are critical path for real-time automation

### Correctness

- **Target**: 100% signature validation accuracy
- **Measurement**: No false positives (valid events rejected) or false negatives (invalid events accepted)
- **Rationale**: Spoofed webhook events could trigger incorrect business logic

### Observability

- **Target**: All webhook events logged with context (event type, timestamp, payload size)
- **Measurement**: Log entries include structured data for debugging
- **Rationale**: Debugging webhook issues requires visibility into event flow

### Maintainability

- **Target**: <200 LOC per module (webhooks.py, photos.py, introspection.py)
- **Measurement**: Count lines with `wc -l jobber/*.py`
- **Rationale**: Small modules are easier to understand, test, and modify

---

## Dependencies

### Python Libraries

- `boto3>=1.35.0` - S3 presigned URL generation (new dependency)
- `flask>=3.0.0` - Webhook example endpoint (optional dev dependency)
- Existing: `requests>=2.32.0`, `oauthlib>=3.2.2`

### External Services

- **AWS S3**: Bucket for photo storage (~$0.05/month for 1000 photos)
- **Webhook Endpoint**: HTTPS server to receive Jobber events (ngrok for dev, hosting for prod)

### Jobber Configuration

- **Webhook URL**: Configured in Jobber Developer Portal
- **Webhook Secret**: Stored in Doppler (`JOBBER_WEBHOOK_SECRET`)
- **S3 Credentials**: Stored in Doppler (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME`)

---

## Progress Log

### 2025-11-22 14:00 - Plan Created

- Created ADR-0007 (MADR format)
- Created plan-0007 (Google Design Doc format)
- Created initial todo list (10 items)
- Ready to start Phase 1 implementation

---

## Related Documents

- **ADR**: `docs/architecture/decisions/0007-ai-agent-enhancements.md`
- **Analysis Report**: `docs/analysis/jobber-api-ai-readiness-report.md`
- **Previous Plan**: `docs/development/plan/0006-production-readiness-validation/plan.md`
- **Skills**: `~/.claude/skills/oauth-pkce-doppler/`, `~/.claude/skills/semantic-release/`
