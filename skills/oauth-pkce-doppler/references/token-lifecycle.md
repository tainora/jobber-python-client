# Token Lifecycle Management

Token refresh strategies (proactive/reactive), threading patterns, concurrency handling, and expiration management.

## Token Expiration

### Access Token Lifetimes

**Typical durations by provider:**
- Jobber: 60 minutes
- GitHub: 8 hours
- Google: 60 minutes
- Stripe: No expiration (but revocable)

**Security trade-off:**
- Short-lived: More secure (smaller breach window), more refresh requests
- Long-lived: Fewer refreshes, larger breach window if stolen

**Best practice:** Use provider defaults, implement automatic refresh

### Refresh Token Lifetimes

**Patterns:**
- **No expiration**: Valid until revoked (Google, most providers)
- **Sliding expiration**: Extends on each use (GitHub: 6 months)
- **Fixed expiration**: Hard deadline regardless of usage (rare)

**Revocation triggers:**
- User explicitly revokes in OAuth provider UI
- Security breach detected
- Developer rotates credentials
- Account deletion

## Proactive Refresh Strategy

### Concept

Refresh tokens BEFORE they expire, in background thread, without user interaction.

**Benefits:**
- No 401 errors during API calls
- Seamless user experience
- Predictable refresh timing
- Lower latency (no retry loop)

**Trade-offs:**
- Background thread overhead
- Refresh may fail silently (fallback to reactive)
- Slight complexity increase

### Implementation Pattern

```python
def _schedule_refresh(self) -> None:
    """Schedule proactive token refresh before expiration."""
    # Calculate delay until refresh should occur
    # Default: 5 minutes before expiry
    delay = max(0, self._token.expires_in_seconds - self.refresh_buffer_seconds)

    def refresh_task():
        with self._lock:  # Thread safety
            if not self._token.is_expired:
                try:
                    self._refresh_token()
                except AuthenticationError:
                    # Proactive refresh failed
                    # Will fall back to reactive refresh on next API call
                    pass

    self._refresh_timer = threading.Timer(delay, refresh_task)
    self._refresh_timer.daemon = True  # Don't block program exit
    self._refresh_timer.start()
```

### Refresh Buffer

**Buffer**: Time before expiration to trigger refresh

**Typical values:**
- 5 minutes (300 seconds) - Default in this skill
- 10 minutes - Conservative, more margin
- 1 minute - Aggressive, cuts it close

**Calculation:**
```
refresh_time = expires_at - buffer_seconds
delay = refresh_time - current_time
```

**Example:**
```
expires_at = 1640000000 (Unix timestamp)
current_time = 1639999100 (15 minutes before expiry)
buffer = 300 (5 minutes)

refresh_time = 1640000000 - 300 = 1639999700
delay = 1639999700 - 1639999100 = 600 seconds (10 minutes)

# Refresh will occur in 10 minutes (5 minutes before expiry)
```

### Timer Management

**Cancel existing timers:**
```python
if self._refresh_timer:
    self._refresh_timer.cancel()
```

Always cancel before scheduling new timer to prevent timer leaks.

**Daemon threads:**
```python
timer.daemon = True  # Allows program to exit even if timer pending
```

Non-daemon timers block program exit. Always use daemon=True for background refresh.

## Reactive Refresh Strategy

### Concept

Refresh tokens ON DEMAND when API call returns 401 Unauthorized.

**Benefits:**
- Simple implementation
- Handles race conditions (token expired between check and use)
- Fallback if proactive refresh fails
- No background threads needed (if used alone)

**Trade-offs:**
- User-visible latency (extra request on 401)
- Retry logic complexity
- More 401 errors logged

### Implementation Pattern

```python
def api_call_with_refresh(self, endpoint: str) -> dict:
    """Make API call with automatic token refresh on 401."""
    token = self.token_manager.get_token()

    try:
        response = requests.get(endpoint, headers={'Authorization': f'Bearer {token}'})
        response.raise_for_status()
        return response.json()

    except requests.HTTPError as e:
        if e.response.status_code == 401:
            # Token expired, refresh and retry ONCE
            token = self.token_manager.refresh_on_401()
            response = requests.get(endpoint, headers={'Authorization': f'Bearer {token}'})
            response.raise_for_status()
            return response.json()
        else:
            # Other error, propagate
            raise
```

