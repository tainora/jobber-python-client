---
name: oauth-pkce-doppler
description: Implement OAuth 2.0 Authorization Code flow with PKCE security and Doppler token storage. Use when implementing OAuth authentication, integrating third-party APIs (Jobber, GitHub, Google), or building CLI tools requiring browser-based authorization with automatic token refresh.
---

# OAuth 2.0 PKCE with Doppler Integration

Implement production-tested OAuth 2.0 authorization flows with PKCE (Proof Key for Code Exchange) and secure token storage in Doppler secrets manager.

## Quick Start

### From Any Project

Use production-ready templates from `/Users/terryli/own/jobber/skills/oauth-pkce-doppler/assets/`:

```python
# Step 1: One-time authentication (user runs once)
# Adapt oauth_auth_template.py with your OAuth provider config
uv run oauth_auth.py

# Step 2: Automatic usage (AI agents, scripts)
# Adapt token_manager_template.py to your project
from your_project.auth import TokenManager

client = TokenManager.from_doppler(
    doppler_project="your-project",
    doppler_config="dev"
)
token = client.get_token()  # Auto-refreshes if needed
```

**Features**:
- ✅ PKCE security (S256 SHA-256 challenge method)
- ✅ Browser-based user authorization
- ✅ Automatic callback server (finds available port 3000-3010)
- ✅ Token storage in Doppler (encrypted, version-controlled)
- ✅ Proactive token refresh (background thread, 5min buffer)
- ✅ Reactive token refresh (on 401 errors)
- ✅ Thread-safe token access
- ✅ Fail-fast error handling with context

## Prerequisites

Before using this skill, ensure you have:

### Required

1. **OAuth Application**: Create OAuth app in provider's developer dashboard
   - See [OAuth App Setup Guide](/Users/terryli/own/jobber/skills/oauth-pkce-doppler/references/oauth-app-setup.md) for step-by-step instructions
   - Obtain Client ID and Client Secret
   - Configure redirect URI: `http://localhost:3000/callback`

2. **Doppler CLI**: Install and authenticate Doppler secrets manager
   ```bash
   # macOS
   brew install dopplerhq/cli/doppler

   # Linux
   curl -sLf https://packages.doppler.com/public/cli/install.sh | sudo bash

   # Authenticate
   doppler login
   ```

3. **Python 3.12+**: Required for modern syntax and PEP 723 support
   ```bash
   python3 --version  # Should be >= 3.12
   ```

4. **uv Package Manager**: For PEP 723 inline dependencies
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

### Environment

- **Browser**: Default browser for user authorization flow
- **Network**: Outbound HTTPS access to OAuth provider
- **Ports**: At least one available port in range 3000-3010 (configurable)
- **Localhost**: Firewall allows localhost connections

### Verification

Verify prerequisites before starting:

```bash
# Check Doppler CLI
doppler --version

# Check Python version
python3 --version

# Check uv installed
uv --version

# Check ports available
lsof -i :3000-3010  # Should show no processes
```

## When to Use This Skill

Use when implementing:
- OAuth 2.0 Authorization Code grant with PKCE
- Browser-based authentication for CLI tools
- Third-party API integrations (Jobber, GitHub, Google, Stripe, etc.)
- Secure token storage in Doppler secrets manager
- Automatic token refresh without user interaction
- AI agent-friendly authentication patterns

## Templates & Assets

### Production Templates

**[oauth_auth_template.py](/Users/terryli/own/jobber/skills/oauth-pkce-doppler/assets/oauth_auth_template.py)**
- Complete one-time browser authorization script
- Parameterized for any OAuth 2.0 provider
- Based on production Jobber implementation
- PEP 723 self-contained (inline dependencies)

**[token_manager_template.py](/Users/terryli/own/jobber/skills/oauth-pkce-doppler/assets/token_manager_template.py)**
- TokenManager class with automatic refresh
- Proactive (background thread) + reactive (on 401) refresh
- Thread-safe token access with locks
- Doppler synchronization

**[doppler_token_flow.sh](/Users/terryli/own/jobber/skills/oauth-pkce-doppler/assets/doppler_token_flow.sh)**
- Token verification and debugging script
- Checks credential existence
- Validates token format
- Estimates time until refresh needed

### Configuration Points

Templates require configuration for:
- **OAuth endpoints**: Authorization URL, token URL
- **Doppler project/config**: Where to store tokens
- **Secret naming**: `{SERVICE}_CLIENT_ID`, `{SERVICE}_ACCESS_TOKEN`, etc.
- **Port range**: Callback server port range (default 3000-3010)
- **PKCE settings**: Verifier length, challenge method (default S256)

## Reference Documentation

For detailed technical information, see:

