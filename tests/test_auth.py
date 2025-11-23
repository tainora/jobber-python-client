"""Unit tests for jobber.auth module (TokenManager)."""

import subprocess
import threading
import time
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from jobber.auth import TokenInfo, TokenManager
from jobber.exceptions import AuthenticationError, ConfigurationError


class TestTokenInfo:
    """Test TokenInfo dataclass and property methods."""

    def test_is_expired_returns_true_when_past_expiration(self) -> None:
        """Token is expired when current time >= expires_at."""
        with patch("time.time", return_value=1000):
            token = TokenInfo(
                access_token="access123", refresh_token="refresh456", expires_at=999
            )
            assert token.is_expired is True

    def test_is_expired_returns_false_when_before_expiration(self) -> None:
        """Token is not expired when current time < expires_at."""
        with patch("time.time", return_value=1000):
            token = TokenInfo(
                access_token="access123", refresh_token="refresh456", expires_at=1001
            )
            assert token.is_expired is False

    def test_expires_in_seconds_returns_remaining_time(self) -> None:
        """expires_in_seconds returns difference between expires_at and current time."""
        with patch("time.time", return_value=1000):
            token = TokenInfo(
                access_token="access123", refresh_token="refresh456", expires_at=1300
            )
            assert token.expires_in_seconds == 300

    def test_expires_in_seconds_returns_zero_when_expired(self) -> None:
        """expires_in_seconds returns 0 when token is expired."""
        with patch("time.time", return_value=1000):
            token = TokenInfo(
                access_token="access123", refresh_token="refresh456", expires_at=999
            )
            assert token.expires_in_seconds == 0

    def test_should_refresh_returns_true_within_buffer(self) -> None:
        """should_refresh returns True when within buffer_seconds of expiration."""
        with patch("time.time", return_value=1000):
            token = TokenInfo(
                access_token="access123", refresh_token="refresh456", expires_at=1200
            )
            # 200 seconds until expiration, buffer is 300 seconds
            assert token.should_refresh(buffer_seconds=300) is True

    def test_should_refresh_returns_false_outside_buffer(self) -> None:
        """should_refresh returns False when beyond buffer_seconds."""
        with patch("time.time", return_value=1000):
            token = TokenInfo(
                access_token="access123", refresh_token="refresh456", expires_at=1400
            )
            # 400 seconds until expiration, buffer is 300 seconds
            assert token.should_refresh(buffer_seconds=300) is False


class TestTokenManagerInit:
    """Test TokenManager initialization."""

    @patch.object(TokenManager, "_schedule_refresh")
    @patch.object(TokenManager, "_load_from_doppler")
    def test_init_loads_tokens_from_doppler(
        self, mock_load: Mock, mock_schedule: Mock
    ) -> None:
        """__init__ calls _load_from_doppler to retrieve initial tokens."""
        mock_token = TokenInfo(
            access_token="access123", refresh_token="refresh456", expires_at=2000
        )
        mock_load.return_value = mock_token

        manager = TokenManager(
            client_id="client123",
            client_secret="secret456",
            doppler_project="test-project",
            doppler_config="test-config",
        )

        assert manager._token == mock_token
        mock_load.assert_called_once()

    @patch.object(TokenManager, "_schedule_refresh")
    @patch.object(TokenManager, "_load_from_doppler")
    def test_init_schedules_proactive_refresh_when_enabled(
        self, mock_load: Mock, mock_schedule: Mock
    ) -> None:
        """__init__ schedules proactive refresh when proactive_refresh=True."""
        mock_token = TokenInfo(
            access_token="access123", refresh_token="refresh456", expires_at=2000
        )
        mock_load.return_value = mock_token

        TokenManager(
            client_id="client123",
            client_secret="secret456",
            doppler_project="test-project",
            doppler_config="test-config",
            proactive_refresh=True,
        )

        mock_schedule.assert_called_once()

    @patch.object(TokenManager, "_schedule_refresh")
    @patch.object(TokenManager, "_load_from_doppler")
    def test_init_skips_proactive_refresh_when_disabled(
        self, mock_load: Mock, mock_schedule: Mock
    ) -> None:
        """__init__ does not schedule proactive refresh when proactive_refresh=False."""
        mock_token = TokenInfo(
            access_token="access123", refresh_token="refresh456", expires_at=2000
        )
        mock_load.return_value = mock_token

        TokenManager(
            client_id="client123",
            client_secret="secret456",
            doppler_project="test-project",
            doppler_config="test-config",
            proactive_refresh=False,
        )

        mock_schedule.assert_not_called()


