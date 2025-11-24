# 10. Claude Code CLI Automation Enhancements

Date: 2025-11-23

## Status

Accepted

## Context

The jobber-python-client library (v0.2.1) has achieved 90% automation readiness for Claude Code CLI workflows. All high-priority features from ADR-0007 (webhooks, photo uploads, schema introspection) have been implemented and validated. However, comprehensive analysis revealed three areas requiring enhancement to enable full autonomous control of Jobber accounts via Claude Code CLI:

### Current State Analysis

**Automation Readiness**: 90% (up from 85% pre-v0.2.0)

**Implemented Capabilities**:
- OAuth 2.0 PKCE authentication with automatic token refresh
- GraphQL query execution with fail-fast error handling
- Real-time webhook event processing (HMAC-SHA256 validation)
- Photo upload workflow (S3 presigned URLs + note linking)
- Schema introspection for AI query validation
- Visual confirmation URLs for instant verification

**Remaining Gaps**:

1. **Inconsistent Tool References**: Example files reference `pip install` instead of project-standard `uv pip install`, violating uv-first philosophy documented in global CLAUDE.md
2. **Scattered Doppler Secrets**: Jobber secrets currently in `claude-config/prd` project, mixed with unrelated secrets (PYPI_TOKEN, CRATES_IO_CLAUDE_CODE). No dedicated Doppler project for Jobber automation
3. **Cloud Storage Uncertainty**: Photo upload implementation assumes AWS S3, but user has no AWS credentials in Doppler. Alternative cloud storage options (Cloudflare R2, Google Cloud Storage, Oracle Cloud) not evaluated
4. **Missing E2E Examples**: No end-to-end workflow examples showing how to orchestrate complete business processes (Lead → Client → Quote → Job → Invoice → Payment). AI agents have atomic capabilities but lack workflow integration patterns

### Business Impact

**Current Workflow Autonomy** (from ADR-0007):
- Lead Capture: 100%
- Quoting: 95%
- Job Scheduling: 80%
- Work Completion: 90% (photo upload enabled)
- Invoicing: 100%
- Payment: 100%
- Follow-up: 95%

**Target with Enhancements**: 95% overall (from 90%)

**Key Blocker**: AI agents can execute individual API calls but lack guidance on orchestrating multi-step workflows autonomously.

### Constraints

- Must maintain fail-fast error handling (no silent failures)
- Must preserve minimal dependency footprint
- Must follow doc-as-code workflow (ADR ↔ plan ↔ code in sync)
- Cloud storage must support presigned URLs for mobile photo uploads
- Doppler structure must support dev/prd environment separation
- Examples must integrate with Claude Code Skills architecture

## Decision

Implement four targeted enhancements to enable full Claude Code CLI automation:

### 1. Tool Reference Consistency

**Decision**: Update all example files to use `uv pip install` instead of `pip install`.

**Affected Files**:
- `examples/photo_upload_workflow.py:15` - boto3 installation
- `examples/webhook_handler.py:12` - Flask installation

**Rationale**: Aligns with project's uv-first philosophy documented in `~/.claude/CLAUDE.md`: "**Python**: `uv` (management), `uv run scriptname.py` (execution), 3.12+ - **Avoid**: pip, conda, setuptools, poetry"

**Impact**: Low (cosmetic change, 2 lines)

### 2. Dedicated Doppler Project Structure

**Decision**: Create dedicated "jobber" Doppler project with dual-config (dev/prd) structure.

**Structure**:
```
Project: jobber
├── Config: dev (sandbox Jobber account)
│   ├── JOBBER_CLIENT_ID
│   ├── JOBBER_CLIENT_SECRET
│   ├── JOBBER_ACCESS_TOKEN (managed by library)
│   ├── JOBBER_REFRESH_TOKEN (managed by library)
│   ├── JOBBER_TOKEN_EXPIRES_AT (managed by library)
│   ├── CLOUD_STORAGE_ACCESS_KEY_ID
│   ├── CLOUD_STORAGE_SECRET_ACCESS_KEY
│   ├── CLOUD_STORAGE_BUCKET_NAME
│   ├── CLOUD_STORAGE_ENDPOINT_URL (optional, for R2)
│   └── WEBHOOK_SECRET
└── Config: prd (production Jobber account)
    └── [same structure, production values]
```

**Rationale**:
- **Separation of concerns**: Jobber secrets isolated from unrelated automation (PYPI_TOKEN, CRATES_IO)
- **Environment isolation**: Dev/prd separation prevents accidental production modifications
- **Scalability**: Supports future multi-tenant or franchise expansion
- **Standard practice**: Matches typical deployment patterns (dev/staging/prod)

**Migration Path**:
1. Create new "jobber" project in Doppler
2. Copy existing secrets from `claude-config/prd` to `jobber/prd`
3. Update code to reference `--project jobber --config prd`
4. Validate token refresh still works
5. Remove secrets from `claude-config/prd` (cleanup)

**Impact**: Medium (one-time migration, affects `jobber/auth.py` Doppler CLI calls)

### 3. Cloud Storage Evaluation and Decision

**Decision**: Use Cloudflare R2 for photo uploads (winner after comparative analysis).

**Evaluated Options**:

