"""
OAuth Token Manager with Automatic Refresh

Generic template for token lifecycle management with Doppler storage.
Handles proactive (background) and reactive (on 401) token refresh.

CUSTOMIZATION:
    1. Update SERVICE_PREFIX for your OAuth provider
    2. Set TOKEN_URL to your provider's token endpoint
    3. Set DOPPLER_PROJECT and DOPPLER_CONFIG
    4. Integrate into your API client

Based on production implementation: /Users/terryli/own/jobber/jobber/auth.py

Usage:
    from your_project.auth import TokenManager

    manager = TokenManager.from_doppler("your-project", "dev")
    token = manager.get_token()  # Auto-refreshes if needed

    # Or handle 401 errors:
    try:
        response = api_call(token)
    except AuthenticationError:
        token = manager.refresh_on_401()
        response = api_call(token)  # Retry

Thread Safety:
    - All public methods are thread-safe (lock-protected)
    - Safe for concurrent use by multiple threads/requests
"""

import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Any

import requests


# ============================================================================
# CONFIGURATION - Customize for your OAuth provider
# ============================================================================

# OAuth Provider
SERVICE_PREFIX = "EXAMPLE_"  # CUSTOMIZE: Prefix for secret names (e.g., "GITHUB_", "JOBBER_")
TOKEN_URL = "https://api.example.com/oauth/token"  # CUSTOMIZE: Token endpoint

# Doppler Configuration
DOPPLER_PROJECT = "your-project"  # CUSTOMIZE
DOPPLER_CONFIG = "dev"            # CUSTOMIZE

# Token Refresh Settings
REFRESH_BUFFER_SECONDS = 300  # Refresh 5 minutes before expiry
PROACTIVE_REFRESH = True      # Enable background refresh thread

# ============================================================================
# Token Manager Implementation
# ============================================================================


class AuthenticationError(Exception):
    """OAuth token invalid or refresh failed"""
    pass


class ConfigurationError(Exception):
    """Doppler configuration invalid or secrets missing"""
    pass


@dataclass
class TokenInfo:
    """OAuth token information"""
    access_token: str
    refresh_token: str
    expires_at: int  # Unix timestamp

    @property
    def is_expired(self) -> bool:
        """Check if token is expired"""
        return time.time() >= self.expires_at

    @property
    def expires_in_seconds(self) -> int:
        """Seconds until token expires"""
        return max(0, int(self.expires_at - time.time()))

    def should_refresh(self, buffer_seconds: int = 300) -> bool:
        """Check if token should be proactively refreshed"""
        return self.expires_in_seconds < buffer_seconds


