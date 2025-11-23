# OAuth Application Setup Guide

Step-by-step instructions for creating OAuth applications across common providers.

## What is an OAuth Application?

An OAuth application is a registered client in an OAuth provider's system. When you create an OAuth app, you receive credentials (Client ID and Client Secret) that your code uses to authenticate with the provider's API.

**Required before using this skill**: You must create an OAuth app in your provider's developer dashboard to obtain credentials.

## Why Create an OAuth App?

1. **Security**: OAuth apps isolate your integration from other apps
2. **Credentials**: Provides Client ID and Client Secret for authentication
3. **Permissions**: Define what scopes/permissions your app needs
4. **Redirect URIs**: Whitelist valid callback URLs (localhost for CLI tools)

## General Steps (All Providers)

Regardless of provider, the process follows this pattern:

1. **Access Developer Dashboard**
   - Log into provider account
   - Navigate to developer/API settings
   - Find "OAuth Apps" or "Applications" section

2. **Create New Application**
   - Click "New App" or "Register Application"
   - Provide application name (e.g., "My CLI Tool")
   - Set application type (Web Application or Desktop Application)

3. **Configure Redirect URI**
   - Add callback URL: `http://localhost:3000/callback`
   - Note: Port 3000 is default, change if using different PORT_RANGE

4. **Enable Required Scopes**
   - Select API permissions your app needs
   - Example: `read:user`, `write:data`, etc.

5. **Enable Authorization Code Grant**
   - Ensure "Authorization Code" grant type is enabled
   - Disable "Implicit" grant (not secure for PKCE)

6. **Record Credentials**
   - Copy Client ID (public identifier)
   - Copy Client Secret (keep secure, never commit to git)

## Provider-Specific Instructions

### Jobber API

**Dashboard**: https://developer.getjobber.com/

**Steps**:
1. Log into Jobber account
2. Navigate to Settings → Developers → API Applications
3. Click "Create Application"
4. Fill in:
   - **Name**: Your application name
   - **Redirect URI**: `http://localhost:3000/callback`
5. Click "Create"
6. Copy **Client ID** and **Client Secret** immediately

**Store in Doppler**:
```bash
doppler secrets set JOBBER_CLIENT_ID --project your-project --config dev
# Paste Client ID when prompted

doppler secrets set JOBBER_CLIENT_SECRET --project your-project --config dev
# Paste Client Secret when prompted
```

**Authorization URL**: `https://api.getjobber.com/api/oauth/authorize`
**Token URL**: `https://api.getjobber.com/api/oauth/token`

---

### GitHub API

**Dashboard**: https://github.com/settings/developers

**Steps**:
1. Log into GitHub
2. Navigate to Settings → Developer settings → OAuth Apps
3. Click "New OAuth App"
4. Fill in:
   - **Application name**: Your app name
   - **Homepage URL**: `http://localhost` (or your project URL)
   - **Authorization callback URL**: `http://localhost:3000/callback`
5. Click "Register application"
6. Click "Generate a new client secret"
7. Copy **Client ID** and **Client Secret**

**Store in Doppler**:
```bash
doppler secrets set GITHUB_CLIENT_ID --project your-project --config dev
doppler secrets set GITHUB_CLIENT_SECRET --project your-project --config dev
```

**Authorization URL**: `https://github.com/login/oauth/authorize`
**Token URL**: `https://github.com/login/oauth/access_token`

**Required Scopes**: Add `scope` parameter to authorization URL (e.g., `repo`, `user`)

---

### Google OAuth 2.0

**Dashboard**: https://console.cloud.google.com/apis/credentials

**Steps**:
1. Log into Google Cloud Console
2. Select or create a project
3. Navigate to APIs & Services → Credentials
4. Click "Create Credentials" → "OAuth client ID"
5. If prompted, configure OAuth consent screen first:
   - User Type: External (for public apps) or Internal (for G Suite)
   - Fill in app information
6. Back in credentials, select:
   - **Application type**: Desktop app (for CLI tools)
   - **Name**: Your application name
7. Click "Create"
8. Copy **Client ID** and **Client Secret**

**Store in Doppler**:
```bash
doppler secrets set GOOGLE_CLIENT_ID --project your-project --config dev
doppler secrets set GOOGLE_CLIENT_SECRET --project your-project --config dev
```

**Authorization URL**: `https://accounts.google.com/o/oauth2/v2/auth`
**Token URL**: `https://oauth2.googleapis.com/token`

**Required Scopes**: Add `scope` parameter with space-separated scopes (e.g., `https://www.googleapis.com/auth/userinfo.email`)

---

### Stripe

**Dashboard**: https://dashboard.stripe.com/settings/apps

**Steps**:
1. Log into Stripe Dashboard
2. Navigate to Developers → OAuth settings
3. Click "Add redirect URI"
4. Add: `http://localhost:3000/callback`
5. Client ID is visible on OAuth settings page
6. Click "Show" next to Client Secret to reveal it
7. Copy both values