| Platform | Free Tier | Egress Cost | S3 Compatible | Migration Effort |
|----------|-----------|-------------|---------------|------------------|
| **Cloudflare R2** | 10GB/month | **$0 (forever)** | Full (boto3) | 5 minutes |
| AWS S3 | 5GB (12 months) | $0.12-0.20/GB | Native | Already setup |
| Oracle Cloud | 20GB (always) | $0.0085/GB | Full (boto3) | 30 minutes |
| Google Cloud | 5GB (US only) | $0.12-0.20/GB | Partial | 2-4 hours |

**Rationale for R2**:
1. **Zero egress fees**: Eliminates future cost concerns at scale (serving 1000s of photos = $0 vs $12-20/month on GCP/AWS)
2. **Full S3 compatibility**: Existing boto3 code works with just endpoint change (5-minute migration vs 2-4 hour GCP rewrite)
3. **Lowest storage cost**: $0.015/GB-month (vs $0.020 AWS, $0.0255 Oracle)
4. **Future-proof**: Cost-effective at any scale (0-100,000 photos)

**Migration from S3** (if needed):
```python
# Old (AWS S3)
s3_client = boto3.client('s3')

# New (Cloudflare R2) - just add endpoint
s3_client = boto3.client(
    's3',
    endpoint_url=os.getenv('CLOUD_STORAGE_ENDPOINT_URL'),
    aws_access_key_id=os.getenv('CLOUD_STORAGE_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('CLOUD_STORAGE_SECRET_ACCESS_KEY')
)
```

**Alternative Considered**: Keep AWS S3 (rejected - user confirmed no AWS credentials in Doppler, egress costs prohibitive at scale)

**Impact**: Low (5-minute code change, backward compatible via environment variables)

### 4. End-to-End Workflow Examples

**Decision**: Create runnable E2E workflow examples integrated with Claude Code Skills architecture.

**Pattern**: Hybrid approach (runnable Python scripts + AI orchestration comments)

**First Example**: Lead Capture → Client Creation

**Structure**:
```python
# /// script
# dependencies = ["jobber-python-client"]
# ///

"""
Lead → Client Creation Workflow

AI Agent Orchestration Pattern:
1. Receive lead data (webhook, form, email)
2. Validate required fields (name, contact)
3. Create Jobber client via GraphQL mutation
4. Return visual confirmation URL
5. Handle errors with fail-fast pattern

Skills Referenced:
- graphql-query-execution: Construct clientCreate mutation
- visual-confirmation-urls: Include jobberWebUri field
- oauth-pkce-doppler: Automatic token management
"""

# Implementation follows...
```

**Rationale**:
- **Runnable**: Works as standalone script (`uv run examples/e2e_lead_to_client.py`)
- **AI-learnable**: Comments teach AI agents decision points and skill integration
- **Progressive disclosure**: References atomic skills for deeper patterns
- **Validation**: Can be executed to verify end-to-end functionality

**Skills Integration**:
- Examples reference existing atomic skills (oauth-pkce-doppler, visual-confirmation-urls, graphql-query-execution)
- No new skills created initially (validate example value first)
- Future: Extract patterns into atomic skills if examples prove valuable

**Impact**: High (enables AI agents to learn complete workflows, not just atomic operations)

## Consequences

### Positive

- **Improved Consistency**: All examples follow uv-first philosophy
- **Better Organization**: Dedicated Doppler project simplifies secret management
- **Cost Optimization**: Zero egress fees with R2 eliminate future cost concerns
- **Enhanced AI Learning**: E2E examples teach workflow orchestration patterns
- **Future-Proof**: R2 scales cost-effectively, Doppler structure supports multi-tenant

### Negative

- **Migration Effort**: One-time Doppler project creation and secret migration
- **Cloud Lock-in**: Choosing R2 creates dependency on Cloudflare (mitigated by S3 compatibility - can switch back to AWS with 5-minute endpoint change)
- **Documentation Burden**: Each enhancement requires ADR + plan + validation

### Neutral

- **No Breaking Changes**: All enhancements are additive or cosmetic
- **Backward Compatible**: Environment variables allow gradual migration
- **Optional Adoption**: Users can continue with existing AWS S3 if preferred

## Implementation Timeline

**Phase 1: Foundation** (2-3 hours)
1. Update example files (15 min)
2. Create Doppler project structure (30 min)
3. Document cloud storage decision (15 min)
4. Validate changes (30 min)

**Phase 2: E2E Examples** (8-12 hours)
1. Create lead capture example (3-4 hours)
2. Validate against live API (1 hour)
3. Document AI orchestration patterns (2 hours)
4. Create additional examples if time permits (4-6 hours)

**Phase 3: Documentation** (2-3 hours)
1. Create ADR-0010 (this document)
2. Create plan-0010
3. Update CLAUDE.md with skill navigation
4. Validate documentation accuracy

**Total**: 12-18 hours

## Future Considerations

If E2E examples prove valuable:

1. **Extract Atomic Skills**: Create `jobber-lead-capture` skill following Claude Code Skills architecture
2. **Expand Workflow Coverage**: Add Quote → Job, Invoice → Payment workflows
3. **MCP Server Integration**: Expose Jobber API as Model Context Protocol tools for conversational access
4. **Google Routes API**: Optimize job scheduling (80% → 95% autonomy)

## References

- ADR-0007: AI Agent Enhancements (webhooks, photos, introspection)
- ADR-0009: Remove PyPI Publishing Infrastructure
- Global CLAUDE.md: `~/.claude/CLAUDE.md` (uv-first philosophy)
- Cloudflare R2 Pricing: https://developers.cloudflare.com/r2/pricing/
- Claude Code Skills Architecture: `~/.claude/plugins/example-skills/skill-creator/`
