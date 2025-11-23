# PKCE Implementation Details

RFC 7636 technical specification, code verifier/challenge generation, and implementation patterns.

## PKCE Specification (RFC 7636)

**Full Specification**: https://tools.ietf.org/html/rfc7636

**Purpose**: Prevent authorization code interception attacks for public clients (mobile apps, CLI tools, SPAs).

**Method**: Cryptographic proof that the client exchanging the authorization code is the same client that requested it.

## Code Verifier Generation

### Requirements

**Length**: 43-128 characters (RFC 7636 Section 4.1)

**Character Set**: `[A-Za-z0-9._~-]` (unreserved characters per RFC 3986)
- Uppercase: `A-Z`
- Lowercase: `a-z`
- Digits: `0-9`
- Unreserved symbols: `.` `_` `~` `-`

**Randomness**: Must be cryptographically random (NOT pseudo-random)

**Entropy**: Minimum 256 bits (recommended)

### Python Implementation

**Using os.urandom (Recommended):**
```python
import os
import base64

# Generate 40 random bytes = 320 bits entropy
random_bytes = os.urandom(40)

# Base64url encode (results in 53-54 chars)
code_verifier = base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')

# Output: 53 characters, e.g., "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
```

**Why 40 bytes:**
- 40 bytes * 8 bits/byte = 320 bits entropy
- Base64 encoding: 40 bytes → 53-54 characters (within 43-128 range)
- Exceeds minimum 256-bit entropy requirement

**Why `rstrip('=')`:**
- Base64url padding `=` characters are optional per RFC 7636
- Removing padding makes verifier URL-safe without percent-encoding
- Server accepts verifiers with or without padding

**Why `os.urandom()` not `random.random()`:**
```python
# ❌ INSECURE: Pseudo-random, predictable
import random
bad_verifier = ''.join(random.choices('A-Za-z0-9', k=50))

# ✅ SECURE: Cryptographically random
import os
good_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8')
```

`os.urandom()` uses OS-level entropy sources:
- Linux: `/dev/urandom`
- macOS: `getentropy()`
- Windows: `CryptGenRandom()`

## Code Challenge Generation

### Challenge Methods

**S256 (SHA-256)** - Recommended, required by this skill:
```
code_challenge = BASE64URL(SHA256(ASCII(code_verifier)))
```

**plain** - Deprecated, insecure (challenge = verifier):
```
code_challenge = code_verifier
```

**Never use `plain` method** - Provides no security against interception attacks.

### SHA-256 Implementation

**Python:**
```python
import hashlib
import base64

# Compute SHA-256 hash
challenge_bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()

# Base64url encode (results in 43 chars)
code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')

# Output: 43 characters, e.g., "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
```

**Why SHA-256:**
- One-way function: Cannot reverse challenge to get verifier
- Collision-resistant: Extremely unlikely for two verifiers to produce same challenge
- Fast computation: Negligible performance impact
- Standardized: Widely supported by OAuth providers

**Why 43 characters:**
- SHA-256 produces 32-byte (256-bit) hash
- Base64 encoding: 32 bytes → 43 characters
- Consistent length regardless of verifier length

### Verification Process

**Server-side validation:**
```python
# Server receives:
stored_challenge = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
received_verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"

# Server computes:
computed_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(received_verifier.encode('utf-8')).digest()
).decode('utf-8').rstrip('=')

# Server compares:
if computed_challenge == stored_challenge:
    # Valid: Issue tokens
else:
    # Invalid: Reject request with 400 error
```

## Complete Flow Implementation

### Phase 1: Client Generates PKCE Pair

```python
def generate_pkce_pair() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge (S256)."""
    # 1. Generate verifier (40 bytes → 53 chars)
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8').rstrip('=')

    # 2. Compute challenge (SHA-256 → 43 chars)
    challenge_bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')

    return code_verifier, code_challenge
```

### Phase 2: Authorization Request

```python
# Include challenge in authorization URL
auth_url = (
    f"{AUTH_URL}?"
    f"client_id={client_id}&"
    f"redirect_uri={redirect_uri}&"
    f"response_type=code&"
    f"code_challenge={code_challenge}&"
    f"code_challenge_method=S256"
)

# Server stores: (authorization_code, code_challenge)
```

### Phase 3: Token Exchange

```python
# Include verifier in token request
token_response = requests.post(TOKEN_URL, data={
    'grant_type': 'authorization_code',
    'code': authorization_code,
    'redirect_uri': redirect_uri,
    'client_id': client_id,
    'client_secret': client_secret,
    'code_verifier': code_verifier,  # Proves client identity
})

# Server validates: SHA256(code_verifier) == stored_code_challenge
```

## Security Analysis

### Attack Scenario Without PKCE

