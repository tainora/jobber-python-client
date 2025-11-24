# Plan: Claude Code CLI Automation Enhancements

## Metadata

- **ADR ID**: 0010
- **ADR Link**: `../../../architecture/decisions/0010-automation-enhancements.md`
- **Status**: In Progress
- **Created**: 2025-11-23
- **Updated**: 2025-11-23
- **Owner**: Terry Li

---

## Context

### Background

The jobber-python-client library v0.2.1 has achieved 90% automation readiness for Claude Code CLI workflows after implementing webhooks, photo uploads, and schema introspection (ADR-0007). Comprehensive analysis by 5 parallel sub-agents revealed four targeted enhancements needed to enable full autonomous control of Jobber accounts via Claude Code CLI.

**Sub-Agent Findings**:

1. **PyPI Reference Auditor**: Found 2 example files using `pip install` instead of `uv pip install` (violates project standards)
2. **Automation Capabilities Analyst**: Mapped 90% automation readiness across 7 workflow phases, identified missing E2E orchestration examples
3. **Automation Gap Identifier**: Confirmed all ADR-0007 gaps addressed, no critical missing features
4. **Claude Code Integration Researcher**: Analyzed Skills architecture, recommended atomic skills pattern + hybrid E2E examples
5. **Enhancement Proposer**: Synthesized findings, proposed Doppler reorganization + cloud storage evaluation + E2E examples

### Motivation

**Problem**: AI agents have atomic capabilities (OAuth, GraphQL, webhooks) but lack guidance on orchestrating complete business workflows.

**Current State**:
- Individual API calls work perfectly (GraphQL queries, mutations, webhooks)
- No examples showing how to chain operations (Lead → Client → Quote → Job)
- Doppler secrets scattered across projects (Jobber mixed with PyPI/Crates.io)
- Cloud storage uncertainty (photo upload assumes S3 but no AWS credentials found)

**Target State**:
- AI agents can learn complete workflows from runnable E2E examples
- Dedicated Doppler project organizes all Jobber-related secrets
- Cloud storage decision documented and implemented (Cloudflare R2 chosen)
- All examples follow project standards (uv-first philosophy)

### Current State

**Library Capabilities** (v0.2.1):
- ✅ OAuth 2.0 PKCE authentication (one-time browser flow, then automated)
- ✅ GraphQL query execution (fail-fast error handling, rate limit awareness)
- ✅ Webhook event processing (HMAC-SHA256 validation, real-time <1s latency)
- ✅ Photo upload workflow (S3 presigned URLs + note linking)
- ✅ Schema introspection (AI query validation, disk caching)
- ✅ Visual confirmation URLs (jobberWebUri pattern, terminal hyperlinks)

**Test Coverage**: 129/129 tests passing (100% pass rate, 0.11s execution)
**Type Safety**: mypy 0 errors (strict mode, all public APIs typed)
**Code Quality**: ruff 0 errors, line length 100

**Documentation**:
- ✅ 9 ADRs (architecture decisions)
- ✅ 3 implementation plans (0006, 0007, 0008)
- ✅ 3 atomic skills (oauth-pkce-doppler, visual-confirmation-urls, graphql-query-execution)
- ✅ 6 runnable examples (basic_usage, error_handling, visual_confirmation_urls, webhook_handler, photo_upload_workflow, schema_introspection)

**Gaps Identified**:
- ❌ Tool reference inconsistency (2 examples use `pip install`)
- ❌ Doppler organization (secrets in `claude-config/prd`, not dedicated project)
- ❌ Cloud storage uncertainty (S3 assumed but no AWS credentials)
- ❌ Missing E2E workflow examples (no Lead → Client orchestration pattern)

### Success Criteria

Implementation is complete when:

1. ✅ Example files use `uv pip install` (consistency with project standards)
2. ✅ Doppler "jobber" project created with dev/prd configs
3. ✅ All required secrets migrated to new Doppler project
4. ✅ Cloud storage decision documented (Cloudflare R2 chosen)
5. ✅ R2 endpoint integration implemented in `jobber/photos.py`
6. ✅ E2E lead capture example created and validated
7. ✅ All tests passing (129/129)
8. ✅ Documentation updated (CLAUDE.md, ADR-0010, plan-0010)
9. ✅ Changes committed with conventional commit message
10. ✅ Automation readiness increased from 90% → 95%

---

## Goals

### Primary Goals

