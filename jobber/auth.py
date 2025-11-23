"""
OAuth token management with Doppler integration.

Handles:
- Loading tokens from Doppler
- Proactive token refresh (background)
- Reactive token refresh (on 401)

Error handling:
- Raises AuthenticationError on any failure
- No fallback or default tokens
"""

import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Any

import requests

from .exceptions import AuthenticationError, ConfigurationError


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
        """Check if token should be proactively refreshed (default 5min buffer)"""
        return self.expires_in_seconds < buffer_seconds


class TokenManager:
    """
    Manages OAuth token lifecycle with Doppler backend.

    Responsibilities:
    - Load tokens from Doppler on init
    - Proactively refresh tokens before expiration
    - Reactively refresh on 401 errors
    - Update Doppler with new tokens

    Thread-safety: Lock-protected token refresh
    """

    TOKEN_URL = "https://api.getjobber.com/api/oauth/token"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        doppler_project: str,
        doppler_config: str,
        proactive_refresh: bool = True,
        refresh_buffer_seconds: int = 300
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
            ConfigurationError: Doppler credentials not found
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
        doppler_project: str,
        doppler_config: str,
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
        Get current valid access token.

        Proactively refreshes if close to expiry.

        Returns:
            Valid access token

        Raises:
            AuthenticationError: Token refresh fails
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
        """
        with self._lock:
            self._refresh_token()
            return self._token.access_token

    def _load_from_doppler(self) -> TokenInfo:
        """
        Load tokens from Doppler.

        Returns:
            TokenInfo with current tokens

        Raises:
            ConfigurationError: Secrets not found
            AuthenticationError: Invalid token format
        """
        try:
            result = subprocess.run(
                [
                    'doppler', 'secrets', 'get',
                    'JOBBER_ACCESS_TOKEN',
                    'JOBBER_REFRESH_TOKEN',
                    'JOBBER_TOKEN_EXPIRES_AT',
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
                    f"Expected 3 tokens from Doppler, got {len(lines)}. "
                    f"Run jobber_auth.py to authenticate."
                )

            access_token, refresh_token, expires_at = lines

            try:
                expires_at_int = int(expires_at)
            except ValueError as e:
                raise AuthenticationError(
                    f"Invalid JOBBER_TOKEN_EXPIRES_AT format: {expires_at}"
                ) from e

            return TokenInfo(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at_int
            )

        except subprocess.CalledProcessError as e:
            raise ConfigurationError(
                f"Failed to load tokens from Doppler: {e.stderr}. "
                f"Ensure project={self.doppler_project}, config={self.doppler_config} exist."
            ) from e

    @staticmethod
    def _load_credentials(project: str, config: str) -> tuple[str, str]:
        """
        Load client credentials from Doppler.

        Returns:
            (client_id, client_secret)

        Raises:
            ConfigurationError: Credentials not found
        """
        try:
            result = subprocess.run(
                [
                    'doppler', 'secrets', 'get',
                    'JOBBER_CLIENT_ID',
                    'JOBBER_CLIENT_SECRET',
                    '--project', project,
                    '--config', config,
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
                    f"Expected JOBBER_CLIENT_ID and JOBBER_CLIENT_SECRET in Doppler. "
                    f"Add credentials to project={project}, config={config}"
                )

            return lines[0], lines[1]

        except subprocess.CalledProcessError as e:
            raise ConfigurationError(
                f"Failed to load client credentials: {e.stderr}"
            ) from e

    def _refresh_token(self) -> None:
        """
        Refresh OAuth token (must hold lock).

        Updates self._token and Doppler.

        Raises:
            AuthenticationError: Refresh fails
        """
        try:
            response = requests.post(
                self.TOKEN_URL,
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': self._token.refresh_token,
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                },
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            # Update token info
            expires_at = int(time.time()) + data['expires_in']
            self._token = TokenInfo(
                access_token=data['access_token'],
                refresh_token=data.get('refresh_token', self._token.refresh_token),
                expires_at=expires_at
            )

            # Update Doppler
            self._save_to_doppler()

            # Reschedule next refresh
            if self.proactive_refresh:
                self._schedule_refresh()

        except requests.RequestException as e:
            raise AuthenticationError(
                f"Token refresh failed: {e}",
                context={'refresh_token': self._token.refresh_token[:8] + '...'}
            ) from e

    def _save_to_doppler(self) -> None:
        """
        Save current tokens to Doppler.

        Raises:
            AuthenticationError: Doppler update fails
        """
        secrets = {
            'JOBBER_ACCESS_TOKEN': self._token.access_token,
            'JOBBER_REFRESH_TOKEN': self._token.refresh_token,
            'JOBBER_TOKEN_EXPIRES_AT': str(self._token.expires_at)
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
                    f"Failed to update {name} in Doppler: {e.stderr}"
                ) from e

    def _schedule_refresh(self) -> None:
        """Schedule proactive token refresh (must hold lock)"""
        # Cancel existing timer
        if self._refresh_timer is not None:
            self._refresh_timer.cancel()

        # Calculate when to refresh
        refresh_in = max(0, self._token.expires_in_seconds - self.refresh_buffer_seconds)

        # Schedule refresh
        self._refresh_timer = threading.Timer(refresh_in, self._proactive_refresh)
        self._refresh_timer.daemon = True
        self._refresh_timer.start()

    def _proactive_refresh(self) -> None:
        """Background thread: proactive token refresh"""
        try:
            with self._lock:
                self._refresh_token()
        except AuthenticationError:
            # Proactive refresh failed - will be retried on next API call (reactive)
            pass
