# OAuth PKCE Examples

Working implementations demonstrating OAuth 2.0 PKCE + Doppler integration patterns.

## Examples

### Basic OAuth Flow
**File**: [`basic_oauth_flow.py`](/Users/terryli/own/jobber/skills/oauth-pkce-doppler/examples/basic_oauth_flow.py)

Minimal working OAuth PKCE flow showing essential components.

**Demonstrates:**
- PKCE parameter generation
- Local callback server
- Token exchange
- Doppler storage

**Run:**
```bash
uv run basic_oauth_flow.py
```

---

### Custom Callback Server
**File**: [`custom_callback_server.py`](/Users/terryli/own/jobber/skills/oauth-pkce-doppler/examples/custom_callback_server.py)

Advanced callback server patterns with custom HTML, timeouts, and logging.

**Demonstrates:**
- Custom success/error HTML pages
- Server timeout handling
- Request logging
- State parameter validation

**Run:**
```bash
uv run custom_callback_server.py
```

---

### Error Handling Patterns
**File**: [`error_handling_patterns.py`](/Users/terryli/own/jobber/skills/oauth-pkce-doppler/examples/error_handling_patterns.py)

Comprehensive error handling for all failure scenarios.

**Demonstrates:**
- Doppler errors (CLI not found, secrets missing)
- Port availability errors
- Authorization errors (user denied, timeout)
- Token exchange errors (expired code, invalid credentials)
- Network errors (timeout, connection failure)

**Run:**
```bash
uv run error_handling_patterns.py
```

---

## Production Reference

**Jobber Implementation**: [`/Users/terryli/own/jobber/jobber_auth.py`](/Users/terryli/own/jobber/jobber_auth.py)

Production-tested OAuth flow for Jobber API. All examples based on this reference implementation.

## Customization

To adapt examples for your OAuth provider:

1. Update configuration section:
```python
AUTH_URL = "https://your-provider.com/oauth/authorize"
TOKEN_URL = "https://your-provider.com/oauth/token"
SERVICE_PREFIX = "YOUR_SERVICE_"
DOPPLER_PROJECT = "your-project"
DOPPLER_CONFIG = "dev"
```

2. Add scopes if required:
```python
SCOPES = ["repo", "user"]  # GitHub example
```

3. Run example:
```bash
uv run example.py
```

## Common Patterns

### Pattern 1: One-Time Authentication
Use `basic_oauth_flow.py` or `oauth_auth_template.py` for initial authorization.

### Pattern 2: Token Refresh
Use `TokenManager` from `token_manager_template.py` for automatic refresh in long-running applications.

### Pattern 3: Error Recovery
Use patterns from `error_handling_patterns.py` to handle failures gracefully.

## Testing

**Prerequisites:**
- Doppler CLI installed and configured
- OAuth app created in provider dashboard
- Client credentials stored in Doppler

**Verification:**
```bash
# Check Doppler secrets exist
doppler secrets get SERVICE_CLIENT_ID SERVICE_CLIENT_SECRET --plain

# Run verification script
/Users/terryli/own/jobber/skills/oauth-pkce-doppler/assets/doppler_token_flow.sh SERVICE claude-config dev

# Run example
uv run basic_oauth_flow.py
```

## Troubleshooting

See [`references/troubleshooting.md`](/Users/terryli/own/jobber/skills/oauth-pkce-doppler/references/troubleshooting.md) for detailed debugging guidance.

**Quick fixes:**
- **Port in use**: Change `PORT_RANGE` in script
- **Doppler CLI not found**: `brew install dopplerhq/cli/doppler`
- **Secrets missing**: `doppler secrets set SERVICE_CLIENT_ID`
- **Authorization failed**: Click "Approve" in browser