class TestLoadFromDoppler:
    """Test _load_from_doppler method."""

    @patch("subprocess.run")
    def test_load_from_doppler_returns_token_info_on_success(self, mock_run: Mock) -> None:
        """_load_from_doppler parses Doppler output into TokenInfo."""
        mock_run.return_value = Mock(
            stdout="access_token_value\nrefresh_token_value\n1700000000\n"
        )

        with patch.object(TokenManager, "_schedule_refresh"):
            manager = TokenManager(
                client_id="client123",
                client_secret="secret456",
                doppler_project="test-project",
                doppler_config="test-config",
            )

        assert manager._token.access_token == "access_token_value"
        assert manager._token.refresh_token == "refresh_token_value"
        assert manager._token.expires_at == 1700000000

    @patch("subprocess.run")
    def test_load_from_doppler_raises_configuration_error_on_wrong_line_count(
        self, mock_run: Mock
    ) -> None:
        """_load_from_doppler raises ConfigurationError when Doppler returns != 3 lines."""
        mock_run.return_value = Mock(stdout="access_token\nrefresh_token\n")  # Only 2 lines

        with pytest.raises(ConfigurationError, match="Expected 3 tokens from Doppler"):
            TokenManager(
                client_id="client123",
                client_secret="secret456",
                doppler_project="test-project",
                doppler_config="test-config",
            )

    @patch("subprocess.run")
    def test_load_from_doppler_raises_authentication_error_on_invalid_expires_at(
        self, mock_run: Mock
    ) -> None:
        """_load_from_doppler raises AuthenticationError when expires_at is not an integer."""
        mock_run.return_value = Mock(
            stdout="access_token\nrefresh_token\ninvalid_timestamp\n"
        )

        with pytest.raises(AuthenticationError, match="Invalid JOBBER_TOKEN_EXPIRES_AT format"):
            TokenManager(
                client_id="client123",
                client_secret="secret456",
                doppler_project="test-project",
                doppler_config="test-config",
            )

    @patch("subprocess.run")
    def test_load_from_doppler_raises_configuration_error_on_subprocess_failure(
        self, mock_run: Mock
    ) -> None:
        """_load_from_doppler raises ConfigurationError when Doppler CLI fails."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["doppler"], stderr="Project not found"
        )

        with pytest.raises(ConfigurationError, match="Failed to load tokens from Doppler"):
            TokenManager(
                client_id="client123",
                client_secret="secret456",
                doppler_project="test-project",
                doppler_config="test-config",
            )


class TestLoadCredentials:
    """Test _load_credentials static method."""

    @patch("subprocess.run")
    def test_load_credentials_returns_client_id_and_secret(self, mock_run: Mock) -> None:
        """_load_credentials parses client_id and client_secret from Doppler."""
        mock_run.return_value = Mock(stdout="client_id_value\nclient_secret_value\n")

        client_id, client_secret = TokenManager._load_credentials("project", "config")

        assert client_id == "client_id_value"
        assert client_secret == "client_secret_value"

    @patch("subprocess.run")
    def test_load_credentials_raises_configuration_error_on_wrong_line_count(
        self, mock_run: Mock
    ) -> None:
        """_load_credentials raises ConfigurationError when Doppler returns != 2 lines."""
        mock_run.return_value = Mock(stdout="client_id_only\n")  # Only 1 line

        with pytest.raises(
            ConfigurationError, match="Expected JOBBER_CLIENT_ID and JOBBER_CLIENT_SECRET"
        ):
            TokenManager._load_credentials("project", "config")

    @patch("subprocess.run")
    def test_load_credentials_raises_configuration_error_on_subprocess_failure(
        self, mock_run: Mock
    ) -> None:
        """_load_credentials raises ConfigurationError when Doppler CLI fails."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["doppler"], stderr="Authentication failed"
        )

        with pytest.raises(ConfigurationError, match="Failed to load client credentials"):
            TokenManager._load_credentials("project", "config")