1. **Maintain Consistency**: Update all example files to follow uv-first philosophy documented in global CLAUDE.md

2. **Organize Secrets**: Create dedicated Doppler "jobber" project with dev/prd configs, isolate Jobber secrets from unrelated automation

3. **Resolve Cloud Storage**: Document and implement Cloudflare R2 integration for photo uploads (zero egress fees, full S3 compatibility)

4. **Enable Workflow Learning**: Create runnable E2E lead capture example teaching AI agents how to orchestrate multi-step business processes

### Secondary Goals

1. **Future-Proof Costs**: Zero egress fees with R2 eliminate scaling concerns (0-100,000 photos = $0 egress)

2. **Simplify Onboarding**: New developers find all Jobber secrets in one Doppler project, not scattered across multiple projects

3. **Demonstrate Pattern**: E2E example serves as template for future workflows (Quote → Job, Invoice → Payment)

4. **Validate Doppler Structure**: Dual-config (dev/prd) supports safe testing before production deployment

---

## Plan

### Phase 1: Tool Reference Consistency (15 minutes)

**Status**: Pending

**Objective**: Update 2 example files to use `uv pip install` instead of `pip install`

**Changes**:

1. **examples/photo_upload_workflow.py:15**
   - Old: `- boto3 installed: pip install boto3`
   - New: `- boto3 installed: uv pip install boto3`

2. **examples/webhook_handler.py:12**
   - Old: `- Flask installed: pip install flask`
   - New: `- Flask installed: uv pip install flask`

**Validation**:
```bash
ruff check examples/
pytest -v  # All 129 tests should pass
```

**Deliverables**:
- 2 files updated
- No functional changes (comments only)
- Alignment with `~/.claude/CLAUDE.md` uv-first philosophy

---

### Phase 2: Doppler Project Structure (45 minutes)

**Status**: Pending

**Objective**: Create dedicated "jobber" Doppler project with dev/prd configs

**Structure**:
```
Project: jobber
├── Config: dev (sandbox)
│   ├── JOBBER_CLIENT_ID
│   ├── JOBBER_CLIENT_SECRET
│   ├── JOBBER_ACCESS_TOKEN (managed by library)
│   ├── JOBBER_REFRESH_TOKEN (managed by library)
│   ├── JOBBER_TOKEN_EXPIRES_AT (managed by library)
│   ├── CLOUD_STORAGE_ACCESS_KEY_ID (R2)
│   ├── CLOUD_STORAGE_SECRET_ACCESS_KEY (R2)
│   ├── CLOUD_STORAGE_BUCKET_NAME (jobber-photos-dev)
│   ├── CLOUD_STORAGE_ENDPOINT_URL (https://<account>.r2.cloudflarestorage.com)
│   └── WEBHOOK_SECRET (dev webhook validation)
└── Config: prd (production)
    └── [same structure, production values]
```

**Implementation Steps**:

1. Create Doppler project:
   ```bash
   doppler projects create jobber \
     --description "Jobber API automation secrets (dev/prd environments)"
   ```

2. Create configs:
   ```bash
   doppler configs create dev --project jobber
   doppler configs create prd --project jobber
   ```

3. Migrate existing secrets from `claude-config/prd`:
   ```bash
   # Extract current values
   doppler secrets get JOBBER_CLIENT_ID --project claude-config --config prd --plain > /tmp/jobber_client_id
   doppler secrets get JOBBER_CLIENT_SECRET --project claude-config --config prd --plain > /tmp/jobber_client_secret

   # Set in new project
   doppler secrets set JOBBER_CLIENT_ID="$(cat /tmp/jobber_client_id)" --project jobber --config prd
   doppler secrets set JOBBER_CLIENT_SECRET="$(cat /tmp/jobber_client_secret)" --project jobber --config prd

   # Clean up temp files
   rm /tmp/jobber_client_id /tmp/jobber_client_secret
   ```

4. Add cloud storage secrets (R2):
   ```bash
   doppler secrets set CLOUD_STORAGE_ACCESS_KEY_ID="..." --project jobber --config prd
   doppler secrets set CLOUD_STORAGE_SECRET_ACCESS_KEY="..." --project jobber --config prd
   doppler secrets set CLOUD_STORAGE_BUCKET_NAME="jobber-photos-prd" --project jobber --config prd
   doppler secrets set CLOUD_STORAGE_ENDPOINT_URL="https://<account>.r2.cloudflarestorage.com" --project jobber --config prd
   ```

