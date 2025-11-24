# Plan: Remove PyPI Publishing Infrastructure

## Metadata

- **ADR ID**: 0009
- **ADR Link**: `../../../architecture/decisions/0009-remove-pypi-publishing.md`
- **Status**: In Progress
- **Created**: 2025-11-23
- **Updated**: 2025-11-23
- **Owner**: Terry Li

---

## Context

### Background

The `jobber-python-client` library was initially designed for public distribution via PyPI. Two versions (v0.2.0, v0.2.1) were published to PyPI under the `terrylica` account on 2025-11-22 and 2025-11-23 respectively.

A request to migrate PyPI publishing to a new account (`tainora_upload`) surfaced a deeper question: Does this project actually need public package distribution?

**Analysis of actual usage**:

- **Single consumer**: Library is used exclusively for one roof cleaning business's Jobber automation
- **No external adoption**: No evidence of pip installations outside the project owner
- **Internal tooling**: Automation workflows are business-specific and not generalizable
- **Direct installation**: Development uses `uv` with local paths; production would use Git URLs

### Motivation

**Problem**: Maintaining PyPI publishing infrastructure adds complexity without benefit.

**Current overhead**:

1. **Account management**: PyPI account tokens, permissions, 2FA
2. **Doppler secrets**: Separate Doppler project for PYPI_TOKEN storage
3. **Publishing script**: 173-line `scripts/publish-to-pypi.sh` with CI detection guards
4. **GitHub Actions OIDC**: OIDC trusted publishing configuration
5. **Documentation**: Installation instructions, publishing workflows, skill references
6. **Migration complexity**: Pending account migration creates technical debt

**Benefits of removal**:

- **Simplified infrastructure**: One less external integration
- **Clear scope**: Internal-only library aligns with actual usage
- **Reduced security surface**: No PyPI token management
- **Eliminated tech debt**: No account migration needed

### Current State

**PyPI Publishing Infrastructure**:

- ✅ `scripts/publish-to-pypi.sh` - 173-line publishing script
- ✅ `.github/workflows/release.yml` - OIDC trusted publishing configuration (lines 13, 40-42)
- ✅ Documentation references in 8 files (README, CLAUDE, 3 plans, 1 validation doc)
- ✅ Published versions: v0.2.0 (2025-11-22), v0.2.1 (2025-11-23)

**Preserved Build Tooling**:

- ✅ `pyproject.toml` - Required for `uv build` and local development
- ✅ `.releaserc.json` - Semantic versioning (GitHub releases, changelogs)
- ✅ `package.json` - Semantic-release configuration

**Affected Documentation**:

1. `/Users/terryli/own/jobber/README.md` - Lines 17-18 (pip install instructions)
2. `/Users/terryli/own/jobber/CLAUDE.md` - Line 133 (plan.md reference to PyPI)
3. `/Users/terryli/own/jobber/docs/development/plan/0006-production-readiness-validation/plan.md` - 7+ references
4. `/Users/terryli/own/jobber/docs/development/plan/0007-ai-agent-enhancements/plan.md` - 5+ references
5. `/Users/terryli/own/jobber/docs/development/plan/0008-comprehensive-validation/plan.md` - 4+ references
6. `/Users/terryli/own/jobber/docs/development/validation/0006-completion-summary.md` - Entire PyPI section (lines 206-235)
7. `/Users/terryli/own/jobber/.github/workflows/release.yml` - OIDC config (lines 13, 40-42)

### Success Criteria

Implementation is complete when:

1. ✅ Publishing script deleted (`scripts/publish-to-pypi.sh`)
2. ✅ Documentation updated to remove PyPI installation instructions
3. ✅ GitHub Actions OIDC configuration removed
4. ✅ Historical documentation (ADRs, plans) updated to reflect removal
5. ✅ Local builds continue to work (`uv build` succeeds)
6. ✅ Tests continue to pass (`pytest` succeeds)
7. ✅ Semantic-release continues to work (version management, changelogs, GitHub releases)
8. ✅ Changes committed with conventional commit message
9. ✅ CHANGELOG.md updated via semantic-release

---

## Goals

### Primary Goals

1. **Remove PyPI Publishing Infrastructure**: Delete publishing script and GitHub Actions OIDC configuration

2. **Update Current Documentation**: Remove PyPI references from README.md and CLAUDE.md (user-facing docs)

3. **Update Historical Documentation**: Remove PyPI references from plans and validation docs (keep as historical record of what was planned but is no longer needed)

4. **Preserve Build Capabilities**: Ensure `uv build`, tests, and semantic-release continue to work

### Secondary Goals

1. **Simplify Installation Instructions**: Replace pip install with Git-based installation in README

2. **Document Removal Decision**: Capture rationale in ADR-0009 for future reference

3. **Validate Build Tooling**: Run builds and tests to ensure no breakage

---

## Plan

### Phase 1: Documentation Setup (5 minutes)

**Status**: ✅ Complete

1. ✅ Create ADR-0009 (`docs/architecture/decisions/0009-remove-pypi-publishing.md`)
2. ✅ Create this plan (`docs/development/plan/0009-remove-pypi-publishing/plan.md`)

### Phase 2: Delete Publishing Infrastructure (2 minutes)

**Status**: ✅ Complete

1. ✅ Delete `scripts/publish-to-pypi.sh`
2. ✅ Update `.github/workflows/release.yml`:
   - Remove `id-token: write` permission (line 13)
   - Remove OIDC comment (lines 40-42)

### Phase 3: Update Current Documentation (10 minutes)

**Status**: ✅ Complete

1. ✅ Update `README.md`:
   - Remove "Install from PyPI" section (lines 17-18)
   - Add Git-based installation instructions

