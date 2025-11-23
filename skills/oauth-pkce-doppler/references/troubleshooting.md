# Troubleshooting OAuth PKCE + Doppler

Common errors, debugging techniques, and resolution steps.

## Common Errors

### Error: "Doppler CLI not found"

**Symptom:**
```
RuntimeError: Doppler CLI failed: [Errno 2] No such file or directory: 'doppler'
```

**Diagnosis:**
```bash
which doppler
# Output: (empty) → Not installed
```

**Resolution:**
```bash
# macOS
brew install dopplerhq/cli/doppler

# Linux (Debian/Ubuntu)
curl -sLf https://packages.doppler.com/public/cli/install.sh | sudo bash

# Verify
doppler --version
```

**Reference:** [Doppler Installation](https://docs.doppler.com/docs/install-cli)

---

### Error: "No available ports in range 3000-3010"

**Symptom:**
```
RuntimeError: No available ports in range 3000-3010. Close applications using these ports or specify different range.
```

**Diagnosis:**
```bash
# Check which ports are in use
lsof -i :3000-3010

# Or check specific port
lsof -i :3000
```

**Resolution Option 1: Close conflicting applications**
```bash
# Find process using port
lsof -ti :3000

# Kill process
kill $(lsof -ti :3000)
```

**Resolution Option 2: Change port range**
```python
# In oauth_auth_template.py, change:
PORT_RANGE = range(8000, 8011)  # Use different range
```

---

### Error: "Expected 2 lines from Doppler, got 0"

**Symptom:**
```
RuntimeError: Expected 2 lines from Doppler, got 0. Ensure JOBBER_CLIENT_ID and JOBBER_CLIENT_SECRET exist.
```

**Diagnosis:**
```bash
# List all secrets
doppler secrets --project claude-config --config dev

# Check specific secret
doppler secrets get JOBBER_CLIENT_ID --project claude-config --config dev --plain
```

**Resolution:**
```bash
# Create missing secrets
doppler secrets set JOBBER_CLIENT_ID --project claude-config --config dev
# Paste value when prompted

doppler secrets set JOBBER_CLIENT_SECRET --project claude-config --config dev
# Paste value when prompted

# Verify
doppler secrets get JOBBER_CLIENT_ID JOBBER_CLIENT_SECRET --project claude-config --config dev --plain
```

---

### Error: "Authorization failed: access_denied"

**Symptom:**
```
AuthorizationError: Authorization failed: access_denied
```

**Cause:** User clicked "Deny" in browser authorization page

**Resolution:**
1. Re-run authorization script: `uv run oauth_auth.py`
2. Click "Approve" when prompted in browser
3. Ensure correct OAuth app permissions configured

---

### Error: "No authorization code received in callback"

**Symptom:**
```
AuthorizationError: No authorization code received in callback
```

**Possible Causes:**
1. Browser didn't navigate to callback URL
2. Callback URL mismatch (registered vs. actual)
3. Network connectivity issue
4. Firewall blocking localhost connections

**Diagnosis:**
```bash
# Check browser console for errors
# Check if callback URL matches registered redirect URI

# Test localhost connectivity
curl http://localhost:3000/callback
```

**Resolution:**
1. Verify redirect URI in OAuth app settings matches `http://localhost:{PORT}/callback`
2. Check firewall allows localhost connections
3. Try different browser
4. Manually paste callback URL if browser doesn't auto-redirect

---

### Error: "Token exchange failed: 400 Bad Request"

**Symptom:**
```
requests.HTTPError: 400 Client Error: Bad Request
```

**Possible Causes:**
1. Invalid authorization code (expired, already used)
2. Redirect URI mismatch
3. PKCE validation failed
4. Invalid client credentials

**Diagnosis:**
```bash
# Check error response body
python -c "
import requests
response = requests.post('TOKEN_URL', data={...})
print(response.status_code)
print(response.json())
"
```

**Resolution:**

**Code expired:**
- Authorization codes expire quickly (5-10 minutes)
- Restart authorization flow: `uv run oauth_auth.py`

**Redirect URI mismatch:**
```python
# Ensure exact match
authorization_redirect_uri = "http://localhost:3000/callback"
token_request_redirect_uri = "http://localhost:3000/callback"  # Must match exactly
```

**PKCE validation failed:**
- Verify `code_verifier` and `code_challenge` generated correctly
- Check S256 method used (not plain)
- Ensure verifier sent with token request

**Invalid credentials:**
```bash
# Verify client credentials
doppler secrets get JOBBER_CLIENT_ID JOBBER_CLIENT_SECRET --plain

# Check against OAuth app settings
```

---

### Error: "Token refresh failed: 401 Unauthorized"

**Symptom:**
```
AuthenticationError: Token refresh failed: 401 Unauthorized
```

**Possible Causes:**
1. Refresh token expired or revoked
2. Invalid client credentials
3. OAuth app deleted or deactivated

**Diagnosis:**
```bash
# Check refresh token exists
doppler secrets get JOBBER_REFRESH_TOKEN --plain

# Check client credentials
doppler secrets get JOBBER_CLIENT_ID JOBBER_CLIENT_SECRET --plain

# Check OAuth app status in provider dashboard
```

**Resolution:**

**Refresh token revoked:**
- User revoked access in provider UI
- Re-run authorization: `uv run oauth_auth.py`

**Client credentials changed:**
- Update Doppler with new credentials
- Re-run authorization

---

### Error: "Token EXPIRED (300 seconds ago)"

**Symptom (from doppler_token_flow.sh):**
```
[2025-01-17] ✗ Token EXPIRED (300 seconds ago)
[2025-01-17]   Run authorization script to re-authenticate
```

**Cause:** Access token expired, automatic refresh not running

**Resolution:**
```bash
# Re-run authorization to get fresh tokens
uv run oauth_auth.py

# Or manually trigger refresh if TokenManager running
# TokenManager will auto-refresh on next get_token() call
```

---

### Error: "Failed to save JOBBER_ACCESS_TOKEN to Doppler"

**Symptom:**
```
RuntimeError: Failed to save JOBBER_ACCESS_TOKEN to Doppler: permission denied
```

**Possible Causes:**
1. Insufficient Doppler permissions
2. Read-only config
3. Network connectivity issue

**Diagnosis:**
```bash
# Check Doppler authentication
doppler configure get token

# Try manual write
doppler secrets set TEST_SECRET --project claude-config --config dev
```

**Resolution:**

**Permission issue:**
- Use service token with write permissions
- Re-authenticate: `doppler login`

**Read-only config:**
- Use correct config (dev not prod)
- Check config permissions in Doppler dashboard

---

### Error: "State parameter mismatch"

**Symptom:**
```
AuthorizationError: State parameter mismatch (potential CSRF attack)
```

**Cause:** OAuth state validation failed

**Diagnosis:**
- Check if browser preserves state through redirect
- Verify no proxy/firewall modifying callback URL

**Resolution:**
- Restart authorization flow
- If persistent, check network proxy settings
- Ensure cookies enabled in browser

---

## Debugging Techniques

### Enable Detailed Logging

```python
import logging

# Add to top of script
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# In oauth_auth_template.py
logger.debug(f"Authorization URL: {auth_url}")
logger.debug(f"Redirect URI: {redirect_uri}")
logger.debug(f"Code challenge: {code_challenge[:10]}...")
logger.debug(f"Received authorization code: {code[:10]}...")
```

### Test OAuth Flow Manually

**1. Generate PKCE parameters:**
```bash
python3 -c "
import os, base64, hashlib
verifier = base64.urlsafe_b64encode(os.urandom(40)).decode().rstrip('=')
challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
print(f'Verifier: {verifier}')
print(f'Challenge: {challenge}')
" | tee pkce.txt
```

**2. Build authorization URL manually:**
```
https://api.example.com/oauth/authorize?
  client_id=YOUR_CLIENT_ID&
  redirect_uri=http://localhost:3000/callback&
  response_type=code&
  code_challenge=CHALLENGE_FROM_ABOVE&
  code_challenge_method=S256
```

**3. Open in browser, approve, capture code from URL**

**4. Exchange code manually:**
```bash
curl -X POST https://api.example.com/oauth/token \
  -d "grant_type=authorization_code" \
  -d "code=AUTHORIZATION_CODE" \
  -d "redirect_uri=http://localhost:3000/callback" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "code_verifier=VERIFIER_FROM_ABOVE"
```

### Verify Doppler Integration

```bash
# Run verification script
./doppler_token_flow.sh JOBBER claude-config dev

# Manual checks
doppler secrets get JOBBER_CLIENT_ID JOBBER_CLIENT_SECRET JOBBER_ACCESS_TOKEN JOBBER_REFRESH_TOKEN JOBBER_TOKEN_EXPIRES_AT \
  --project claude-config --config dev --plain

# Test token injection
doppler run --project claude-config --config dev \
  --command='echo Access token length: ${#JOBBER_ACCESS_TOKEN}'
```

### Check Token Format

**Access token should be:**
- Non-empty string
- Base64 or JWT format
- Typically 50-200 characters

**Refresh token should be:**
- Non-empty string
- Different from access token
- Typically 30-100 characters

**Expires_at should be:**
- Unix timestamp (integer)
- Future time (> current time)
- Example: 1640003600

```bash
# Check format
token=$(doppler secrets get JOBBER_ACCESS_TOKEN --plain)
echo "Length: ${#token}"
echo "First 10 chars: ${token:0:10}"

expires_at=$(doppler secrets get JOBBER_TOKEN_EXPIRES_AT --plain)
now=$(date +%s)
remaining=$((expires_at - now))
echo "Expires in: $((remaining / 60)) minutes"
```

## Verification Checklist

Before reporting issues:

- [ ] Doppler CLI installed and authenticated
- [ ] OAuth app created in provider dashboard
- [ ] Client ID and secret stored in Doppler
- [ ] Redirect URI registered matches script (`http://localhost:XXXX/callback`)
- [ ] Ports 3000-3010 available (or custom range configured)
- [ ] Browser can open authorization URL
- [ ] Network connectivity to OAuth provider
- [ ] Firewall allows localhost connections
- [ ] PKCE supported by provider (check docs)
- [ ] Scopes configured if required by provider

## Advanced Debugging

### Packet Capture

```bash
# Capture OAuth traffic (macOS/Linux)
sudo tcpdump -i any -w oauth.pcap port 443

# Analyze with Wireshark
wireshark oauth.pcap
```

### HTTP Proxy for Debugging

```bash
# Use mitmproxy to inspect OAuth requests
mitmproxy --mode regular --listen-port 8080

# Configure script to use proxy
export HTTP_PROXY=http://localhost:8080
export HTTPS_PROXY=http://localhost:8080
uv run oauth_auth.py
```

### Python Debugger

```python
# Add breakpoint in oauth_auth_template.py
import pdb; pdb.set_trace()

# Run script
uv run oauth_auth.py

# Debugger commands:
# (Pdb) print(code_verifier)
# (Pdb) print(code_challenge)
# (Pdb) continue
```

## Getting Help

**Information to include in bug reports:**
1. Full error message and stack trace
2. OAuth provider (Jobber, GitHub, Google, etc.)
3. Python version: `python3 --version`
4. Doppler CLI version: `doppler --version`
5. Operating system: `uname -a`
6. Verification script output: `./doppler_token_flow.sh`
7. Anonymized configuration (no secrets!)

**Reference Implementation:**
- Production code: `/Users/terryli/own/jobber/jobber_auth.py`
- Token manager: `/Users/terryli/own/jobber/jobber/auth.py`

## References

- **OAuth 2.0 RFC 6749**: https://tools.ietf.org/html/rfc6749
- **PKCE RFC 7636**: https://tools.ietf.org/html/rfc7636
- **Doppler Troubleshooting**: https://docs.doppler.com/docs/troubleshooting
