# Jobber OAuth Token Guide

**Status**: Client credentials exist ✅, Access tokens missing ❌

---

## Current Token Status

### ✅ What You HAVE (Existing in Doppler)

```bash
$ doppler secrets --project claude-config --config dev | grep JOBBER
```

**Found**:

- `JOBBER_CLIENT_ID` = `f388123a-8dab-4e81-b07e-...` ✅
- `JOBBER_CLIENT_SECRET` = `a6db0828e4a6ba1d3c46d1b...` ✅
- `JOBBER_ACCOUNT_EMAIL` = `usalchemist@gmail.com` ✅
- `JOBBER_API_URL` = `https://api.getjobber.com` ✅
- `JOBBER_API_VERSION` = `2023-11-15` ✅
- `JOBBER_GRAPHQL_ENDPOINT` = `https://api.getjobber.com/api/graphql` ✅

**Interpretation**: You have OAuth app credentials from a previous session!

### ❌ What You NEED (Missing - These Expire)

```bash
$ doppler secrets get JOBBER_ACCESS_TOKEN --project claude-config --config dev
Error: Could not find requested secret: JOBBER_ACCESS_TOKEN
```

**Missing**:

- `JOBBER_ACCESS_TOKEN` - Short-lived token (expires after 60 minutes) ❌
- `JOBBER_REFRESH_TOKEN` - Long-lived token (used to get new access tokens) ❌
- `JOBBER_TOKEN_EXPIRES_AT` - Unix timestamp when access token expires ❌

**Why they're missing**:

1. Never ran the OAuth flow, OR
2. Tokens expired and were never refreshed

---

## How OAuth Tokens Work

### Token Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│ ONE-TIME SETUP (You already did this!)                      │
│                                                             │
│ 1. Created OAuth App in Jobber Developer Portal            │
│ 2. Got CLIENT_ID and CLIENT_SECRET                         │
│ 3. Stored in Doppler ✅                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ AUTHORIZATION FLOW (Need to do this now!)                   │
│                                                             │
│ 1. Run: uv run jobber_auth.py                              │
│ 2. Browser opens to Jobber authorization page              │
│ 3. You click "Authorize" to grant access                   │
│ 4. Script exchanges code for tokens                        │
│ 5. Tokens saved to Doppler:                                │
│    - JOBBER_ACCESS_TOKEN (60 min lifetime)                 │
│    - JOBBER_REFRESH_TOKEN (long-lived)                     │
│    - JOBBER_TOKEN_EXPIRES_AT (timestamp)                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ AUTOMATIC TOKEN REFRESH (Handled by library)                │
│                                                             │
│ - TokenManager checks expiration every 5 minutes            │
│ - Proactively refreshes 5 minutes before expiry            │
│ - Reactive refresh on 401 errors                           │
│ - New tokens auto-saved to Doppler                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step: Getting Your Tokens

### Step 1: Verify Client Credentials Exist

```bash
doppler secrets get JOBBER_CLIENT_ID JOBBER_CLIENT_SECRET \
  --project claude-config --config dev --plain
```

**Expected output**:

```
f388123a-8dab-4e81-b07e-...
a6db0828e4a6ba1d3c46d1b...
```

**Status**: ✅ You have these!

### Step 2: Run OAuth Authorization

```bash
cd /Users/terryli/own/jobber
uv run jobber_auth.py
```

**What happens**:

1. **Script starts**:

   ```
   === Jobber OAuth 2.0 Authorization ===

   Loading credentials from Doppler...
   ✅ Client ID: f388123a-8dab-4e81-b07e-...
   ✅ Client Secret: ******

   Starting callback server on port 3000...
   ✅ Server ready at http://127.0.0.1:3000
   ```

2. **Browser opens automatically** to:

   ```
   https://api.getjobber.com/api/oauth/authorize?
     response_type=code&
     client_id=f388123a-8dab-4e81-b07e-...&
     redirect_uri=http://127.0.0.1:3000&
     code_challenge=...&
     code_challenge_method=S256&
     state=...
   ```