2. ✅ Update `CLAUDE.md`:
   - Remove PyPI reference from plan.md link (line 133)

### Phase 4: Update Historical Documentation (15 minutes)

**Status**: ✅ Complete

1. ✅ Update `docs/development/plan/0006-production-readiness-validation/plan.md`:
   - Remove "Phase 5: PyPI Publication" section
   - Remove PyPI checkboxes and validation steps
   - Remove UV_PUBLISH_TOKEN references

2. ✅ Update `docs/development/plan/0007-ai-agent-enhancements/plan.md`:
   - Remove "Publish to PyPI" goals
   - Remove PyPI publication workflow details
   - Remove pypi-doppler skill references

3. ✅ Update `docs/development/plan/0008-comprehensive-validation/plan.md`:
   - Remove "Phase 7.2: PyPI Publication" section
   - Remove pypi-doppler skill invocation references
   - Remove PyPI checklist items

4. ✅ Update `docs/development/validation/0006-completion-summary.md`:
   - Remove entire "PyPI Publication" section (lines 206-235)

### Phase 5: Validation (5 minutes)

**Status**: ✅ Complete

1. ✅ Run `uv build` to verify local builds work
2. ✅ Run `pytest` to verify tests pass (129/129 passed)
3. ✅ Run `ruff check` to verify linting passes
4. ✅ Run `mypy` to verify type checking passes
5. ✅ Fix pyproject.toml: ruff.target-version and mypy.python_version (were incorrectly set to package version)

### Phase 6: Commit Changes (5 minutes)

**Status**: ✅ Complete

1. ✅ Stage all changes: `git add -A`
2. ✅ Create conventional commit: `chore: remove PyPI publishing infrastructure`
3. ✅ Commit message body:
   ```
   Remove all PyPI publishing infrastructure and references.

   The library is internal-only automation for a single roof cleaning
   business. Public PyPI distribution adds maintenance overhead without
   external benefit.

   - Delete scripts/publish-to-pypi.sh (173 lines)
   - Remove GitHub Actions OIDC trusted publishing config
   - Update installation docs to use Git URLs
   - Remove PyPI references from historical plans
   - Fix pyproject.toml (ruff.target-version, mypy.python_version)

   Preserved capabilities:
   - Local builds via uv build
   - Semantic versioning via semantic-release
   - GitHub releases via semantic-release workflow
   - All tests passing (129/129)

   See ADR-0009 for full rationale.
   ```
4. ✅ Verify commit message format
5. ⬜ Push to GitHub (semantic-release will create v0.2.2 with updated changelog)

---

## Task List

### Setup
- [x] Create ADR-0009
- [x] Create plan.md (this file)

### Delete Infrastructure
- [x] Delete `scripts/publish-to-pypi.sh`
- [x] Edit `.github/workflows/release.yml` (remove OIDC)

### Update Documentation
- [x] Edit `README.md` (installation section)
- [x] Edit `CLAUDE.md` (plan reference)
- [x] Edit `plan/0006-production-readiness-validation/plan.md`
- [x] Edit `plan/0007-ai-agent-enhancements/plan.md`
- [x] Edit `plan/0008-comprehensive-validation/plan.md`
- [x] Edit `validation/0006-completion-summary.md`

### Validate
- [x] Run `uv build`
- [x] Run `pytest` (129/129 passed)
- [x] Run `ruff check`
- [x] Run `mypy`
- [x] Fix pyproject.toml (ruff.target-version, mypy.python_version)

### Commit
- [x] Stage changes (`git add -A`)
- [x] Commit with conventional message (commit 2840e26)
- [ ] Push to GitHub

---

## Risks and Mitigations

### Risk 1: Break Local Builds

**Likelihood**: Low
**Impact**: High
**Mitigation**: Keep `pyproject.toml` unchanged. Validate `uv build` after each change.

### Risk 2: Break Semantic-Release

**Likelihood**: Low
**Impact**: Medium
**Mitigation**: Keep `.releaserc.json` and `package.json` unchanged. Only remove PyPI-specific items.

### Risk 3: Orphaned PyPI Versions

**Likelihood**: Certain
**Impact**: Low
**Mitigation**: Document in ADR that v0.2.0/v0.2.1 remain on PyPI as archived versions. No action needed.

---

## SLOs

- **Availability**: 99.9% - No impact to core library functionality
- **Correctness**: 100% - All builds and tests must pass after changes
- **Observability**: All validation steps must be logged and verified
- **Maintainability**: Reduced complexity via infrastructure removal

---

## Progress Log

### 2025-11-23 (Initial Planning)

- ✅ Created ADR-0009
- ✅ Created plan.md with full task list
- ✅ Implementation complete

### 2025-11-23 (Implementation)

- ✅ Deleted scripts/publish-to-pypi.sh
- ✅ Removed OIDC configuration from .github/workflows/release.yml
- ✅ Updated README.md with Git-based installation
- ✅ Updated CLAUDE.md to remove PyPI reference
- ✅ Updated all historical plans (0006, 0007, 0008) to remove PyPI sections
- ✅ Updated validation/0006-completion-summary.md
- ✅ Fixed pyproject.toml: ruff.target-version and mypy.python_version
- ✅ Validated: uv build, pytest (129/129), ruff check, mypy
- ✅ Committed changes (commit 2840e26)
- ⏳ Ready to push to GitHub

---

## Notes

- **No breaking changes**: Removal is purely infrastructure cleanup
- **Historical integrity**: Keep references in historical docs to preserve decision trail
- **Future extensibility**: If public distribution becomes necessary, ADR-0009 documents what was removed and why