5. Update code to reference new Doppler project:
   - `jobber/auth.py:_load_from_doppler()` - Change `--project claude-config --config prd` → `--project jobber --config prd`
   - `jobber/photos.py:get_s3_credentials_from_doppler()` - Update Doppler project reference

**Validation**:
```bash
# Test token loading from new project
uv run jobber_auth.py  # Should authenticate successfully
pytest tests/test_auth.py -v  # Token management tests should pass
```

**Deliverables**:
- Doppler project "jobber" created
- 10 secrets × 2 configs (dev/prd)
- Code updated to reference new project
- Token refresh validated

---

### Phase 3: Cloud Storage Integration (1 hour)

**Status**: Pending

**Objective**: Implement Cloudflare R2 integration for photo uploads

**Decision Rationale** (from ADR-0010):
- Zero egress fees (vs $0.12-0.20/GB for AWS/GCP)
- Full S3 compatibility (boto3 works with just endpoint change)
- Lowest storage cost ($0.015/GB-month)
- 5-minute migration effort

**Code Changes**:

1. **jobber/photos.py** - Update to support R2 endpoint:

```python
def get_s3_credentials_from_doppler(
    project: str = "jobber",  # Changed from "claude-config"
    config: str = "prd",
) -> tuple[str, str, str, str | None]:
    """Get S3/R2 credentials from Doppler."""
    cmd = [
        "doppler",
        "secrets",
        "download",
        "--no-file",
        "--format",
        "json",
        "--project",
        project,
        "--config",
        config,
    ]
    # ... existing implementation ...

    # Extract endpoint URL (optional for R2)
    endpoint_url = secrets.get("CLOUD_STORAGE_ENDPOINT_URL")

    return access_key, secret_key, bucket_name, endpoint_url


def generate_presigned_upload_url(
    bucket_name: str,
    object_key: str,
    expiration: int = 3600,
    access_key_id: str | None = None,
    secret_access_key: str | None = None,
    endpoint_url: str | None = None,  # NEW: R2 endpoint support
) -> str:
    """Generate presigned URL for direct upload to S3/R2."""
    # Fetch credentials if not provided
    if not (access_key_id and secret_access_key):
        access_key_id, secret_access_key, bucket_name, endpoint_url = (
            get_s3_credentials_from_doppler()
        )

    # Create S3 client (works for both S3 and R2)
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        endpoint_url=endpoint_url,  # None for S3, URL for R2
    )

    # ... rest of implementation unchanged ...
```

2. **examples/photo_upload_workflow.py** - Update prerequisites:

```python
# Prerequisites:
# - boto3 installed: uv pip install boto3  # UPDATED
# - Doppler configured with R2 credentials (jobber/prd project)
# - R2 bucket created with CORS configuration
```

**R2 Setup Steps** (manual, one-time):

1. Create Cloudflare R2 bucket via dashboard
2. Generate API tokens (Access Key ID + Secret Access Key)
3. Configure CORS:
   ```json
   [
     {
       "AllowedOrigins": ["*"],
       "AllowedMethods": ["GET", "PUT", "POST"],
       "AllowedHeaders": ["*"],
       "MaxAgeSeconds": 3600
     }
   ]
   ```
4. Store credentials in Doppler (already done in Phase 2)

**Validation**:
```bash
# Test presigned URL generation
python -c "
from jobber.photos import generate_presigned_upload_url
url = generate_presigned_upload_url('jobber-photos-prd', 'test.jpg')
print(f'✅ Generated presigned URL: {url[:50]}...')
"

# Test photo upload workflow
uv run examples/photo_upload_workflow.py

# Run photo-related tests
pytest tests/test_photos.py -v
```

**Deliverables**:
- `jobber/photos.py` updated with R2 endpoint support
- Example updated with R2 prerequisites
- Presigned URL generation validated
- 11 photo tests passing

---

### Phase 4: E2E Lead Capture Example (3-4 hours)

**Status**: Pending

**Objective**: Create runnable E2E workflow example showing Lead → Client creation

**File**: `examples/e2e_lead_to_client.py`

**Structure** (PEP 723 script):

