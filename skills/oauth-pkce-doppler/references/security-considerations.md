# Security Considerations for OAuth 2.0 PKCE

OAuth security model, PKCE requirements, token storage best practices, and attack prevention strategies.

## OAuth 2.0 Security Model

### Authorization Code Flow

The Authorization Code flow is designed for confidential clients (applications that can keep secrets secure). Key security features:

1. **Two-step process**: Authorization code → Access token
2. **Server-side token exchange**: Client secret never exposed to browser
3. **Short-lived authorization codes**: Typically 5-10 minutes expiration
4. **One-time use codes**: Authorization code invalidated after exchange

### Attack Vectors Without PKCE

**Authorization Code Interception Attack:**
1. Attacker intercepts authorization code (man-in-the-middle, malware, browser history)
2. Attacker exchanges code for tokens using stolen client credentials
3. Attacker gains full access to user's account

**Why this matters**: Mobile and CLI apps cannot keep client secrets truly secret (decompilation, memory inspection, network sniffing).

## PKCE (Proof Key for Code Exchange)

RFC 7636: https://tools.ietf.org/html/rfc7636

### How PKCE Works

**Setup Phase:**
1. Client generates `code_verifier`: 43-128 character random string
2. Client generates `code_challenge`: SHA-256 hash of verifier
3. Client stores verifier locally (never transmitted to server)

**Authorization Phase:**
1. Client sends `code_challenge` in authorization request
2. Server stores challenge with authorization code

**Token Exchange Phase:**
1. Client sends `code_verifier` with token request
2. Server computes SHA-256(verifier) and compares to stored challenge
3. If match, server issues tokens; otherwise rejects request

**Security Guarantee:**
- Interceptor has authorization code but NOT code_verifier
- Without verifier, cannot compute matching challenge
- Token exchange fails, attack prevented

### PKCE Implementation Details

**Code Verifier Requirements:**
- Length: 43-128 characters
- Character set: `[A-Za-z0-9_-]` (URL-safe base64)
- Randomness: Cryptographically secure (use `os.urandom()` not `random`)

**Code Challenge Methods:**
- `S256`: SHA-256 hash (recommended, required by this skill)
- `plain`: No hashing (deprecated, insecure, never use)

**Implementation in template:**
```python
code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8').rstrip('=')
challenge_bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()
code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')
```

## Token Storage Security

### Never Store Tokens In

❌ **Git repositories** - Public exposure, version history never truly deleted
❌ **Environment variables** - Visible in `ps`, logs, error messages, child processes
❌ **Code** - Hardcoded secrets = security breach, requires code changes to rotate
❌ **Plain text files** - Readable by any process, no access control, no audit trail
❌ **Browser localStorage** - XSS attacks can steal tokens

### Always Store Tokens In

✅ **Secrets Manager** (Doppler, AWS Secrets Manager, HashiCorp Vault)
- Encrypted at rest
- Access control (who can read/write)
- Audit logging (who accessed when)
- Versioning (rollback to previous tokens)
- Remote updates (change once, apply everywhere)

### Token Rotation

**Best Practices:**
- Rotate tokens when developer leaves team
- Rotate after suspected compromise
- Rotate periodically (e.g., every 90 days)
- Use short-lived access tokens (60 minutes typical)
- Long-lived refresh tokens (but revocable)

**Doppler Rotation:**
```bash
# Update tokens via auth script (recommended)
uv run oauth_auth.py

# Manual rotation (if needed)
doppler secrets set SERVICE_ACCESS_TOKEN --project X --config Y
```

## State Parameter (CSRF Protection)

### Attack Without State Parameter

**Cross-Site Request Forgery (CSRF) Attack:**
1. Attacker initiates OAuth flow, gets authorization URL
2. Attacker tricks victim into clicking URL
3. Victim approves, callback goes to attacker's app
4. Attacker's app receives tokens for victim's account
5. Attacker links victim's account to attacker's profile

### How State Prevents CSRF

1. Client generates random `state` value (e.g., UUID)
2. Client stores state (session, memory)
3. Client includes state in authorization URL
4. Server returns state in callback
5. Client validates returned state matches stored state
6. If mismatch, reject callback (CSRF detected)

**Implementation:**
```python
# oauthlib handles this automatically
client = WebApplicationClient(client_id)
auth_url = client.prepare_request_uri(...)  # state auto-generated
# Client stores state internally, validates on callback
```

## Redirect URI Security

### CLI Tools

**Requirements:**
- Use `http://localhost:{port}/callback` (never `127.0.0.1` due to some browser issues)
- Bind server to `127.0.0.1` (prevents network access)
- Use dynamic port selection (avoid conflicts)
- Never use wildcard URIs

**Security:**
- Localhost-only prevents remote attackers
- Dynamic port prevents port hijacking
- Exact URI match prevents redirect manipulation

**Implementation:**
```python
server = HTTPServer(('127.0.0.1', port), handler)  # Localhost only
redirect_uri = f"http://localhost:{port}/callback"  # Exact match required
```