3. **Jobber login page appears**:
   - Log in with: `usalchemist@gmail.com`
   - Enter your Jobber password
   - Click "Authorize" to grant access

4. **Browser redirects back to localhost**:

   ```
   http://127.0.0.1:3000?code=abc123...&state=...
   ```

5. **Script exchanges code for tokens**:

   ```
   ✅ Authorization code received

   Exchanging code for access token...
   ✅ Tokens received

   Storing tokens in Doppler...
   ✅ JOBBER_ACCESS_TOKEN stored
   ✅ JOBBER_REFRESH_TOKEN stored
   ✅ JOBBER_TOKEN_EXPIRES_AT stored

   === Authorization Complete ===
   You can now use the Jobber API!
   ```

6. **Browser shows success page**:
   ```
   Authorization Successful
   You can close this window and return to the terminal.
   ```

### Step 3: Verify Tokens Saved

```bash
doppler secrets get JOBBER_ACCESS_TOKEN JOBBER_REFRESH_TOKEN \
  --project claude-config --config dev --plain
```

**Expected output**:

```
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...  (access token)
def456ghi789...                          (refresh token)
```

---

## Troubleshooting

### Issue: "Browser doesn't open"

**Cause**: `webbrowser` module can't find default browser

**Solution**: Manually open the URL shown in terminal:

```
Opening browser to: https://api.getjobber.com/api/oauth/authorize?...
```

Copy/paste that URL into your browser.

### Issue: "Authorization failed - redirect_uri mismatch"

**Cause**: OAuth app in Jobber not configured with correct redirect URI

**Solution**: Update OAuth app in Jobber Developer Portal:

1. Go to https://developer.getjobber.com/
2. Select your app
3. Add redirect URI: `http://127.0.0.1:3000`
4. Save and try again

### Issue: "Port 3000 already in use"

**Cause**: Another application is using port 3000

**Solution**: Script automatically tries ports 3000-3010. If all busy:

```bash
# Check what's using the ports
lsof -i :3000-3010

# Kill the process or wait for script to find available port
```

### Issue: "Doppler CLI failed"

**Cause**: Doppler not configured for project/config

**Solution**:

```bash
# Check current Doppler setup
doppler setup

# Or specify project/config
doppler setup --project claude-config --config dev
```

---

## Token Expiration & Refresh

### Access Token Lifecycle

**Lifespan**: 60 minutes (3600 seconds)

**What happens when it expires**:

1. API returns 401 Unauthorized
2. `TokenManager` catches 401
3. Uses `JOBBER_REFRESH_TOKEN` to get new `ACCESS_TOKEN`
4. Retries original request
5. Saves new tokens to Doppler

**Proactive Refresh**:

- Background thread checks expiration every 5 minutes
- Refreshes 5 minutes BEFORE expiration
- Prevents 401 errors during API calls

### Refresh Token Lifecycle

**Lifespan**: Until revoked (no automatic expiration)

**When it gets revoked**:

- User revokes access in Jobber settings
- User deletes OAuth app
- User changes password (sometimes)

**What to do if revoked**:

- Run `uv run jobber_auth.py` again to re-authorize

---

## How the Script Works (Technical Details)

### PKCE (Proof Key for Code Exchange)

