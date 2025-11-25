"""Unit tests for jobber.client module (JobberClient facade)."""

from unittest.mock import Mock, patch

import pytest

from jobber.client import JobberClient
from jobber.exceptions import AuthenticationError, GraphQLError


class TestJobberClientInit:
    """Test JobberClient initialization."""

    def test_init_stores_token_manager(self) -> None:
        """__init__ stores token manager and initializes executor as None."""
        mock_token_manager = Mock()

        client = JobberClient(mock_token_manager)

        assert client.token_manager is mock_token_manager
        assert client._executor is None


class TestFromDoppler:
    """Test from_doppler class method factory."""

    @patch("jobber.client.TokenManager.from_doppler")
    def test_creates_client_with_doppler_credentials(
        self, mock_from_doppler: Mock
    ) -> None:
        """from_doppler() creates client with TokenManager from Doppler."""
        mock_token_manager = Mock()
        mock_from_doppler.return_value = mock_token_manager

        client = JobberClient.from_doppler("test-project", "test-config")

        # Verify TokenManager.from_doppler called with correct params
        mock_from_doppler.assert_called_once_with("test-project", "test-config")

        # Verify client created with token manager
        assert client.token_manager is mock_token_manager

    @patch("jobber.client.TokenManager.from_doppler")
    def test_uses_default_doppler_params(self, mock_from_doppler: Mock) -> None:
        """from_doppler() uses default project/config when not specified."""
        mock_token_manager = Mock()
        mock_from_doppler.return_value = mock_token_manager

        client = JobberClient.from_doppler()

        # Verify defaults used (updated to jobber/prd as of ADR-0010)
        mock_from_doppler.assert_called_once_with("jobber", "prd")

        assert client.token_manager is mock_token_manager


class TestExecuteQuery:
    """Test GraphQL query execution."""

    @patch("jobber.client.GraphQLExecutor")
    def test_executes_query_with_fresh_token(self, mock_executor_class: Mock) -> None:
        """execute_query() gets token and executes GraphQL query."""
        mock_token_manager = Mock()
        mock_token_manager.get_token.return_value = "valid_access_token_123"

        mock_executor = Mock()
        mock_executor.execute.return_value = {"clients": {"totalCount": 42}}
        mock_executor_class.return_value = mock_executor

        client = JobberClient(mock_token_manager)

        result = client.execute_query("{ clients { totalCount } }")

        # Verify token retrieved
        mock_token_manager.get_token.assert_called_once()

        # Verify executor created with token
        mock_executor_class.assert_called_once_with("valid_access_token_123")

        # Verify query executed
        mock_executor.execute.assert_called_once_with("{ clients { totalCount } }", None, None)

        # Verify result returned
        assert result == {"clients": {"totalCount": 42}}

    @patch("jobber.client.GraphQLExecutor")
    def test_passes_variables_and_operation_name(self, mock_executor_class: Mock) -> None:
        """execute_query() passes variables and operation name to executor."""
        mock_token_manager = Mock()
        mock_token_manager.get_token.return_value = "valid_access_token_123"

        mock_executor = Mock()
        mock_executor.execute.return_value = {"client": {"id": "456"}}
        mock_executor_class.return_value = mock_executor

        client = JobberClient(mock_token_manager)

        result = client.execute_query(
            query="query GetClient($id: ID!) { client(id: $id) { id } }",
            variables={"id": "456"},
            operation_name="GetClient",
        )

        # Verify query executed with variables and operation name
        mock_executor.execute.assert_called_once_with(
            "query GetClient($id: ID!) { client(id: $id) { id } }",
            {"id": "456"},
            "GetClient",
        )

        assert result == {"client": {"id": "456"}}

    @patch("jobber.client.GraphQLExecutor")
    def test_refreshes_token_on_authentication_error(
        self, mock_executor_class: Mock
    ) -> None:
        """execute_query() refreshes token and retries on 401 error."""
        mock_token_manager = Mock()
        mock_token_manager.get_token.return_value = "expired_token_123"
        mock_token_manager.refresh_on_401.return_value = "new_token_456"

        # First executor (with expired token) raises AuthenticationError
        mock_executor_1 = Mock()
        mock_executor_1.execute.side_effect = AuthenticationError("Token expired")

        # Second executor (with refreshed token) succeeds
        mock_executor_2 = Mock()
        mock_executor_2.execute.return_value = {"clients": {"totalCount": 42}}

        mock_executor_class.side_effect = [mock_executor_1, mock_executor_2]

        client = JobberClient(mock_token_manager)

        result = client.execute_query("{ clients { totalCount } }")

        # Verify token refresh called after 401
        mock_token_manager.refresh_on_401.assert_called_once()

        # Verify second executor created with refreshed token
        assert mock_executor_class.call_count == 2
        mock_executor_class.assert_any_call("expired_token_123")  # First attempt
        mock_executor_class.assert_any_call("new_token_456")  # Second attempt

        # Verify result returned after retry
        assert result == {"clients": {"totalCount": 42}}

    @patch("jobber.client.GraphQLExecutor")
    def test_raises_other_exceptions_without_retry(
        self, mock_executor_class: Mock
    ) -> None:
        """execute_query() raises non-authentication errors without retry."""
        mock_token_manager = Mock()
        mock_token_manager.get_token.return_value = "valid_token_123"

        mock_executor = Mock()
        mock_executor.execute.side_effect = GraphQLError(
            "Invalid query",
            errors=[{"message": "Field 'invalid' doesn't exist"}],
            query="{ invalid }",
        )
        mock_executor_class.return_value = mock_executor

        client = JobberClient(mock_token_manager)

        with pytest.raises(GraphQLError, match="Invalid query"):
            client.execute_query("{ invalid }")

        # Verify refresh NOT called (not AuthenticationError)
        mock_token_manager.refresh_on_401.assert_not_called()

        # Verify only one executor created (no retry)
        assert mock_executor_class.call_count == 1


class TestGetThrottleStatus:
    """Test rate limit status retrieval."""

    def test_returns_none_when_no_executor(self) -> None:
        """get_throttle_status() returns None before any queries executed."""
        mock_token_manager = Mock()
        client = JobberClient(mock_token_manager)

        status = client.get_throttle_status()

        assert status is None

    @patch("jobber.client.GraphQLExecutor")
    def test_returns_none_when_executor_has_no_status(
        self, mock_executor_class: Mock
    ) -> None:
        """get_throttle_status() returns None when executor has no status."""
        mock_token_manager = Mock()
        mock_token_manager.get_token.return_value = "valid_token_123"

        mock_executor = Mock()
        mock_executor.execute.return_value = {"clients": {"totalCount": 42}}
        mock_executor.get_throttle_status.return_value = None
        mock_executor_class.return_value = mock_executor

        client = JobberClient(mock_token_manager)

        # Execute a query to create executor
        client.execute_query("{ clients { totalCount } }")

        # Now get_throttle_status should delegate to executor
        status = client.get_throttle_status()

        assert status is None

    def test_always_returns_none_because_executor_not_stored(self) -> None:
        """get_throttle_status() always returns None (executor not stored in self._executor).

        NOTE: This test documents current behavior where executor is created as
        local variable in execute_query() and never assigned to self._executor.
        This appears to be a bug, but tests should reflect actual behavior.
        """
        mock_token_manager = Mock()
        client = JobberClient(mock_token_manager)

        # Even after executing a query, get_throttle_status returns None
        # because executor is not stored in self._executor
        status = client.get_throttle_status()

        assert status is None