**Key points:**
- Only retry ONCE (prevent infinite loops)
- Only on 401 (not 403, 500, etc.)
- Use fresh token from refresh_on_401()

### Refresh-on-401 Method

```python
def refresh_on_401(self) -> str:
    """Reactive token refresh after 401 error."""
    with self._lock:  # Thread safety
        self._refresh_token()
        return self._token.access_token
```

**Thread safety:** Lock prevents concurrent refresh attempts from multiple threads.

## Hybrid Strategy (Recommended)

Combine proactive + reactive for best experience:

```python
class TokenManager:
    def __init__(self, ..., proactive_refresh=True):
        # ...
        if proactive_refresh:
            self._schedule_refresh()  # Background refresh

    def get_token(self) -> str:
        """Get token with proactive refresh check."""
        with self._lock:
            if self._token.should_refresh(self.refresh_buffer_seconds):
                self._refresh_token()  # Immediate refresh if past buffer
            return self._token.access_token

# Usage in API client
try:
    token = manager.get_token()  # May proactively refresh
    response = api_call(token)
except AuthenticationError:
    token = manager.refresh_on_401()  # Reactive refresh fallback
    response = api_call(token)  # Retry once
```

**Flow:**
1. Background thread refreshes 5min before expiry (proactive)
2. If background refresh fails, `get_token()` checks and refreshes (proactive fallback)
3. If token still expired (race condition), `refresh_on_401()` retries (reactive)

## Thread Safety

### Concurrency Challenges

**Race condition example:**
```python
# Thread 1                          # Thread 2
token = manager.get_token()         token = manager.get_token()
# Both check: token expires in 4min
# Both trigger refresh simultaneously
manager._refresh_token()            manager._refresh_token()
# Two concurrent refresh requests!
```

**Problems:**
- Wasted requests (two refreshes for same expiration)
- Potential token rotation conflicts
- Doppler write race conditions

### Lock-Protected Critical Sections

```python
class TokenManager:
    def __init__(self):
        self._lock = threading.Lock()  # Mutex for token access

    def get_token(self) -> str:
        with self._lock:  # Acquire lock
            if self._token.should_refresh():
                self._refresh_token()  # Only one thread can execute
            return self._token.access_token
        # Lock auto-released on exit

    def _refresh_token(self) -> None:
        # Assumes caller holds lock
        # Safe to modify self._token
```

**Protected operations:**
- Reading token expiration
- Checking if refresh needed
- Performing refresh request
- Updating in-memory token
- Writing to Doppler

**Lock granularity:**
- Hold lock for entire refresh operation
- Prevents partial updates (torn reads)
- Ensures atomic token replacement

### Deadlock Prevention

**Avoid nested locks:**
```python
# ❌ Bad: Potential deadlock
def outer():
    with self._lock:
        self.inner()  # If inner() also acquires lock → deadlock

def inner():
    with self._lock:  # Tries to acquire already-held lock
        pass
```

**Fix: Assume lock held:**
```python
# ✅ Good: Document lock requirement
def get_token(self) -> str:
    with self._lock:
        self._refresh_if_needed()  # Assumes caller holds lock

def _refresh_if_needed(self) -> None:
    # Private method, assumes lock held
    # No nested lock acquisition
```

## Refresh Token Rotation

### Providers That Rotate

**GitHub:** Issues new refresh_token on each refresh
```json
{
  "access_token": "new_access_gho_xxx",
  "refresh_token": "new_refresh_ghr_yyy",  // New refresh token
  "expires_in": 28800
}
```

**Providers That Don't Rotate:**

**Jobber, Google:** Reuse existing refresh_token
```json
{
  "access_token": "new_access_xxx",
  // No refresh_token field (reuse existing)
  "expires_in": 3600
}
```

### Handling Both Patterns

```python
def _refresh_token(self) -> None:
    response = requests.post(TOKEN_URL, data={
        'grant_type': 'refresh_token',
        'refresh_token': self._token.refresh_token,
        'client_id': self.client_id,
        'client_secret': self.client_secret,
    })
    response.raise_for_status()

    token_data = response.json()
    access_token = token_data['access_token']

    # Handle both rotating and non-rotating refresh tokens
    refresh_token = token_data.get('refresh_token', self._token.refresh_token)

    expires_in = token_data['expires_in']
    expires_at = int(time.time()) + expires_in

    self._token = TokenInfo(access_token, refresh_token, expires_at)
    self._save_to_doppler()
```

