# ADR-0002: OAuth PKCE Skill Extraction

## Status

Accepted

## Context

The Jobber API client implementation includes a production-tested OAuth 2.0 Authorization Code flow with PKCE (Proof Key for Code Exchange) and Doppler token storage. This pattern, implemented in `jobber_auth.py` and `jobber/auth.py`, is generic and reusable for any OAuth 2.0 provider supporting PKCE.

**Current Implementation:**

- `jobber_auth.py` (355 lines): One-time browser-based authorization
  - PKCE code verifier/challenge generation (SHA-256)
  - Temporary HTTP callback server (ports 3000-3010)
  - Token exchange with authorization code
  - Token persistence in Doppler secrets manager
- `jobber/auth.py` (355 lines): Token lifecycle management
  - Proactive refresh (background thread, 5min buffer)
  - Reactive refresh (on 401 errors)
  - Thread-safe token access
  - Doppler synchronization on refresh

**Problem:**
Future projects requiring OAuth authentication will need to reimplement this pattern or copy-paste code, risking:

- Security vulnerabilities from incomplete implementations
- Duplicated maintenance burden (bug fixes must propagate)
- Lost tribal knowledge (OAuth PKCE patterns are complex)
- Inconsistent token storage strategies across projects

**Opportunity:**
The OAuth PKCE + Doppler pattern is proven, secure, and API-agnostic. Only the authorization/token URLs and secret names are provider-specific. This makes it an ideal candidate for skill extraction.

## Decision

Extract the OAuth 2.0 PKCE authentication pattern into a reusable atomic skill at `skills/oauth-pkce-doppler/`.

**Skill Structure:**

```
skills/oauth-pkce-doppler/
├── SKILL.md                          # Hub: Quick start, when to use
├── assets/
│   ├── oauth_auth_template.py       # Parameterized jobber_auth.py
│   ├── token_manager_template.py    # Parameterized TokenManager
│   └── doppler_token_flow.sh        # Token verification script
├── references/
│   ├── security-considerations.md   # OAuth security, PKCE, tokens
│   ├── doppler-integration.md       # Doppler patterns, secret naming
│   ├── pkce-implementation.md       # PKCE technical details
│   ├── token-lifecycle.md           # Refresh strategies, threading
│   └── troubleshooting.md           # Common errors, debugging
└── examples/
    ├── basic_oauth_flow.py          # Minimal example
    ├── custom_callback_server.py    # Advanced patterns
    ├── error_handling_patterns.py   # Error scenarios
    └── README.md                    # Examples index
```

**Parameterization Strategy:**
Templates accept configuration for:

- OAuth endpoints (authorization URL, token URL)
- Doppler project/config
- Secret naming conventions (CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN, etc.)
- Port range for callback server
- PKCE settings (verifier length, challenge method)

**Documentation Strategy:**

- **SKILL.md**: Hub with quick start, triggers, progressive disclosure links
- **references/**: Deep-dive documentation (security, Doppler, PKCE, lifecycle, troubleshooting)
- **examples/**: Runnable code demonstrating basic → advanced patterns
- **assets/**: Production-ready templates and verification scripts

**Skill Location:**
Project-local (`skills/oauth-pkce-doppler/`) rather than global (`~/.claude/skills/`). Rationale:

- Jobber project proves the pattern works
- Future migration to global location possible after validation
- Keeps skill close to reference implementation (jobber_auth.py)

## Alternatives Considered

### Alternative 1: Keep OAuth pattern project-specific

**Approach:** Leave code in jobber_auth.py, document in README

**Pros:**

- No extraction effort required
- Code stays co-located with usage

**Cons:**

- Future projects must copy-paste or reinvent
- Security improvements don't propagate
- Lost opportunity for standardization

**Rejected:** Violates DRY principle and prevents knowledge reuse.

### Alternative 2: Create Python package (PyPI)

**Approach:** Package OAuth PKCE + Doppler as `oauth-pkce-doppler` library

**Pros:**

- Standard distribution mechanism
- Version management via pip/uv
- Can be used by non-AI-agent projects

**Cons:**

- Overhead of package management (releases, versioning)
- Less flexible than skill (harder to customize)
- Skill better suited for AI agent workflows

**Rejected:** Skill provides better flexibility for AI-driven customization.

### Alternative 3: Generic OAuth library (support all grant types)

**Approach:** Support Authorization Code, Client Credentials, Device Code, etc.

**Pros:**

- Covers all OAuth use cases
- More broadly reusable

**Cons:**

- Increased complexity (multiple grant types, multiple flows)
- Violates atomic skill principle
- Harder to maintain and document

**Rejected:** Atomic skills (one pattern each) preferred for clarity and maintainability.

## Consequences

### Positive

**Maintainability:**

- Single source of truth for OAuth PKCE + Doppler pattern
- Bug fixes and security improvements propagate to all users
- Reduces code duplication across projects

**Correctness:**

- Production-tested implementation becomes canonical
- Security best practices (PKCE, state validation, token rotation) documented
- Type-safe templates reduce integration errors

**Observability:**

- Comprehensive troubleshooting documentation
- Verification scripts for debugging token flows
- Clear error messages with resolution steps

**Reusability:**

- Applicable to any OAuth 2.0 provider (GitHub, Google, Stripe, etc.)
- Parameterized templates adapt to different secret naming conventions
- Examples demonstrate integration patterns

**Knowledge Preservation:**

- OAuth PKCE patterns codified in skill documentation
- Security considerations explicitly documented
- Tribal knowledge becomes organizational knowledge

### Negative

**Maintenance Burden:**

- Skill must be maintained alongside Jobber client
- Updates to OAuth standards (RFC changes) require skill updates
- Documentation must stay synchronized with implementation

**Abstraction Cost:**

- Templates add indirection vs. direct implementation
- Developers must understand parameterization strategy
- Customization requires modifying templates

**Validation Overhead:**

- Skill must be validated across multiple OAuth providers
- Template parameters must be tested for correctness
- Documentation must cover edge cases

### Mitigation Strategies

**Maintenance:**

- Link skill to jobber_auth.py as reference implementation
- Use semantic versioning if skill moves to global location
- Automate skill validation with tests

**Abstraction:**

- Provide runnable examples for common providers (Jobber, GitHub, Google)
- Inline comments explain template parameters
- SKILL.md includes Quick Start for copy-paste usage

**Validation:**

- Include verification scripts (doppler_token_flow.sh)
- Document troubleshooting for common errors
- Test templates with at least 2 OAuth providers (Jobber + GitHub)

## Related Decisions

- **ADR-0001**: Jobber API Client Architecture - Established fail-fast error handling and Doppler token storage patterns that this skill codifies
- **Future ADR**: Global skill migration - Decision to move skill to `~/.claude/skills/` after validation with multiple OAuth providers

## References

- OAuth 2.0 RFC 6749: https://tools.ietf.org/html/rfc6749
- PKCE RFC 7636: https://tools.ietf.org/html/rfc7636
- Doppler CLI Documentation: https://docs.doppler.com/docs/cli
- Jobber OAuth Implementation: `jobber_auth.py` (reference implementation)
- Skill Architecture Patterns: `~/.claude/skills/skill-architecture/`
- Documentation Standards: `~/.claude/skills/documentation-standards/`