```python
# /// script
# dependencies = ["jobber-python-client>=0.2.1"]
# ///

"""
End-to-End Lead Capture Workflow

Demonstrates autonomous client creation from lead data sources:
- Website contact forms
- Webhook events
- Email inquiries
- Manual lead entry

AI Agent Orchestration Pattern:
1. Receive lead data (any source)
2. Validate required fields (name, email/phone)
3. Construct GraphQL clientCreate mutation
4. Execute with fail-fast error handling
5. Return visual confirmation URL (jobberWebUri)

Skills Referenced:
- graphql-query-execution: Mutation construction & execution
- visual-confirmation-urls: Include jobberWebUri for verification
- oauth-pkce-doppler: Automatic token management

Workflow Autonomy: 100% (no human intervention after lead received)
"""

import sys
from typing import Any

from jobber import JobberClient
from jobber.exceptions import (
    AuthenticationError,
    ConfigurationError,
    GraphQLError,
    NetworkError,
)


def validate_lead_data(lead: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate lead data has required fields.

    AI Agent Decision Point:
    - Required: firstName, lastName
    - At least one: email OR phone
    - Optional: address fields (improve matching but not required)

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    if not lead.get("firstName"):
        errors.append("Missing required field: firstName")
    if not lead.get("lastName"):
        errors.append("Missing required field: lastName")
    if not lead.get("email") and not lead.get("phone"):
        errors.append("Missing contact info: need email OR phone")

    return (len(errors) == 0, errors)


def construct_client_create_mutation(lead: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """
    Construct GraphQL clientCreate mutation from lead data.

    AI Agent Decision Point:
    - ALWAYS include jobberWebUri field (visual-confirmation-urls pattern)
    - Validate mutation structure against schema (use schema introspection)
    - Use variables for type safety (prevent injection)

    Skills: graphql-query-execution, visual-confirmation-urls
    """
    mutation = """
        mutation CreateClient($input: ClientCreateInput!) {
            clientCreate(input: $input) {
                client {
                    id
                    name
                    jobberWebUri
                }
                userErrors {
                    message
                    path
                }
            }
        }
    """

    variables = {
        "input": {
            "firstName": lead["firstName"],
            "lastName": lead["lastName"],
        }
    }

    # Add optional fields if present
    if lead.get("email"):
        variables["input"]["email"] = lead["email"]
    if lead.get("phone"):
        variables["input"]["phone"] = lead["phone"]
    if lead.get("companyName"):
        variables["input"]["companyName"] = lead["companyName"]

    # Add address if available (improves client matching)
    if lead.get("street1") or lead.get("city"):
        variables["input"]["billingAddress"] = {}
        if lead.get("street1"):
            variables["input"]["billingAddress"]["street1"] = lead["street1"]
        if lead.get("street2"):
            variables["input"]["billingAddress"]["street2"] = lead["street2"]
        if lead.get("city"):
            variables["input"]["billingAddress"]["city"] = lead["city"]
        if lead.get("province"):
            variables["input"]["billingAddress"]["province"] = lead["province"]
        if lead.get("postalCode"):
            variables["input"]["billingAddress"]["postalCode"] = lead["postalCode"]
        if lead.get("country"):
            variables["input"]["billingAddress"]["country"] = lead["country"]

    return mutation, variables


def create_client_from_lead(lead: dict[str, Any]) -> dict[str, Any]:
    """
    Execute complete lead → client workflow.

    AI Agent Decision Point:
    - Validate lead data BEFORE API call (fail-fast at boundary)
    - Construct mutation with type-safe variables
    - Handle errors without retry (fail-fast, surface to caller)
    - Return jobberWebUri for visual verification

    Returns:
        {
            "client_id": "gid://...",
            "client_name": "John Doe",
            "jobber_web_url": "https://secure.getjobber.com/...",
        }

    Raises:
        ValueError: Invalid lead data
        GraphQLError: Mutation failed (duplicate client, invalid data)
        AuthenticationError: Token expired/invalid
        NetworkError: Network failure
        ConfigurationError: Missing Doppler secrets

    Error Handling Pattern:
    - NO automatic retry (fail-fast philosophy)
    - NO default values (explicit errors better than silent failures)
    - NO fallback (caller decides recovery strategy)
    - ALL errors propagated with context
    """
    # Step 1: Validate lead data (fail-fast at boundary)
    is_valid, errors = validate_lead_data(lead)
    if not is_valid:
        raise ValueError(f"Invalid lead data: {', '.join(errors)}")

    # Step 2: Construct mutation (type-safe, includes jobberWebUri)
    mutation, variables = construct_client_create_mutation(lead)

    # Step 3: Initialize client (oauth-pkce-doppler skill handles auth)
    try:
        client = JobberClient.from_doppler(
            project="jobber",  # NEW: dedicated Doppler project
            config="prd",
        )
    except ConfigurationError as e:
        print(f"❌ Doppler configuration error: {e}")
        print("Ensure secrets exist in Doppler: doppler secrets --project jobber --config prd")
        raise

    # Step 4: Execute mutation (fail-fast error handling)
    try:
        result = client.execute_query(mutation, variables)
    except AuthenticationError:
        print("❌ Authentication failed - token may be expired")
        print("Run: uv run jobber_auth.py")
        raise
    except NetworkError as e:
        print(f"❌ Network error: {e}")
        raise
    except GraphQLError as e:
        print(f"❌ GraphQL error: {e}")
        if e.context and "errors" in e.context:
            for error in e.context["errors"]:
                print(f"  - {error.get('message', 'Unknown error')}")
        raise

    # Step 5: Extract client data from response
    client_create = result.get("clientCreate", {})

    # Check for user errors (e.g., duplicate client)
    user_errors = client_create.get("userErrors", [])
    if user_errors:
        error_messages = [err["message"] for err in user_errors]
        raise GraphQLError(
            f"Client creation failed: {', '.join(error_messages)}",
            context={"user_errors": user_errors},
        )

    client_data = client_create.get("client", {})
    if not client_data:
        raise GraphQLError(
            "Client creation succeeded but no client data returned",
            context={"response": result},
        )

    # Step 6: Return structured result with visual confirmation URL
    return {
        "client_id": client_data["id"],
        "client_name": client_data["name"],
        "jobber_web_url": client_data["jobberWebUri"],
    }


def main() -> int:
    """
    Example usage: Create client from sample lead data.

    AI Agent Integration:
    - Replace sample_lead with actual data from:
      - Webhook event payload
      - Website form submission
      - Email parser output
      - CRM integration
    """
    # Sample lead data (replace with actual source)
    sample_lead = {
        "firstName": "Jane",
        "lastName": "Smith",
        "email": "jane.smith@example.com",
        "phone": "+1-555-123-4567",
        "companyName": "Smith Roofing Co.",
        "street1": "123 Main St",
        "city": "Vancouver",
        "province": "BC",
        "postalCode": "V6B 1A1",
        "country": "CA",
    }

    print("🔄 Creating Jobber client from lead data...")
    print(f"   Lead: {sample_lead['firstName']} {sample_lead['lastName']}")

    try:
        result = create_client_from_lead(sample_lead)

        print("✅ Client created successfully!")
        print(f"   Client ID: {result['client_id']}")
        print(f"   Client Name: {result['client_name']}")
        print(f"   🔗 View in Jobber: {result['jobber_web_url']}")

        return 0

    except ValueError as e:
        print(f"❌ Validation error: {e}")
        return 1
    except (GraphQLError, AuthenticationError, NetworkError, ConfigurationError) as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

**Validation**:
```bash
# Dry run (requires Doppler + OAuth setup)
uv run examples/e2e_lead_to_client.py