**Store in Doppler**:
```bash
doppler secrets set STRIPE_CLIENT_ID --project your-project --config dev
doppler secrets set STRIPE_CLIENT_SECRET --project your-project --config dev
```

**Authorization URL**: `https://connect.stripe.com/oauth/authorize`
**Token URL**: `https://connect.stripe.com/oauth/token`

---

### Generic OAuth 2.0 Provider

If your provider isn't listed, find these values in their API documentation:

**Required Information**:
1. **Developer Dashboard URL**: Where to create OAuth apps
2. **Authorization Endpoint**: URL for user authorization
3. **Token Endpoint**: URL for token exchange
4. **Supported Grant Types**: Verify "Authorization Code" is supported
5. **PKCE Support**: Check if S256 or plain PKCE is supported

**Configuration Steps**:
1. Create OAuth app in provider dashboard
2. Set redirect URI to `http://localhost:3000/callback`
3. Enable Authorization Code grant type
4. Enable PKCE if available (improves security)
5. Record Client ID and Client Secret
6. Store in Doppler with provider-specific prefix

## Common Configuration Issues

### Redirect URI Mismatch

**Symptom**: "redirect_uri_mismatch" error during authorization

**Cause**: Redirect URI in code doesn't match registered URI

**Resolution**:
- Ensure exact match: `http://localhost:3000/callback`
- No trailing slash
- Correct port number (match PORT_RANGE in script)
- http (not https) for localhost

### Invalid Client Error

**Symptom**: "invalid_client" during token exchange

**Cause**: Incorrect Client ID or Client Secret

**Resolution**:
```bash
# Verify stored credentials
doppler secrets get SERVICE_CLIENT_ID SERVICE_CLIENT_SECRET --plain

# Compare with provider dashboard
# Re-set if mismatch
```

### Unsupported Grant Type

**Symptom**: "unsupported_grant_type" error

**Cause**: Authorization Code grant not enabled

**Resolution**:
- Check OAuth app settings in provider dashboard
- Enable "Authorization Code" grant type
- Disable "Implicit" grant (not compatible with PKCE)

### Missing Required Scopes

**Symptom**: Authorization succeeds but API calls fail with 403

**Cause**: OAuth app not granted required permissions

**Resolution**:
- Review provider API documentation for required scopes
- Update authorization URL with `scope` parameter
- Example (GitHub): `scope=repo user:email`
- Re-run authorization flow after updating scopes

## Verification

After creating OAuth app, verify configuration:

**1. Credentials exist in Doppler**:
```bash
doppler secrets get SERVICE_CLIENT_ID SERVICE_CLIENT_SECRET \
  --project your-project --config dev --plain
```

**2. Redirect URI matches code**:
```python
# In oauth_auth_template.py
CALLBACK_PORT = 3000  # Must match registered URI port
```

**3. Authorization URL accessible**:
```bash
# Test authorization endpoint responds
curl -I https://provider.com/oauth/authorize
# Should return 200 or 302
```

**4. Token URL accessible**:
```bash
# Test token endpoint responds
curl -I https://provider.com/oauth/token
# Should return 200 or 405 (method not allowed for GET)
```

## Next Steps

After creating OAuth app and storing credentials:

1. **Customize template**: Update `oauth_auth_template.py` with provider URLs
2. **Run authorization**: `uv run oauth_auth.py`
3. **Verify tokens stored**: Check Doppler for `SERVICE_ACCESS_TOKEN`
4. **Test API calls**: Use stored token to make API request

See [SKILL.md](/Users/terryli/own/jobber/skills/oauth-pkce-doppler/SKILL.md) for complete workflow.

## Security Best Practices

1. **Never commit credentials**: Client Secret must stay in Doppler
2. **Use environment-specific apps**: Separate OAuth apps for dev/staging/prod
3. **Rotate secrets regularly**: Generate new Client Secret periodically
4. **Minimize scopes**: Only request permissions your app needs
5. **Monitor usage**: Check OAuth app activity logs in provider dashboard

## Getting Help

If you encounter issues:

1. Check provider's OAuth documentation
2. Verify redirect URI configuration
3. Review [Troubleshooting](/Users/terryli/own/jobber/skills/oauth-pkce-doppler/references/troubleshooting.md)
4. Test with provider's OAuth playground (if available)
5. Contact provider support with:
   - OAuth app Client ID (safe to share)
   - Error messages (redact Client Secret)
   - Redirect URI configuration

## References

- **OAuth 2.0 RFC**: https://tools.ietf.org/html/rfc6749
- **OAuth App Security**: [security-considerations.md](/Users/terryli/own/jobber/skills/oauth-pkce-doppler/references/security-considerations.md)
- **Doppler Setup**: [doppler-integration.md](/Users/terryli/own/jobber/skills/oauth-pkce-doppler/references/doppler-integration.md)