### Web Applications

**Requirements:**
- HTTPS required (never HTTP)
- Exact domain match (no wildcards)
- Register all redirect URIs with provider

## Client Secret Handling

### Storage

**Doppler (Recommended):**
```bash
# Store during setup
doppler secrets set SERVICE_CLIENT_ID --project X --config Y
doppler secrets set SERVICE_CLIENT_SECRET --project X --config Y

# Load in code
client_id = doppler_get("SERVICE_CLIENT_ID")
client_secret = doppler_get("SERVICE_CLIENT_SECRET")
```

**Never:**
- Hardcode in source code
- Commit to git (even private repos)
- Log in error messages
- Pass as command-line arguments (visible in `ps`)

### Rotation

**When to Rotate:**
- Developer with access leaves team
- Secret accidentally exposed (git commit, logs, Slack)
- Suspected compromise
- Regular rotation schedule (e.g., quarterly)

**How to Rotate:**
1. Generate new secret in OAuth provider
2. Update Doppler with new secret
3. Test with new secret
4. Delete old secret from provider
5. Monitor for unauthorized access attempts

## Token Refresh Security

### Refresh Token Rotation

Some OAuth providers issue a new `refresh_token` on each refresh. This improves security:

**Benefits:**
- Limits damage if refresh token stolen (only works once)
- Detects token theft (old token stops working)
- Enables revocation tracking

**Implementation:**
```python
token_data = refresh_request()
access_token = token_data['access_token']
# Some providers return new refresh token, some don't
refresh_token = token_data.get('refresh_token', old_refresh_token)
```

### Refresh Timing

**Proactive Refresh (Background):**
- Refresh 5 minutes before expiry
- Prevents 401 errors during API calls
- Reduces user-visible disruption

**Reactive Refresh (On 401):**
- Retry once on authentication error
- Handles race conditions (token expired between check and use)
- Fallback if proactive refresh fails

**Security:**
- Both approaches valid
- Proactive reduces attack window (less time with expired token)
- Reactive handles edge cases

## Common Security Anti-Patterns

### ❌ Don't: Implement OAuth Without PKCE

**Why dangerous**: Authorization code interception attacks work

**Fix**: Always use PKCE with S256 challenge method

### ❌ Don't: Store Tokens in Git

**Why dangerous**: Public exposure, permanent history

**Fix**: Use Doppler or secrets manager

### ❌ Don't: Log Tokens

**Why dangerous**: Logs often less secured, retained longer, searchable

**Example of bad code:**
```python
logger.debug(f"Access token: {access_token}")  # NEVER DO THIS
```

**Fix:**
```python
logger.debug(f"Access token length: {len(access_token)}")  # Log metadata only
```

### ❌ Don't: Use HTTP for Redirect URIs (Web Apps)

**Why dangerous**: Man-in-the-middle can steal authorization code

**Fix**: Always use HTTPS (localhost HTTP is OK for CLI tools)

### ❌ Don't: Skip State Validation

**Why dangerous**: CSRF attacks allow account linking attacks

**Fix**: Validate state parameter on callback

### ❌ Don't: Use `plain` PKCE Method

**Why dangerous**: No protection against code interception

**Fix**: Always use `S256` (SHA-256 challenge)

## OAuth Provider Differences

### Jobber
- PKCE: Supported (S256)
- Scopes: Not used
- Token lifetime: 60 minutes (access), long-lived (refresh)
- Refresh token rotation: No

### GitHub
- PKCE: Supported (S256)
- Scopes: Required (e.g., `repo`, `user`)
- Token lifetime: 8 hours (access), 6 months (refresh)
- Refresh token rotation: Yes (new refresh token on each refresh)

### Google
- PKCE: Required for mobile/desktop apps
- Scopes: Required (e.g., `openid`, `email`)
- Token lifetime: 60 minutes (access), no expiration (refresh)
- Refresh token rotation: No (but can be revoked)

## Security Checklist

Before deploying OAuth implementation:

- [ ] PKCE enabled with S256 challenge method
- [ ] State parameter generated and validated
- [ ] Tokens stored in Doppler (never git, env vars, code)
- [ ] Client secret stored in Doppler
- [ ] Redirect URI exact match (no wildcards)
- [ ] Localhost-only callback server (127.0.0.1)
- [ ] HTTPS for all OAuth endpoints
- [ ] Token refresh implemented (proactive + reactive)
- [ ] Error handling raises exceptions (no silent failures)
- [ ] Logging excludes token values
- [ ] Rotation process documented
- [ ] Access control on Doppler project

## References

- **OAuth 2.0 RFC 6749**: https://tools.ietf.org/html/rfc6749
- **PKCE RFC 7636**: https://tools.ietf.org/html/rfc7636
- **OAuth 2.0 Security Best Practices**: https://tools.ietf.org/html/draft-ietf-oauth-security-topics
- **Doppler Security**: https://docs.doppler.com/docs/security