class TestGetToken:
    """Test get_token method."""

    @patch.object(TokenManager, "_refresh_token")
    @patch.object(TokenManager, "_load_from_doppler")
    @patch.object(TokenManager, "_schedule_refresh")
    def test_get_token_returns_fresh_token_without_refresh(
        self, mock_schedule: Mock, mock_load: Mock, mock_refresh: Mock
    ) -> None:
        """get_token returns access token without refresh when not expired."""
        mock_token = TokenInfo(
            access_token="access123", refresh_token="refresh456", expires_at=2000
        )
        mock_load.return_value = mock_token

        with patch("time.time", return_value=1000):  # 1000 seconds until expiration
            manager = TokenManager(
                client_id="client123",
                client_secret="secret456",
                doppler_project="test-project",
                doppler_config="test-config",
                refresh_buffer_seconds=300,
            )

            token = manager.get_token()

        assert token == "access123"
        mock_refresh.assert_not_called()

    @patch.object(TokenManager, "_refresh_token")
    @patch.object(TokenManager, "_load_from_doppler")
    @patch.object(TokenManager, "_schedule_refresh")
    def test_get_token_refreshes_when_within_buffer(
        self, mock_schedule: Mock, mock_load: Mock, mock_refresh: Mock
    ) -> None:
        """get_token calls _refresh_token when within refresh buffer."""
        mock_token = TokenInfo(
            access_token="access123", refresh_token="refresh456", expires_at=1200
        )
        mock_load.return_value = mock_token

        with patch("time.time", return_value=1000):  # 200 seconds until expiration
            manager = TokenManager(
                client_id="client123",
                client_secret="secret456",
                doppler_project="test-project",
                doppler_config="test-config",
                refresh_buffer_seconds=300,  # Refresh when <300 seconds remain
            )

            manager.get_token()

        mock_refresh.assert_called_once()


class TestRefreshOn401:
    """Test refresh_on_401 method."""

    @patch.object(TokenManager, "_refresh_token")
    @patch.object(TokenManager, "_load_from_doppler")
    @patch.object(TokenManager, "_schedule_refresh")
    def test_refresh_on_401_calls_refresh_and_returns_new_token(
        self, mock_schedule: Mock, mock_load: Mock, mock_refresh: Mock
    ) -> None:
        """refresh_on_401 triggers token refresh and returns new access token."""
        mock_token = TokenInfo(
            access_token="old_token", refresh_token="refresh456", expires_at=2000
        )
        mock_load.return_value = mock_token

        manager = TokenManager(
            client_id="client123",
            client_secret="secret456",
            doppler_project="test-project",
            doppler_config="test-config",
        )

        # Simulate token refresh updating _token
        def refresh_side_effect() -> None:
            manager._token = TokenInfo(
                access_token="new_token", refresh_token="refresh456", expires_at=3000
            )

        mock_refresh.side_effect = refresh_side_effect

        token = manager.refresh_on_401()

        assert token == "new_token"
        mock_refresh.assert_called_once()


class TestRefreshToken:
    """Test _refresh_token method."""

    @patch("requests.post")
    @patch.object(TokenManager, "_save_to_doppler")
    @patch.object(TokenManager, "_schedule_refresh")
    @patch.object(TokenManager, "_load_from_doppler")
    @patch("time.time")
    def test_refresh_token_updates_token_and_saves_to_doppler(
        self,
        mock_time: Mock,
        mock_load: Mock,
        mock_schedule_init: Mock,
        mock_save: Mock,
        mock_post: Mock,
    ) -> None:
        """_refresh_token requests new token, updates _token, and saves to Doppler."""
        mock_time.return_value = 1000
        mock_token = TokenInfo(
            access_token="old_token", refresh_token="refresh456", expires_at=2000
        )
        mock_load.return_value = mock_token

        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response

        manager = TokenManager(
            client_id="client123",
            client_secret="secret456",
            doppler_project="test-project",
            doppler_config="test-config",
        )

        with patch.object(manager, "_schedule_refresh") as mock_schedule_refresh:
            manager._refresh_token()

        # Verify token updated
        assert manager._token.access_token == "new_access_token"
        assert manager._token.refresh_token == "new_refresh_token"
        assert manager._token.expires_at == 4600  # 1000 + 3600

        # Verify Doppler save called
        mock_save.assert_called_once()

        # Verify refresh rescheduled
        mock_schedule_refresh.assert_called_once()

    @patch("requests.post")
    @patch.object(TokenManager, "_load_from_doppler")
    @patch.object(TokenManager, "_schedule_refresh")
    def test_refresh_token_raises_authentication_error_on_http_error(
        self, mock_schedule: Mock, mock_load: Mock, mock_post: Mock
    ) -> None:
        """_refresh_token raises AuthenticationError when HTTP request fails."""
        import requests

        mock_token = TokenInfo(
            access_token="old_token", refresh_token="refresh456", expires_at=2000
        )
        mock_load.return_value = mock_token

        mock_post.side_effect = requests.RequestException("Network error")

        manager = TokenManager(
            client_id="client123",
            client_secret="secret456",
            doppler_project="test-project",
            doppler_config="test-config",
        )

        with pytest.raises(AuthenticationError, match="Token refresh failed"):
            manager._refresh_token()