1. **Attacker intercepts** authorization code (malware, network sniffing)
2. **Attacker has** client_id and client_secret (public client, easily extracted)
3. **Attacker exchanges** code for tokens
4. **Attack succeeds** - Attacker has full API access

### Attack Scenario With PKCE

1. **Attacker intercepts** authorization code
2. **Attacker has** client_id, client_secret, authorization code
3. **Attacker MISSING** code_verifier (only client has this)
4. **Attacker attempts** token exchange without verifier → 400 error
5. **Attacker attempts** token exchange with guessed verifier → 400 error (2^320 possibilities)
6. **Attack fails** - Cannot exchange code without original verifier

### Why SHA-256 Hash

**Without hashing (plain method):**
- Challenge = Verifier
- Interceptor sees challenge in authorization URL
- Interceptor can use challenge as verifier
- Attack succeeds (plain method provides no security)

**With SHA-256 hashing (S256 method):**
- Challenge = SHA-256(Verifier)
- Interceptor sees challenge in authorization URL
- Interceptor cannot reverse SHA-256 to get verifier
- Attack fails

## Testing PKCE Locally

### Unit Tests

```python
def test_verifier_length():
    """Verifier must be 43-128 characters."""
    verifier, _ = generate_pkce_pair()
    assert 43 <= len(verifier) <= 128

def test_verifier_charset():
    """Verifier must use URL-safe characters."""
    verifier, _ = generate_pkce_pair()
    assert all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
               for c in verifier)

def test_challenge_deterministic():
    """Same verifier produces same challenge."""
    verifier = "test_verifier"
    challenge1 = compute_challenge(verifier)
    challenge2 = compute_challenge(verifier)
    assert challenge1 == challenge2

def test_challenge_unique():
    """Different verifiers produce different challenges."""
    _, challenge1 = generate_pkce_pair()
    _, challenge2 = generate_pkce_pair()
    assert challenge1 != challenge2

def test_server_validation():
    """Server can validate verifier against challenge."""
    verifier, challenge = generate_pkce_pair()
    # Simulate server validation
    computed = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).decode().rstrip('=')
    assert computed == challenge
```

### Integration Test

```python
def test_oauth_flow_with_pkce():
    """Full OAuth flow with PKCE."""
    # 1. Generate PKCE pair
    verifier, challenge = generate_pkce_pair()

    # 2. Authorization request (includes challenge)
    auth_url = build_auth_url(challenge)
    # User approves, returns authorization code

    # 3. Token exchange (includes verifier)
    token_response = exchange_code(authorization_code, verifier)

    # 4. Verify tokens received
    assert 'access_token' in token_response
    assert 'refresh_token' in token_response
```

## Common Implementation Errors

### ❌ Error: Using Pseudo-Random Generator

```python
# INSECURE
import random
verifier = ''.join(random.choices(string.ascii_letters + string.digits, k=50))
```

**Fix:** Use `os.urandom()` for cryptographic randomness

### ❌ Error: Verifier Too Short

```python
# Generates ~27 chars (< 43 minimum)
verifier = base64.urlsafe_b64encode(os.urandom(20)).decode().rstrip('=')
```

**Fix:** Use at least 32 bytes (preferably 40) for urandom

### ❌ Error: Using Plain Method

```python
# No security
auth_url = f"...&code_challenge={verifier}&code_challenge_method=plain"
```

**Fix:** Always use S256 method

### ❌ Error: Not Stripping Padding

```python
# May include '=' which needs URL encoding
verifier = base64.urlsafe_b64encode(os.urandom(40)).decode()
```

**Fix:** Strip padding with `.rstrip('=')`

### ❌ Error: Storing Verifier on Server

```python
# Server should only store challenge, not verifier
server_storage['code'] = {'challenge': challenge, 'verifier': verifier}  # WRONG
```

**Fix:** Client keeps verifier, server stores only challenge

## Provider-Specific Notes

### Jobber
- PKCE support: ✅ S256 required
- Plain method: ❌ Not supported
- Challenge in URL: Yes
- Verifier validation: Strict (exact match required)

### GitHub
- PKCE support: ✅ S256 recommended
- Plain method: ✅ Supported (but discouraged)
- Challenge in URL: Yes
- Verifier validation: Strict

### Google
- PKCE support: ✅ S256 required for mobile/desktop
- Plain method: ❌ Not supported
- Challenge in URL: Yes
- Verifier validation: Strict

## References

- **RFC 7636 (PKCE)**: https://tools.ietf.org/html/rfc7636
- **RFC 3986 (URI)**: https://tools.ietf.org/html/rfc3986 (unreserved characters)
- **RFC 4648 (Base64)**: https://tools.ietf.org/html/rfc4648 (base64url encoding)
- **OAuth 2.0 Security**: https://tools.ietf.org/html/draft-ietf-oauth-security-topics
