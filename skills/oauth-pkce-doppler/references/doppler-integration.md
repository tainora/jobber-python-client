# Doppler Integration Patterns

Doppler CLI setup, secret naming conventions, reading/writing patterns, and verification workflows.

## Doppler CLI Setup

### Installation

**macOS (Homebrew):**
```bash
brew install dopplerhq/cli/doppler
```

**Linux:**
```bash
# Debian/Ubuntu
sudo apt-get update && sudo apt-get install -y apt-transport-https ca-certificates curl gnupg
curl -sLf --retry 3 --tlsv1.2 --proto "=https" 'https://packages.doppler.com/public/cli/gpg.DE2A7741A397C129.key' | sudo apt-key add -
echo "deb https://packages.doppler.com/public/cli/deb/debian any-version main" | sudo tee /etc/apt/sources.list.d/doppler-cli.list
sudo apt-get update && sudo apt-get install doppler

# RHEL/CentOS
sudo rpm --import 'https://packages.doppler.com/public/cli/gpg.DE2A7741A397C129.key'
curl -sLf --retry 3 --tlsv1.2 --proto "=https" 'https://packages.doppler.com/public/cli/config.rpm.txt' | sudo tee /etc/yum.repos.d/doppler-cli.repo
sudo yum update && sudo yum install doppler
```

**Verify Installation:**
```bash
doppler --version
# Expected: 3.x.x
```

### Authentication

```bash
# Login (opens browser)
doppler login

# Or use service token (CI/CD)
export DOPPLER_TOKEN="dp.st.xxxx"
```

### Project Setup

```bash
# List projects
doppler projects list

# Create project
doppler projects create your-project

# List configs
doppler configs list --project your-project

# Create config
doppler configs create dev --project your-project
```

## Secret Naming Conventions

Follow consistent naming for easy maintenance and automation.

### Standard Pattern

```
{SERVICE_PREFIX}{SECRET_TYPE}
```

**Examples:**
- `JOBBER_CLIENT_ID` - OAuth client ID
- `JOBBER_CLIENT_SECRET` - OAuth client secret
- `JOBBER_ACCESS_TOKEN` - Current access token
- `JOBBER_REFRESH_TOKEN` - Current refresh token
- `JOBBER_TOKEN_EXPIRES_AT` - Unix timestamp expiration

### Service Prefixes

Use uppercase service name + underscore:
- `JOBBER_` - Jobber API
- `GITHUB_` - GitHub API
- `GOOGLE_` - Google APIs
- `STRIPE_` - Stripe API

### Secret Types

**OAuth Credentials:**
- `CLIENT_ID` - OAuth application client ID
- `CLIENT_SECRET` - OAuth application client secret

**OAuth Tokens:**
- `ACCESS_TOKEN` - Short-lived access token
- `REFRESH_TOKEN` - Long-lived refresh token
- `TOKEN_EXPIRES_AT` - Unix timestamp (integer as string)

### Multi-Environment Strategy

**Config-based separation:**
```
your-project/
├── dev/
│   ├── JOBBER_CLIENT_ID (dev app)
│   ├── JOBBER_CLIENT_SECRET
│   └── JOBBER_ACCESS_TOKEN
├── staging/
│   ├── JOBBER_CLIENT_ID (staging app)
│   ├── JOBBER_CLIENT_SECRET
│   └── JOBBER_ACCESS_TOKEN
└── prod/
    ├── JOBBER_CLIENT_ID (prod app)
    ├── JOBBER_CLIENT_SECRET
    └── JOBBER_ACCESS_TOKEN
```

**Usage:**
```bash
# Dev
doppler run --project your-project --config dev -- python app.py

# Prod
doppler run --project your-project --config prod -- python app.py
```

## Reading Secrets

### Single Secret

```bash
doppler secrets get SECRET_NAME \
  --project your-project \
  --config dev \
  --plain
```

**Flags:**
- `--plain`: Output value only (no JSON wrapping)
- `--project`: Doppler project name
- `--config`: Config name (dev/staging/prod)

### Multiple Secrets

```bash
doppler secrets get SECRET1 SECRET2 SECRET3 \
  --project your-project \
  --config dev \
  --plain
```

