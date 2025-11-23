# 7. AI Agent Enhancements for Autonomous Operations

Date: 2025-11-22

## Status

Accepted

## Context

The comprehensive Jobber API AI Readiness Report (score: 8.5/10) identified the API as highly suitable for autonomous roof cleaning business operations, with 85% workflow autonomy achievable. However, three immediate enhancements are required to reach 95%+ autonomy and enable production deployment.

### Current Capabilities

The existing `jobber-python-client` library (v0.1.1) provides:

- OAuth 2.0 PKCE authentication with Doppler token storage
- GraphQL query execution with fail-fast error handling
- Rate limit awareness via `throttleStatus` parsing
- Visual confirmation URLs (`jobberWebUri`) for human verification
- Automatic token refresh (proactive + reactive)

### Identified Gaps

Analysis of complete lead-to-payment workflow revealed three high-priority gaps:

1. **Event-Driven Automation Gap**: Library uses polling for state changes (e.g., check quote approvals every 5 minutes), causing 5-minute latency. Jobber supports webhooks for real-time events, but library lacks webhook validation.

2. **Photo Upload Gap**: Work completion phase (roof cleaning before/after photos) has 70% autonomy due to missing photo upload API. Workaround exists (S3 + note links) but not implemented.

3. **Schema Discovery Gap**: AI agents construct GraphQL queries without dynamic type validation, causing hallucination risk. GraphQL introspection is available but not utilized.

### Business Impact

**Current state**:

- Lead Capture: 100% autonomous
- Quoting: 95% autonomous
- Job Scheduling: 80% autonomous
- Work Completion: 70% autonomous ← **Blocked by photo upload**
- Invoicing: 100% autonomous
- Payment: 100% autonomous
- Follow-up: 95% autonomous

**Target state (with enhancements)**:

- Work Completion: 90% autonomous (photo workaround implemented)
- Event latency: 5 minutes → real-time (webhooks)
- Query accuracy: Improved via schema introspection

### Constraints

- Must maintain fail-fast error handling (no silent failures)
- Must preserve minimal dependency footprint
- Webhook endpoint requires HTTPS hosting (ngrok for dev, production server for prod)
- S3 bucket setup requires AWS account (~$0.05/month cost)
- Schema introspection adds one-time API call (caching required)

## Decision

Implement three enhancements as separate, composable modules:

### 1. Webhook Support (`jobber/webhooks.py`)

**Purpose**: Enable real-time event-driven automation instead of polling.

**Implementation**:

- HMAC-SHA256 signature validation (prevent spoofed events)
- Event parser (JSON → Python dataclasses)
- Example webhook handler (Flask/FastAPI)

**Rationale**: Jobber sends webhook events in real-time (`QUOTE_APPROVED`, `INVOICE_PAID`, etc.). Validating signatures ensures events are authentic. Real-time events reduce latency from 5 minutes (polling) to <1 second (webhook).

**Alternative considered**: Continue with polling strategy (rejected - 5-minute latency unacceptable for customer experience).

### 2. Photo Upload Integration (`jobber/photos.py`)

**Purpose**: Unblock roof cleaning before/after photo requirements.

**Implementation**:

- S3 presigned URL generation (boto3)
- `attach_photos_to_visit(visit_id, photo_urls)` helper (uses `noteCreate`)
- Mobile upload flow example

**Rationale**: Jobber GraphQL API does not support photo uploads. S3 workaround is industry-standard pattern (photos stored in AI-accessible location, linked via notes). Cost is negligible (~$0.05/month for 1000 photos).

**Alternative considered**: Wait for Jobber to add photo upload API (rejected - no timeline, blocks production deployment).

### 3. Schema Introspection (`jobber/introspection.py`)

**Purpose**: Improve AI query construction accuracy via dynamic type validation.

**Implementation**:

- `get_schema()` function (executes `__schema` query)
- `extract_field_descriptions(type_name)` helper
- Schema caching (avoid repeated introspection calls)

**Rationale**: GraphQL introspection provides complete schema with type names, field names, and descriptions. AI agents can validate query structure before execution, reducing hallucination risk. Caching prevents rate limit impact.

**Alternative considered**: Manual schema documentation (rejected - prone to drift as Jobber API evolves).

## Consequences

### Positive

- **Real-time automation**: Webhook events eliminate 5-minute polling latency
- **Photo workflow unblocked**: Work completion phase autonomy increases from 70% → 90%
- **Reduced hallucination**: Schema introspection provides ground truth for query construction
- **Composable design**: Each module is independent, can be adopted incrementally
- **Production-ready**: All three enhancements address blockers identified in AI readiness report