# Expected output:
# 🔄 Creating Jobber client from lead data...
#    Lead: Jane Smith
# ✅ Client created successfully!
#    Client ID: gid://jobber/Client/123456
#    Client Name: Jane Smith
#    🔗 View in Jobber: https://secure.getjobber.com/clients/123456
```

**Deliverables**:
- `examples/e2e_lead_to_client.py` created (300+ lines)
- PEP 723 self-contained script
- AI orchestration comments throughout
- Error handling demonstrates fail-fast pattern
- Visual confirmation URL included

---

### Phase 5: Documentation Updates (30 minutes)

**Status**: Pending

**Objective**: Update CLAUDE.md with navigation to automation enhancements

**Changes**:

1. **CLAUDE.md** - Add E2E examples section:

```markdown
## Examples

**See [examples/](examples/) directory for runnable code.**

### End-to-End Workflows

- **[e2e_lead_to_client.py](examples/e2e_lead_to_client.py)** - Lead capture → Client creation (100% autonomous)

### Atomic Capabilities

- **[basic_usage.py](examples/basic_usage.py)** - Account queries, pagination, throttle status
- **[error_handling.py](examples/error_handling.py)** - Comprehensive exception handling patterns
- **[visual_confirmation_urls.py](examples/visual_confirmation_urls.py)** - Get web links for visual verification
- **[webhook_handler.py](examples/webhook_handler.py)** - Flask webhook endpoint with HMAC validation
- **[photo_upload_workflow.py](examples/photo_upload_workflow.py)** - R2/S3 photo upload + note linking
- **[schema_introspection.py](examples/schema_introspection.py)** - GraphQL schema discovery for AI context
```

2. **CLAUDE.md** - Add Doppler section:

```markdown
## Doppler Configuration