**Output:**
```
value1
value2
value3
```

One secret per line in order requested.

### From Python

```python
import subprocess

def load_from_doppler(
    secret_names: list[str],
    project: str,
    config: str
) -> dict[str, str]:
    """Load multiple secrets from Doppler."""
    result = subprocess.run(
        ['doppler', 'secrets', 'get'] + secret_names +
        ['--project', project, '--config', config, '--plain'],
        capture_output=True,
        text=True,
        check=True,
        timeout=10
    )

    lines = result.stdout.strip().split('\n')
    return dict(zip(secret_names, lines))

# Usage
secrets = load_from_doppler(
    ['JOBBER_CLIENT_ID', 'JOBBER_CLIENT_SECRET'],
    'claude-config',
    'dev'
)
client_id = secrets['JOBBER_CLIENT_ID']
```

## Writing Secrets

### Secure Input via Stdin

**Recommended** - Secret never visible in process list:
```bash
echo -n 'secret_value' | doppler secrets set SECRET_NAME \
  --project your-project \
  --config dev \
  --silent
```

**From Python:**
```python
subprocess.run(
    ['doppler', 'secrets', 'set', 'SECRET_NAME',
     '--project', project, '--config', config, '--silent'],
    input='secret_value',
    text=True,
    check=True,
    capture_output=True,
    timeout=10
)
```

### Interactive Input

**Prompts for value** (not visible in terminal):
```bash
doppler secrets set SECRET_NAME \
  --project your-project \
  --config dev
# Prompts: Enter SECRET_NAME:
```

### From File

```bash
cat secret.txt | doppler secrets set SECRET_NAME \
  --project your-project \
  --config dev \
  --silent
```

### Bulk Updates

```bash
# Update multiple secrets from JSON
echo '{"SECRET1":"value1","SECRET2":"value2"}' | \
  doppler secrets upload \
  --project your-project \
  --config dev
```

## Verification Workflows

### 4-Step Verification

**Step 1: Check Secret Existence**
```bash
doppler secrets get JOBBER_ACCESS_TOKEN \
  --project claude-config \
  --config dev \
  --plain >/dev/null 2>&1
echo $?  # 0 = exists, 1 = missing
```

**Step 2: Verify Secret Format**
```bash
# Check token is non-empty
token=$(doppler secrets get JOBBER_ACCESS_TOKEN --project X --config Y --plain)
if [ -n "$token" ]; then
    echo "Token exists (length: ${#token})"
else
    echo "Token empty or missing"
fi
```

**Step 3: Test Secret Injection**
```bash
# Verify environment variable injection works
doppler run --project claude-config --config dev \
  --command='echo Token length: ${#JOBBER_ACCESS_TOKEN}'

# Expected output: "Token length: 89" (or similar non-zero)
```

**Step 4: Validate Secret Usage**
```bash
# Test actual API call with token
doppler run --project claude-config --config dev \
  --command='python test_api.py'
```

### Display vs Actual Values

**Never log actual values:**
```bash
# ❌ Bad: Exposes token
echo "Token: $(doppler secrets get TOKEN --plain)"

# ✅ Good: Shows metadata only
token=$(doppler secrets get TOKEN --plain)
echo "Token length: ${#token} chars"
echo "Token prefix: ${token:0:8}..."
```

**From Python:**
```python
# ❌ Bad
print(f"Access token: {access_token}")

# ✅ Good
print(f"Access token: {access_token[:8]}... (length: {len(access_token)})")
```

### Automated Verification Script

See `/Users/terryli/own/jobber/skills/oauth-pkce-doppler/assets/doppler_token_flow.sh`

```bash
./doppler_token_flow.sh JOBBER claude-config dev
```