### Negative

- **Additional dependencies**: `boto3` (S3 client), optional `flask`/`fastapi` (webhook examples)
- **Infrastructure requirements**: Webhook endpoint hosting, S3 bucket setup
- **Operational complexity**: Webhook secret management, S3 bucket configuration
- **Cost increase**: S3 storage (~$0.05/month), webhook endpoint hosting (varies)

### Neutral

- **Maintenance burden**: Three new modules to maintain (estimated <200 LOC each)
- **Documentation expansion**: README, examples, skill references require updates
- **Testing surface**: Unit tests for signature validation, integration tests for webhooks/S3

## Trade-offs

**Webhook Hosting Complexity vs Real-time Automation**:

- Accept: Webhook endpoint requires HTTPS hosting (ngrok for dev, production server for prod)
- Gain: 5-minute latency → <1 second real-time events
- Mitigation: Provide deployment guide for common platforms (Heroku, Railway, Fly.io)

**S3 Setup Complexity vs Photo Upload**:

- Accept: S3 bucket setup requires AWS knowledge
- Gain: Unblocks roof cleaning photo requirements (70% → 90% autonomy)
- Mitigation: Provide setup guide with Terraform/CloudFormation templates

**Schema Caching Staleness vs Rate Limit Impact**:

- Accept: Cached schema may be stale if Jobber updates API
- Gain: Avoid rate limit impact from repeated introspection calls
- Mitigation: Schema diff utility detects changes, alerts on breaking changes

## Implementation Notes

### Module Structure

```
jobber/
├── webhooks.py       # HMAC validation, event parsing
├── photos.py         # S3 presigned URLs, note attachment
├── introspection.py  # Schema queries, field descriptions
└── ...

examples/
├── webhook_handler.py          # Flask webhook endpoint
├── photo_upload_workflow.py    # Complete photo flow
└── schema_introspection.py     # AI context usage
```

### Error Handling

All modules follow fail-fast principle:

- `webhooks.py`: Raise `SignatureValidationError` on invalid HMAC
- `photos.py`: Raise `S3UploadError` on presigned URL generation failure
- `introspection.py`: Raise `GraphQLError` on introspection query failure

### SLOs

- **Availability**: 98% (webhook endpoint must be reliable)
- **Correctness**: 100% (signature validation prevents spoofed events, S3 URLs expire after 1 hour)
- **Observability**: All webhook events logged with context, S3 uploads logged, schema cache hits/misses logged
- **Maintainability**: <200 LOC per module, comprehensive docstrings, type hints

### Dependency Management

Add to `pyproject.toml`:

```toml
dependencies = [
    "requests>=2.32.0",
    "oauthlib>=3.2.2",
    "boto3>=1.35.0",  # New: S3 presigned URLs
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "mypy>=1.14.0",
    "ruff>=0.8.0",
    "flask>=3.0.0",  # New: Webhook example
]
```

### Webhook Security

Jobber webhooks include HMAC-SHA256 signature in `X-Jobber-Signature` header:

```
X-Jobber-Signature: sha256=<hex_digest>
```

Validation algorithm:

```python
import hmac
import hashlib

def validate_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

### S3 Security

Presigned URLs expire after 1 hour (configurable):

```python
import boto3

s3_client = boto3.client('s3')
url = s3_client.generate_presigned_url(
    'put_object',
    Params={'Bucket': 'my-bucket', 'Key': 'photo.jpg'},
    ExpiresIn=3600  # 1 hour
)
```

### Schema Caching Strategy

Cache schema to disk to avoid repeated introspection:

```python
import json
from pathlib import Path

CACHE_FILE = Path.home() / '.cache' / 'jobber' / 'schema.json'

def get_schema(client, use_cache=True):
    if use_cache and CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text())

    schema = client.execute_query(INTROSPECTION_QUERY)
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(schema))
    return schema
```

## Validation Criteria

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

## Related

- **Analysis**: `docs/analysis/jobber-api-ai-readiness-report.md` (AI readiness score 8.5/10)
- **Implementation Plan**: `docs/development/plan/0007-ai-agent-enhancements/plan.md`
- **Previous ADRs**: ADR-0001 (architecture), ADR-0006 (production readiness)
- **Skill References**: `visual-confirmation-urls`, `graphql-query-execution`, `oauth-pkce-doppler`
