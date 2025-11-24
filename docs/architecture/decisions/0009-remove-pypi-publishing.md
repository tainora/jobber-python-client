# 9. Remove PyPI Publishing Infrastructure

Date: 2025-11-23

## Status

Accepted

## Context

The `jobber-python-client` library was initially designed as a public package for distribution via PyPI. However, the project scope has evolved to serve as an internal automation library for a specific roof cleaning business, eliminating the need for public package distribution.

### Current PyPI Infrastructure

The project currently includes:

- **Publishing Script**: `scripts/publish-to-pypi.sh` (173 lines) with CI detection guards and Doppler token management
- **GitHub Actions OIDC**: OIDC trusted publishing configuration in release workflow
- **Documentation References**: Multiple references to PyPI installation, publishing workflows, and the `pypi-doppler` skill across ADRs, plans, and guides
- **Account Migration Complexity**: Pending migration from `terrylica` PyPI account to `tainora_upload` account

### Published Versions

- **v0.2.0**: Published 2025-11-22 to PyPI (terrylica account)
- **v0.2.1**: Published 2025-11-23 to PyPI (terrylica account)

### Project Usage

Analysis of actual usage patterns shows:

- **Internal automation**: Library is used exclusively for a single roof cleaning business's Jobber automation
- **No external consumers**: No evidence of external pip installations or community usage
- **Direct installation**: Development and production environments use `uv` with local paths or Git URLs
- **Tight coupling**: Automation workflows are business-specific and not generalizable

### Maintenance Burden

Maintaining PyPI publishing infrastructure incurs ongoing costs:

- **Account management**: Managing PyPI accounts, tokens, and permissions
- **Doppler secrets**: Separate Doppler project configuration for PyPI tokens
- **Documentation overhead**: Keeping installation instructions and publishing workflows current
- **Security surface**: Additional token management and OIDC configuration
- **Migration complexity**: Pending account migration creates technical debt

## Decision

Remove all PyPI publishing infrastructure and references from the project.

### Scope of Removal

1. **Delete publishing script**: Remove `scripts/publish-to-pypi.sh`
2. **Update documentation**: Remove PyPI references from README, CLAUDE.md, ADRs, and plans
3. **Clean workflows**: Remove OIDC trusted publishing configuration from GitHub Actions
4. **Preserve build tooling**: Keep `pyproject.toml`, `.releaserc.json`, and `package.json` for local builds and semantic versioning

### Preserved Capabilities

- **Local builds**: `uv build` continues to work for local wheel generation
- **Semantic versioning**: `semantic-release` continues to manage versions and changelogs
- **GitHub releases**: GitHub releases continue via semantic-release workflow
- **Development workflow**: No changes to local development, testing, or linting

### Installation Methods

Going forward, users will install via:

```bash
# Direct from Git (recommended for production)
uv add git+https://github.com/tainora/jobber-python-client.git

# Local development
uv add -e /path/to/jobber-python-client
```

### Rationale

1. **Single-purpose library**: Library is internal automation tool, not public package
2. **Simplified maintenance**: Removes account management, token rotation, and publishing workflows
3. **Reduced security surface**: Eliminates PyPI token management and OIDC configuration
4. **Clear scope**: Aligns infrastructure with actual usage patterns
5. **No user impact**: No external users affected by removal

### Alternative Considered

**Migrate to new PyPI account** (rejected):

- Requires setting up new Doppler project for tokens
- Adds complexity for single-consumer library
- Continues maintenance burden for zero external benefit
- Creates confusion with orphaned v0.2.0/v0.2.1 on old account

## Consequences

### Positive

- **Simplified infrastructure**: One less external integration to maintain
- **Clear project scope**: Internal-only library with no public distribution expectations
- **Reduced documentation**: Fewer installation methods and publishing workflows to document
- **Eliminated technical debt**: No PyPI account migration needed

### Negative

- **Historical versions orphaned**: v0.2.0 and v0.2.1 remain on PyPI under `terrylica` account (acceptable - versions are archived)
- **No pip install**: Users cannot `pip install jobber-python-client` (acceptable - single internal user)

### Neutral

- **Installation method change**: Git-based installation is standard practice for internal libraries
- **Build tooling unchanged**: `pyproject.toml` remains for local builds

### Migration Path

1. Create this ADR documenting removal decision
2. Create implementation plan in `docs/development/plan/0009-remove-pypi-publishing/`
3. Delete publishing script and update documentation
4. Validate builds and tests continue to work
5. Commit changes with conventional commit message
6. Allow semantic-release to create next version (v0.2.2) with PyPI removal noted in changelog

### Future Considerations

If public distribution becomes necessary:

- Re-add publishing infrastructure with clear external use cases
- Establish community support model
- Document public API guarantees and breaking change policies