**Output:**
```
[2025-01-17 10:00:00] Verifying OAuth token flow for JOBBER
[2025-01-17 10:00:00] Doppler: project=claude-config config=dev

[2025-01-17 10:00:00] ✓ Doppler CLI found

[2025-01-17 10:00:00] Checking client credentials...
[2025-01-17 10:00:00] ✓ JOBBER_CLIENT_ID exists
[2025-01-17 10:00:00] ✓ JOBBER_CLIENT_SECRET exists
[2025-01-17 10:00:00]   Client ID length: 32 chars

[2025-01-17 10:00:00] Checking tokens...
[2025-01-17 10:00:00] ✓ JOBBER_ACCESS_TOKEN exists
[2025-01-17 10:00:00] ✓ JOBBER_REFRESH_TOKEN exists
[2025-01-17 10:00:00] ✓ JOBBER_TOKEN_EXPIRES_AT exists
[2025-01-17 10:00:00]   Access token length: 89 chars
[2025-01-17 10:00:00]   Refresh token length: 43 chars

[2025-01-17 10:00:00] Checking token expiration...
[2025-01-17 10:00:00] ✓ Token valid (45 minutes remaining)
[2025-01-17 10:00:00]   Expires at: 2025-01-17 10:45:00

[2025-01-17 10:00:00] Testing token injection...
[2025-01-17 10:00:00] ✓ Token injection works (length: 89 chars)

[2025-01-17 10:00:00] Verification complete!
```

## Best Practices

### Secret Organization

**Group related secrets:**
```
SERVICE_CLIENT_ID
SERVICE_CLIENT_SECRET
SERVICE_ACCESS_TOKEN
SERVICE_REFRESH_TOKEN
SERVICE_TOKEN_EXPIRES_AT
SERVICE_WEBHOOK_SECRET
SERVICE_API_KEY
```

**Use consistent prefixes:**
- OAuth providers: `GITHUB_`, `GOOGLE_`, `STRIPE_`
- Databases: `POSTGRES_`, `REDIS_`, `MONGODB_`
- Services: `SENDGRID_`, `TWILIO_`, `SLACK_`

### Access Control

**Principle of least privilege:**
```bash
# Developer access (read-only in prod)
doppler configs tokens create dev --config dev --max-age 30d

# CI/CD access (read-only, specific config)
doppler configs tokens create ci --config prod --max-age 0

# Service access (read-only, service tokens)
doppler service-tokens create api-service --config prod
```

### Audit Logging

**Review access logs:**
```bash
doppler activity
```

**Filter by secret:**
```bash
doppler activity --secret JOBBER_ACCESS_TOKEN
```

**Monitor changes:**
```bash
# Set up Doppler webhooks for change notifications
# https://docs.doppler.com/docs/webhooks
```

### Rotation Workflow

**Regular token rotation:**
```bash
# 1. Run auth script to get new tokens
uv run oauth_auth.py

# 2. Verify new tokens work
./doppler_token_flow.sh JOBBER claude-config dev

# 3. Monitor for errors (24-48 hours)
tail -f /var/log/app.log | grep "401\|Authentication"

# 4. Old tokens auto-replaced by auth script
```

## Common Issues

### Issue: "Doppler CLI not found"

**Diagnosis:**
```bash
which doppler  # Should show: /usr/local/bin/doppler
```

**Fix:**
```bash
# Install Doppler CLI
brew install dopplerhq/cli/doppler
```

### Issue: "Failed to authenticate with Doppler"

**Diagnosis:**
```bash
doppler configure get token  # Should show: dp.sa.xxxx or dp.st.xxxx
```

**Fix:**
```bash
doppler login  # Re-authenticate
```

### Issue: "Secret not found"

**Diagnosis:**
```bash
# List all secrets
doppler secrets --project your-project --config dev

# Check exact secret name
doppler secrets get SERVICE_CLIENT_ID --plain
```

**Fix:**
```bash
# Create missing secret
doppler secrets set SERVICE_CLIENT_ID --project your-project --config dev
```

### Issue: "Timeout fetching secrets"

**Diagnosis:**
```bash
time doppler secrets get TEST --plain
# Should complete in < 1 second
```

**Fix:**
```bash
# Check network connectivity
curl -I https://api.doppler.com

# Increase timeout in code
subprocess.run([...], timeout=30)  # Default 10s may be too short
```

## References

- **Doppler Documentation**: https://docs.doppler.com/docs
- **Doppler CLI Reference**: https://docs.doppler.com/docs/cli
- **Doppler Security**: https://docs.doppler.com/docs/security