**Key:** Use `get('refresh_token', fallback)` to handle optional field.

## Expiration Timestamp Calculation

### Unix Timestamps

**Definition:** Seconds since January 1, 1970 00:00:00 UTC

**Example:**
```python
import time

# Current time
now = time.time()  # 1640000000.123456

# Token expires in 3600 seconds (1 hour)
expires_in = 3600
expires_at = int(now) + expires_in  # 1640003600

# Store as string for Doppler
expires_at_str = str(expires_at)  # "1640003600"
```

### Checking Expiration

```python
@property
def is_expired(self) -> bool:
    """Check if token is currently expired."""
    return time.time() >= self.expires_at

@property
def expires_in_seconds(self) -> int:
    """Seconds until token expires."""
    return max(0, int(self.expires_at - time.time()))

def should_refresh(self, buffer_seconds: int = 300) -> bool:
    """Check if token should be refreshed (within buffer window)."""
    return self.expires_in_seconds < buffer_seconds
```

### Clock Skew Handling

**Problem:** Client and server clocks may differ

**Conservative approach:**
```python
# Add small buffer to account for clock skew
CLOCK_SKEW_BUFFER = 60  # 1 minute

def is_expired(self) -> bool:
    return time.time() >= (self.expires_at - CLOCK_SKEW_BUFFER)
```

Treats token as expired 1 minute early to account for potential clock differences.

## Error Handling in Refresh

### Refresh Failures

**Network errors:**
```python
except requests.Timeout:
    # Server didn't respond
    raise AuthenticationError("Token refresh timeout")

except requests.ConnectionError:
    # Cannot reach server
    raise AuthenticationError("Token refresh connection failed")
```

**HTTP errors:**
```python
except requests.HTTPError as e:
    if e.response.status_code == 400:
        # Invalid refresh token
        raise AuthenticationError("Refresh token invalid or expired")
    elif e.response.status_code == 401:
        # Unauthorized (shouldn't happen with valid refresh token)
        raise AuthenticationError("Client credentials invalid")
    else:
        raise AuthenticationError(f"Token refresh failed: {e}")
```

### Proactive Refresh Failure

**Silent failure acceptable:**
```python
def refresh_task():
    try:
        with self._lock:
            self._refresh_token()
    except AuthenticationError:
        # Proactive refresh failed (network issue, temporary server error)
        # Don't crash program
        # Reactive refresh will retry on next API call
        pass
```

**Logging recommended:**
```python
except AuthenticationError as e:
    logger.warning(f"Proactive token refresh failed: {e}")
    # Continue execution, reactive refresh will handle it
```

### Reactive Refresh Failure

**Must propagate:**
```python
def refresh_on_401(self) -> str:
    try:
        with self._lock:
            self._refresh_token()
            return self._token.access_token
    except AuthenticationError:
        # Reactive refresh failed - caller must handle
        # Likely needs re-authorization (refresh token revoked)
        raise
```

Caller decides whether to re-authenticate or abort operation.

## Best Practices

### 1. Use Hybrid Strategy

Proactive (background) + reactive (on 401) provides best UX.

### 2. Conservative Buffer

5-10 minutes before expiry gives margin for network delays.

### 3. Thread-Safe Operations

Always protect token reads/writes with locks.

### 4. Daemon Threads

Background threads should be daemon to allow clean exit.

### 5. Handle Both Rotation Patterns

Use `.get('refresh_token', fallback)` for providers that don't rotate.

### 6. Silent Proactive Failures

Log but don't crash on background refresh failures.

### 7. Propagate Reactive Failures

Let caller decide recovery strategy for on-demand refresh failures.

### 8. Update Doppler on Every Refresh

Keep secrets manager synchronized with in-memory state.

## References

- **Jobber Token Management**: `/Users/terryli/own/jobber/jobber/auth.py`
- **Threading Documentation**: https://docs.python.org/3/library/threading.html
- **OAuth Token Refresh**: RFC 6749 Section 6