**Project**: jobber
**Configs**: dev (sandbox), prd (production)

**Required Secrets**:
- OAuth: `JOBBER_CLIENT_ID`, `JOBBER_CLIENT_SECRET`
- Tokens: `JOBBER_ACCESS_TOKEN`, `JOBBER_REFRESH_TOKEN`, `JOBBER_TOKEN_EXPIRES_AT` (managed by library)
- Cloud Storage: `CLOUD_STORAGE_ACCESS_KEY_ID`, `CLOUD_STORAGE_SECRET_ACCESS_KEY`, `CLOUD_STORAGE_BUCKET_NAME`, `CLOUD_STORAGE_ENDPOINT_URL`
- Webhooks: `WEBHOOK_SECRET`

**Setup**:
```bash
# Create project and configs
doppler projects create jobber
doppler configs create dev --project jobber
doppler configs create prd --project jobber

# Set secrets
doppler secrets set JOBBER_CLIENT_ID="..." --project jobber --config prd
# ... (see ADR-0010 for complete list)
```
```

**Deliverables**:
- CLAUDE.md updated with E2E examples section
- CLAUDE.md updated with Doppler configuration guide
- Documentation aligned with ADR-0010

---

### Phase 6: Validation (30 minutes)

**Status**: Pending

**Objective**: Validate all changes work correctly

**Validation Steps**:

1. **Build validation**:
   ```bash
   uv build
   # Expected: Successfully built dist/jobber_python_client-0.2.1.tar.gz
   #            Successfully built dist/jobber_python_client-0.2.1-py3-none-any.whl
   ```

2. **Test validation**:
   ```bash
   pytest -v
   # Expected: 129/129 tests passing
   ```

3. **Type checking**:
   ```bash
   mypy jobber/
   # Expected: Success: no issues found in 9 source files
   ```

4. **Linting**:
   ```bash
   ruff check jobber/ examples/
   # Expected: All checks passed!
   ```

5. **Example validation**:
   ```bash
   # Test updated examples (comments only, should work unchanged)
   uv run examples/photo_upload_workflow.py --help
   uv run examples/webhook_handler.py --help

   # Test new E2E example
   uv run examples/e2e_lead_to_client.py
   # Expected: Client created successfully with jobberWebUri
   ```

6. **Doppler validation** (if migrated):
   ```bash
   # Test token loading from new project
   uv run jobber_auth.py
   # Expected: OAuth flow succeeds, tokens stored in jobber/prd

   # Verify secrets accessible
   doppler secrets --project jobber --config prd
   # Expected: List of 10 secrets
   ```

**Deliverables**:
- All builds succeed
- All tests pass
- All type checks pass
- All lint checks pass
- All examples run successfully
- Doppler integration validated

---

### Phase 7: Commit and Release (15 minutes)

**Status**: Pending

**Objective**: Commit changes with conventional commit message

**Commit Message**:
```
feat: add automation enhancements for Claude Code CLI

Implement four targeted enhancements to enable full autonomous control
of Jobber accounts via Claude Code CLI:

1. Tool Reference Consistency
   - Update examples to use 'uv pip install' (not 'pip install')
   - Align with project's uv-first philosophy

2. Dedicated Doppler Project
   - Create 'jobber' project with dev/prd configs
   - Migrate secrets from claude-config/prd
   - Support environment isolation (dev/prd separation)

3. Cloud Storage Integration
   - Implement Cloudflare R2 support (zero egress fees)
   - Full S3 compatibility via boto3
   - 5-minute migration from AWS S3

4. End-to-End Workflow Example
   - Create e2e_lead_to_client.py (Lead → Client creation)
   - Demonstrate AI orchestration pattern
   - Include fail-fast error handling
   - Reference atomic skills (graphql, visual-urls, oauth)