- **[OAuth App Setup](/Users/terryli/own/jobber/skills/oauth-pkce-doppler/references/oauth-app-setup.md)** - **START HERE** - Create OAuth apps (Jobber, GitHub, Google, Stripe), obtain credentials, configure redirect URIs
- **[Security Considerations](/Users/terryli/own/jobber/skills/oauth-pkce-doppler/references/security-considerations.md)** - OAuth security model, PKCE requirements, token storage, state validation, redirect URI security
- **[Doppler Integration](/Users/terryli/own/jobber/skills/oauth-pkce-doppler/references/doppler-integration.md)** - Doppler CLI setup, secret naming conventions, verification workflows
- **[PKCE Implementation](/Users/terryli/own/jobber/skills/oauth-pkce-doppler/references/pkce-implementation.md)** - RFC 7636 technical details, code verifier/challenge generation, SHA-256 implementation
- **[Token Lifecycle](/Users/terryli/own/jobber/skills/oauth-pkce-doppler/references/token-lifecycle.md)** - Refresh strategies (proactive/reactive), threading patterns, concurrency handling
- **[Troubleshooting](/Users/terryli/own/jobber/skills/oauth-pkce-doppler/references/troubleshooting.md)** - Common errors, debugging techniques, verification scripts

## Examples

Working implementations demonstrating basic → advanced patterns:

- **[basic_oauth_flow.py](/Users/terryli/own/jobber/skills/oauth-pkce-doppler/examples/basic_oauth_flow.py)** - Minimal working OAuth PKCE flow
- **[custom_callback_server.py](/Users/terryli/own/jobber/skills/oauth-pkce-doppler/examples/custom_callback_server.py)** - Advanced callback server patterns
- **[error_handling_patterns.py](/Users/terryli/own/jobber/skills/oauth-pkce-doppler/examples/error_handling_patterns.py)** - Comprehensive error handling
- **[examples/README.md](/Users/terryli/own/jobber/skills/oauth-pkce-doppler/examples/README.md)** - Examples index and usage

**Reference Implementation**: [`/Users/terryli/own/jobber/jobber_auth.py`](/Users/terryli/own/jobber/jobber_auth.py) - Production Jobber OAuth implementation

## Workflow Pattern

This skill follows the **Workflow Pattern** (sequential multi-step procedure):

### Phase 1: Prerequisites
1. Verify Doppler CLI installed
2. Load client credentials from Doppler
3. Validate port range availability

### Phase 2: PKCE Generation
1. Generate code verifier (43-128 chars, cryptographically random)
2. Generate code challenge (SHA-256 hash of verifier)
3. Start local HTTP callback server

### Phase 3: Browser Authorization
1. Build authorization URL with PKCE parameters
2. Open user's browser to authorization page
3. Wait for callback with authorization code

### Phase 4: Token Exchange
1. Build token request payload (includes code_verifier)
2. POST to token endpoint
3. Parse access_token, refresh_token, expires_in

### Phase 5: Token Persistence
1. Calculate expiration timestamp
2. Store tokens in Doppler
3. Verify storage success

### Phase 6: Automatic Refresh (Ongoing)
- Proactive: Background thread refreshes 5min before expiry
- Reactive: Retry on 401 errors
- Update Doppler with new tokens

## Security Model

### PKCE (Proof Key for Code Exchange)
- Prevents authorization code interception attacks
- Code challenge sent in authorization request
- Code verifier proves client identity during token exchange
- Only client with verifier can exchange authorization code

### Token Storage
- Never store tokens in git, environment variables, or code
- Always use Doppler secrets manager (encrypted at rest)
- Access tokens expire (typically 60min)
- Refresh tokens long-lived (until revoked)

### State Parameter
- CSRF protection during OAuth flow
- Random state generated, validated on callback
- Prevents cross-site request forgery

### Redirect URI
- CLI tools use `http://localhost:{port}/callback`
- Localhost-only prevents network exposure
- Port dynamically selected from available range

## Dependencies

### Runtime Requirements
- Python >= 3.12
- `requests` >= 2.32.0 (HTTP client)
- `oauthlib` >= 3.2.2 (OAuth utilities)

### External Tools
- **Doppler CLI** (secrets management)
- **Browser** (user authorization flow)

### Standard Library
- `http.server` (callback server)
- `subprocess` (Doppler CLI interaction)
- `webbrowser` (browser automation)
- `hashlib`, `base64`, `os` (PKCE generation)

## Error Handling

All errors raise exceptions immediately (fail-fast). Caller decides recovery strategy.

**Common exceptions**:
- `ConfigurationError`: Doppler secrets not found, CLI not installed
- `AuthorizationError`: User denied, callback timeout, invalid code
- `TokenExchangeError`: Invalid credentials, expired code, PKCE validation failed
- `NetworkError`: Connection timeout, Doppler CLI failure

See [Troubleshooting](/Users/terryli/own/jobber/skills/oauth-pkce-doppler/references/troubleshooting.md) for resolution steps.

## Related Patterns

- **Credentials Management**: Doppler workflows for secret storage
- **Documentation Standards**: Hub-and-spoke progressive disclosure
- **Fail-Fast Architecture**: Error propagation without retry/fallback

## References

- **OAuth 2.0 RFC 6749**: https://tools.ietf.org/html/rfc6749
- **PKCE RFC 7636**: https://tools.ietf.org/html/rfc7636
- **Doppler Documentation**: https://docs.doppler.com/docs
- **ADR-0002**: [OAuth PKCE Skill Extraction](/Users/terryli/own/jobber/docs/decisions/0002-oauth-pkce-skill-extraction.md)