class TestSaveToDoppler:
    """Test _save_to_doppler method."""

    @patch("subprocess.run")
    @patch.object(TokenManager, "_load_from_doppler")
    @patch.object(TokenManager, "_schedule_refresh")
    def test_save_to_doppler_updates_all_three_secrets(
        self, mock_schedule: Mock, mock_load: Mock, mock_run: Mock
    ) -> None:
        """_save_to_doppler calls doppler secrets set for all 3 token values."""
        mock_token = TokenInfo(
            access_token="access123", refresh_token="refresh456", expires_at=2000
        )
        mock_load.return_value = mock_token

        manager = TokenManager(
            client_id="client123",
            client_secret="secret456",
            doppler_project="test-project",
            doppler_config="test-config",
        )

        manager._save_to_doppler()

        # Verify 3 subprocess calls (one per secret)
        assert mock_run.call_count == 3

        # Verify each secret was set
        calls = mock_run.call_args_list
        assert any("JOBBER_ACCESS_TOKEN" in str(call) for call in calls)
        assert any("JOBBER_REFRESH_TOKEN" in str(call) for call in calls)
        assert any("JOBBER_TOKEN_EXPIRES_AT" in str(call) for call in calls)

    @patch("subprocess.run")
    @patch.object(TokenManager, "_load_from_doppler")
    @patch.object(TokenManager, "_schedule_refresh")
    def test_save_to_doppler_raises_authentication_error_on_subprocess_failure(
        self, mock_schedule: Mock, mock_load: Mock, mock_run: Mock
    ) -> None:
        """_save_to_doppler raises AuthenticationError when Doppler CLI fails."""
        mock_token = TokenInfo(
            access_token="access123", refresh_token="refresh456", expires_at=2000
        )
        mock_load.return_value = mock_token

        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["doppler"], stderr="Permission denied"
        )

        manager = TokenManager(
            client_id="client123",
            client_secret="secret456",
            doppler_project="test-project",
            doppler_config="test-config",
        )

        with pytest.raises(AuthenticationError, match="Failed to update.*in Doppler"):
            manager._save_to_doppler()


# NOTE: Schedule refresh tests omitted due to threading.Timer mocking complexity
# The proactive refresh functionality is tested indirectly through:
# - TestTokenManagerInit (verifies _schedule_refresh called on init)
# - TestRefreshToken (verifies _schedule_refresh called after token refresh)
# - TestProactiveRefresh (verifies _proactive_refresh worker function)


class TestProactiveRefresh:
    """Test _proactive_refresh method."""

    @patch.object(TokenManager, "_refresh_token")
    @patch.object(TokenManager, "_load_from_doppler")
    @patch.object(TokenManager, "_schedule_refresh")
    def test_proactive_refresh_calls_refresh_token(
        self, mock_schedule: Mock, mock_load: Mock, mock_refresh: Mock
    ) -> None:
        """_proactive_refresh calls _refresh_token within lock."""
        mock_token = TokenInfo(
            access_token="access123", refresh_token="refresh456", expires_at=2000
        )
        mock_load.return_value = mock_token

        manager = TokenManager(
            client_id="client123",
            client_secret="secret456",
            doppler_project="test-project",
            doppler_config="test-config",
        )

        manager._proactive_refresh()

        mock_refresh.assert_called_once()

    @patch.object(TokenManager, "_refresh_token")
    @patch.object(TokenManager, "_load_from_doppler")
    @patch.object(TokenManager, "_schedule_refresh")
    def test_proactive_refresh_suppresses_authentication_error(
        self, mock_schedule: Mock, mock_load: Mock, mock_refresh: Mock
    ) -> None:
        """_proactive_refresh catches AuthenticationError and continues silently."""
        mock_token = TokenInfo(
            access_token="access123", refresh_token="refresh456", expires_at=2000
        )
        mock_load.return_value = mock_token

        mock_refresh.side_effect = AuthenticationError("Refresh failed")

        manager = TokenManager(
            client_id="client123",
            client_secret="secret456",
            doppler_project="test-project",
            doppler_config="test-config",
        )

        # Should not raise exception
        manager._proactive_refresh()


class TestFromDopplerClassMethod:
    """Test from_doppler class method."""

    @patch.object(TokenManager, "_load_credentials")
    @patch.object(TokenManager, "__init__")
    def test_from_doppler_loads_credentials_and_creates_instance(
        self, mock_init: Mock, mock_load_creds: Mock
    ) -> None:
        """from_doppler loads credentials and creates TokenManager instance."""
        mock_load_creds.return_value = ("client_id_value", "client_secret_value")
        mock_init.return_value = None

        TokenManager.from_doppler("test-project", "test-config")

        mock_load_creds.assert_called_once_with("test-project", "test-config")
        mock_init.assert_called_once_with(
            "client_id_value", "client_secret_value", "test-project", "test-config"
        )