The script uses PKCE for enhanced security (even though Jobber doesn't require it for server-side apps).

**PKCE Flow**:

1. **Generate code_verifier** (random 40-byte string):

   ```python
   code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8')
   # Example: "XZ4r7Gp2mK9nLqW8tYvUb3cDe5fH6jI0oP1aS"
   ```

2. **Generate code_challenge** (SHA-256 hash):

   ```python
   challenge_bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()
   code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8')
   # Example: "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
   ```

3. **Send code_challenge in authorization URL**:

   ```
   GET https://api.getjobber.com/api/oauth/authorize?
     code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&
     code_challenge_method=S256
   ```

4. **Exchange code with code_verifier**:

   ```
   POST https://api.getjobber.com/api/oauth/token
   {
     "code": "abc123...",
     "code_verifier": "XZ4r7Gp2mK9nLqW8tYvUb3cDe5fH6jI0oP1aS",
     "client_id": "...",
     "client_secret": "...",
     "grant_type": "authorization_code"
   }
   ```

5. **Server verifies**: `SHA256(code_verifier) == code_challenge`

**Why PKCE?**: Prevents authorization code interception attacks

### Callback Server

**Purpose**: Receive authorization code from Jobber

**How it works**:

1. **Start HTTP server** on localhost:

   ```python
   server = HTTPServer(('127.0.0.1', 3000), OAuthCallbackHandler)
   ```

2. **Wait for single request**:

   ```python
   server.handle_request()  # Blocks until request received
   ```

3. **Extract authorization code** from query params:

   ```python
   # URL: http://127.0.0.1:3000?code=abc123&state=xyz
   code = query_params['code'][0]
   ```

4. **Respond to browser**:

   ```html
   <h1>Authorization Successful</h1>
   <script>
     window.close();
   </script>
   ```

5. **Shutdown server**:
   ```python
   server.shutdown()
   ```

### Token Storage in Doppler

**Why Doppler?**:

- Encrypted secret storage
- CLI access for scripts
- Environment-based configs (dev, prod)
- No tokens in source code

**How tokens are stored**:

```bash
# Access token (JWT format)
doppler secrets set JOBBER_ACCESS_TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..." \
  --project claude-config --config dev

# Refresh token (opaque string)
doppler secrets set JOBBER_REFRESH_TOKEN="def456ghi789..." \
  --project claude-config --config dev

# Expiration timestamp (Unix epoch)
doppler secrets set JOBBER_TOKEN_EXPIRES_AT="1700000000" \
  --project claude-config --config dev
```

---

## Next Steps

### 1. Run Authorization (Now!)

```bash
uv run jobber_auth.py
```

### 2. Test API Access

```bash
# Option A: List existing clients
uv run python list_existing_clients.py

# Option B: Create new client
uv run python test_create_client_url.py
```

### 3. Verify URL Clicking

After running Option A or B, **Cmd+Click** the URL to view in Jobber web interface.

---

## OAuth App Details

### Where OAuth App Was Created

**Jobber Developer Portal**: https://developer.getjobber.com/

**Your OAuth App**:

- Client ID: `f388123a-8dab-4e81-b07e-...`
- Redirect URI: `http://127.0.0.1:3000` (or similar)
- Scopes: Full API access (default)

**To view/edit your app**:

1. Go to https://developer.getjobber.com/
2. Log in with: `usalchemist@gmail.com`
3. Click "Apps" → Your app name
4. Review settings

---

## Security Best Practices

### ✅ What We Do Right

1. **PKCE** - Extra security layer
2. **Doppler** - Encrypted token storage
3. **Short-lived tokens** - 60-minute access tokens
4. **Auto-refresh** - Proactive token renewal
5. **No tokens in code** - All in Doppler
6. **HTTPS** - Secure API communication

### ⚠️ Additional Recommendations

1. **Rotate refresh tokens** - Periodically re-authorize
2. **Monitor token usage** - Check Doppler audit logs
3. **Revoke old tokens** - If not used
4. **2FA on Jobber account** - Extra security
5. **Limit OAuth scopes** - Only request needed permissions

---

## References

- **Jobber OAuth Documentation**: https://developer.getjobber.com/docs/building_your_app/app_authorization/
- **OAuth 2.0 RFC 6749**: https://tools.ietf.org/html/rfc6749
- **PKCE RFC 7636**: https://tools.ietf.org/html/rfc7636
- **Doppler CLI**: https://docs.doppler.com/docs/cli

---

## Summary

**What you have**: ✅ Client ID, Client Secret (OAuth app credentials)

**What you need**: ❌ Access Token, Refresh Token (user authorization)

**How to get them**: Run `uv run jobber_auth.py` → Authorize in browser → Tokens saved automatically

**Time required**: 2 minutes (one-time setup)

**After that**: API tests work, URLs are clickable, full functionality unlocked! 🚀