class TokenManager:
    """
    Manages OAuth token lifecycle with Doppler backend.

    Responsibilities:
    - Load tokens from Doppler on init
    - Proactively refresh tokens before expiration (background thread)
    - Reactively refresh on 401 errors
    - Update Doppler with new tokens
    - Thread-safe token access

    Thread Safety:
        All public methods protected by lock
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        doppler_project: str = DOPPLER_PROJECT,
        doppler_config: str = DOPPLER_CONFIG,
        proactive_refresh: bool = PROACTIVE_REFRESH,
        refresh_buffer_seconds: int = REFRESH_BUFFER_SECONDS,
    ):
        """
        Initialize token manager.

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            doppler_project: Doppler project name
            doppler_config: Doppler config name
            proactive_refresh: Enable background token refresh
            refresh_buffer_seconds: Seconds before expiry to trigger refresh

        Raises:
            ConfigurationError: Doppler secrets not found
            AuthenticationError: Token loading fails
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.doppler_project = doppler_project
        self.doppler_config = doppler_config
        self.proactive_refresh = proactive_refresh
        self.refresh_buffer_seconds = refresh_buffer_seconds

        self._lock = threading.Lock()
        self._refresh_timer: threading.Timer | None = None

        # Load initial tokens from Doppler
        self._token = self._load_from_doppler()

        # Schedule proactive refresh
        if self.proactive_refresh:
            self._schedule_refresh()

    @classmethod
    def from_doppler(
        cls,
        doppler_project: str = DOPPLER_PROJECT,
        doppler_config: str = DOPPLER_CONFIG,
        **kwargs: Any
    ) -> 'TokenManager':
        """
        Create TokenManager loading credentials from Doppler.

        Args:
            doppler_project: Doppler project name
            doppler_config: Doppler config name
            **kwargs: Additional arguments for TokenManager.__init__

        Returns:
            Configured TokenManager instance

        Raises:
            ConfigurationError: Required secrets not found in Doppler
        """
        client_id, client_secret = cls._load_credentials(doppler_project, doppler_config)
        return cls(client_id, client_secret, doppler_project, doppler_config, **kwargs)

    def get_token(self) -> str:
        """
        Get current valid access token. Proactively refreshes if close to expiry.

        Returns:
            Valid access token

        Raises:
            AuthenticationError: Token refresh fails

        Thread Safety:
            Lock-protected, safe for concurrent calls
        """
        with self._lock:
            if self._token.should_refresh(self.refresh_buffer_seconds):
                self._refresh_token()
            return self._token.access_token

    def refresh_on_401(self) -> str:
        """
        Reactive token refresh after 401 error.

        Returns:
            New access token

        Raises:
            AuthenticationError: Token refresh fails

        Thread Safety:
            Lock-protected, safe for concurrent calls
        """
        with self._lock:
            self._refresh_token()
            return self._token.access_token

    def _load_from_doppler(self) -> TokenInfo:
        """
        Load tokens from Doppler secrets.

        Returns:
            TokenInfo with current tokens

        Raises:
            ConfigurationError: Secrets not found
            AuthenticationError: Invalid token data
        """
        try:
            result = subprocess.run(
                [
                    'doppler', 'secrets', 'get',
                    f'{SERVICE_PREFIX}ACCESS_TOKEN',
                    f'{SERVICE_PREFIX}REFRESH_TOKEN',
                    f'{SERVICE_PREFIX}TOKEN_EXPIRES_AT',
                    '--project', self.doppler_project,
                    '--config', self.doppler_config,
                    '--plain'
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )

            lines = result.stdout.strip().split('\n')
            if len(lines) != 3:
                raise ConfigurationError(
                    f"Expected 3 token secrets, got {len(lines)}. "
                    f"Ensure {SERVICE_PREFIX}ACCESS_TOKEN, {SERVICE_PREFIX}REFRESH_TOKEN, "
                    f"and {SERVICE_PREFIX}TOKEN_EXPIRES_AT exist in Doppler."
                )

            access_token, refresh_token, expires_at_str = lines
            expires_at = int(expires_at_str)

            return TokenInfo(access_token, refresh_token, expires_at)

        except subprocess.CalledProcessError as e:
            raise ConfigurationError(
                f"Failed to load tokens from Doppler: {e.stderr}"
            ) from e
        except (ValueError, IndexError) as e:
            raise AuthenticationError(
                f"Invalid token data in Doppler: {e}"
            ) from e

    @classmethod
    def _load_credentials(cls, doppler_project: str, doppler_config: str) -> tuple[str, str]:
        """
        Load client ID and secret from Doppler.

        Returns:
            (client_id, client_secret)

        Raises:
            ConfigurationError: Credentials not found
        """
        try:
            result = subprocess.run(
                [
                    'doppler', 'secrets', 'get',
                    f'{SERVICE_PREFIX}CLIENT_ID',
                    f'{SERVICE_PREFIX}CLIENT_SECRET',
                    '--project', doppler_project,
                    '--config', doppler_config,
                    '--plain'
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )

            lines = result.stdout.strip().split('\n')
            if len(lines) != 2:
                raise ConfigurationError(
                    f"Expected 2 credential secrets, got {len(lines)}. "
                    f"Ensure {SERVICE_PREFIX}CLIENT_ID and {SERVICE_PREFIX}CLIENT_SECRET exist."
                )

            return lines[0], lines[1]

        except subprocess.CalledProcessError as e:
            raise ConfigurationError(
                f"Failed to load credentials from Doppler: {e.stderr}"
            ) from e

    def _refresh_token(self) -> None:
        """
        Refresh OAuth token (must hold lock).

        Raises:
            AuthenticationError: Token refresh fails

        Updates:
            - self._token with new tokens
            - Doppler with new tokens
            - Refresh timer schedule
        """
        try:
            response = requests.post(
                TOKEN_URL,
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': self._token.refresh_token,
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                },
                timeout=30
            )
            response.raise_for_status()

            token_data = response.json()
            access_token = token_data['access_token']
            # Some providers issue new refresh token, some don't
            refresh_token = token_data.get('refresh_token', self._token.refresh_token)
            expires_in = token_data['expires_in']
            expires_at = int(time.time()) + expires_in

            # Update in-memory token
            self._token = TokenInfo(access_token, refresh_token, expires_at)

            # Save to Doppler
            self._save_to_doppler()

            # Reschedule proactive refresh
            if self.proactive_refresh:
                self._schedule_refresh()

        except requests.RequestException as e:
            raise AuthenticationError(f"Token refresh failed: {e}") from e

    def _save_to_doppler(self) -> None:
        """
        Save current tokens to Doppler (must hold lock).

        Raises:
            AuthenticationError: Doppler save fails
        """
        secrets = {
            f'{SERVICE_PREFIX}ACCESS_TOKEN': self._token.access_token,
            f'{SERVICE_PREFIX}REFRESH_TOKEN': self._token.refresh_token,
            f'{SERVICE_PREFIX}TOKEN_EXPIRES_AT': str(self._token.expires_at)
        }

        for name, value in secrets.items():
            try:
                subprocess.run(
                    [
                        'doppler', 'secrets', 'set', name,
                        '--project', self.doppler_project,
                        '--config', self.doppler_config,
                        '--silent'
                    ],
                    input=value,
                    text=True,
                    check=True,
                    capture_output=True,
                    timeout=10
                )
            except subprocess.CalledProcessError as e:
                raise AuthenticationError(
                    f"Failed to save {name} to Doppler: {e.stderr}"
                ) from e

    def _schedule_refresh(self) -> None:
        """
        Schedule proactive token refresh (must hold lock).

        Cancels existing timer if present.
        """
        # Cancel existing timer
        if self._refresh_timer:
            self._refresh_timer.cancel()

        # Schedule refresh before expiration
        delay = max(0, self._token.expires_in_seconds - self.refresh_buffer_seconds)

        def refresh_task():
            with self._lock:
                if not self._token.is_expired:
                    try:
                        self._refresh_token()
                    except AuthenticationError:
                        # Proactive refresh failed, will retry on next get_token()
                        pass

        self._refresh_timer = threading.Timer(delay, refresh_task)
        self._refresh_timer.daemon = True  # Don't block program exit
        self._refresh_timer.start()