Changes:
- docs/architecture/decisions/0010-automation-enhancements.md
- docs/development/plan/0010-automation-enhancements/plan.md
- examples/photo_upload_workflow.py (pip → uv pip)
- examples/webhook_handler.py (pip → uv pip)
- jobber/auth.py (Doppler project reference)
- jobber/photos.py (R2 endpoint support)
- examples/e2e_lead_to_client.py (NEW)
- CLAUDE.md (examples + Doppler sections)

Validation:
- 129/129 tests passing
- mypy 0 errors
- ruff 0 errors
- All examples runnable

Automation readiness: 90% → 95%

See ADR-0010 for full rationale.
```

**Git Commands**:
```bash
git add -A
git commit -m "feat: add automation enhancements for Claude Code CLI"
git push
```

**Deliverables**:
- Changes committed with conventional commit
- Semantic-release will create v0.2.2 tag
- GitHub release will be created automatically
- CHANGELOG.md will be updated

---

## Task List

### Phase 1: Tool Reference Consistency
- [ ] Edit `examples/photo_upload_workflow.py:15` (pip → uv pip)
- [ ] Edit `examples/webhook_handler.py:12` (pip → uv pip)
- [ ] Validate with ruff check

### Phase 2: Doppler Project Structure
- [ ] Create Doppler project "jobber"
- [ ] Create dev config
- [ ] Create prd config
- [ ] Migrate secrets from claude-config/prd
- [ ] Add cloud storage secrets
- [ ] Update `jobber/auth.py` Doppler references
- [ ] Validate token loading

### Phase 3: Cloud Storage Integration
- [ ] Update `jobber/photos.py` with R2 endpoint support
- [ ] Update example prerequisites
- [ ] Test presigned URL generation
- [ ] Run photo tests

### Phase 4: E2E Lead Capture Example
- [ ] Create `examples/e2e_lead_to_client.py`
- [ ] Implement validation logic
- [ ] Implement mutation construction
- [ ] Implement client creation workflow
- [ ] Add AI orchestration comments
- [ ] Test against live API

### Phase 5: Documentation Updates
- [ ] Update CLAUDE.md (E2E examples section)
- [ ] Update CLAUDE.md (Doppler configuration guide)

### Phase 6: Validation
- [ ] Run uv build
- [ ] Run pytest (129/129 tests)
- [ ] Run mypy
- [ ] Run ruff check
- [ ] Test all examples
- [ ] Validate Doppler integration

### Phase 7: Commit and Release
- [ ] Stage changes (git add -A)
- [ ] Commit with conventional message
- [ ] Push to GitHub
- [ ] Verify semantic-release creates v0.2.2

---

## Risks and Mitigations

### Risk 1: Doppler Migration Breaks Token Refresh

**Likelihood**: Medium
**Impact**: High (blocks all API calls)

**Mitigation**:
- Test token loading BEFORE removing secrets from old project
- Keep secrets in both projects during transition
- Validate `uv run jobber_auth.py` succeeds with new project
- Only remove old secrets after 24-hour validation period

### Risk 2: R2 Presigned URLs Don't Work

**Likelihood**: Low
**Impact**: Medium (blocks photo uploads)

**Mitigation**:
- Test presigned URL generation in isolation first
- Verify CORS configuration on R2 bucket
- Fallback to AWS S3 if R2 fails (5-minute rollback)
- Document S3 compatibility as requirement

### Risk 3: E2E Example Fails Against Live API

**Likelihood**: Medium
**Impact**: Low (example only, not core library)

**Mitigation**:
- Test against sandbox Jobber account first (dev config)
- Use existing validation patterns from other examples
- Include error handling for all known failure modes
- Document prerequisite setup clearly

---

## SLOs

- **Availability**: 99.9% - No impact to core library functionality
- **Correctness**: 100% - All 129 tests must pass after changes
- **Observability**: All validation steps logged and verified
- **Maintainability**: ADR + plan + code in sync, clear documentation

---

## Progress Log

### 2025-11-23 (Initial Planning)

- ✅ Created ADR-0010 (automation enhancements decision)
- ✅ Created plan-0010 with plan/context/task list
- ⏳ Ready to begin Phase 1 implementation

---

## Notes

- **No breaking changes**: All enhancements are additive or cosmetic
- **Backward compatible**: Environment variables support gradual migration
- **Optional adoption**: Users can continue with AWS S3 if preferred
- **Future extensibility**: E2E pattern serves as template for additional workflows (Quote → Job, Invoice → Payment)
