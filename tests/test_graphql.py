"""Unit tests for jobber.graphql module (GraphQLExecutor)."""

from unittest.mock import Mock, patch

import pytest
import requests

from jobber.exceptions import AuthenticationError, GraphQLError, NetworkError, RateLimitError
from jobber.graphql import GraphQLExecutor


class TestGraphQLExecutorInit:
    """Test GraphQLExecutor initialization."""

    def test_init_stores_access_token(self) -> None:
        """__init__ stores access token for Authorization header."""
        executor = GraphQLExecutor(access_token="test_token_123")
        assert executor.access_token == "test_token_123"
        assert executor.last_throttle_status is None


class TestExecuteSuccessful:
    """Test successful GraphQL query execution."""

    @patch("requests.post")
    def test_execute_returns_data_on_successful_query(self, mock_post: Mock) -> None:
        """execute() returns response['data'] on successful query."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"account": {"id": "123", "name": "Test Account"}}
        }
        mock_post.return_value = mock_response

        executor = GraphQLExecutor(access_token="test_token")
        result = executor.execute("{ account { id name } }")

        assert result == {"account": {"id": "123", "name": "Test Account"}}

    @patch("requests.post")
    def test_execute_includes_variables_in_payload(self, mock_post: Mock) -> None:
        """execute() includes variables in request payload when provided."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"client": {"id": "456"}}}
        mock_post.return_value = mock_response

        executor = GraphQLExecutor(access_token="test_token")
        executor.execute("query($id: ID!) { client(id: $id) { id } }", variables={"id": "456"})

        # Verify variables were included in payload
        call_args = mock_post.call_args
        assert call_args[1]["json"]["variables"] == {"id": "456"}

    @patch("requests.post")
    def test_execute_includes_operation_name_in_payload(self, mock_post: Mock) -> None:
        """execute() includes operationName in request payload when provided."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"account": {"id": "123"}}}
        mock_post.return_value = mock_response

        executor = GraphQLExecutor(access_token="test_token")
        executor.execute(
            "query GetAccount { account { id } }", operation_name="GetAccount"
        )

        # Verify operationName was included in payload
        call_args = mock_post.call_args
        assert call_args[1]["json"]["operationName"] == "GetAccount"

    @patch("requests.post")
    def test_execute_sets_correct_headers(self, mock_post: Mock) -> None:
        """execute() sets Authorization, Content-Type, and API version headers."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {}}
        mock_post.return_value = mock_response

        executor = GraphQLExecutor(access_token="test_token_abc")
        executor.execute("{ account { id } }")

        # Verify headers
        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer test_token_abc"
        assert headers["Content-Type"] == "application/json"
        assert headers["X-JOBBER-GRAPHQL-VERSION"] == "2023-11-15"


class TestExecuteErrorHandling:
    """Test GraphQL executor error handling."""

    @patch("requests.post")
    def test_execute_raises_authentication_error_on_401(self, mock_post: Mock) -> None:
        """execute() raises AuthenticationError when response is 401."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        executor = GraphQLExecutor(access_token="invalid_token")

        with pytest.raises(AuthenticationError, match="Access token invalid or expired"):
            executor.execute("{ account { id } }")

    @patch("requests.post")
    def test_execute_raises_network_error_on_timeout(self, mock_post: Mock) -> None:
        """execute() raises NetworkError when request times out."""
        mock_post.side_effect = requests.Timeout("Request timeout")

        executor = GraphQLExecutor(access_token="test_token")

        with pytest.raises(NetworkError, match="Request timeout after 30 seconds"):
            executor.execute("{ account { id } }")

    @patch("requests.post")
    def test_execute_raises_network_error_on_connection_error(
        self, mock_post: Mock
    ) -> None:
        """execute() raises NetworkError when connection fails."""
        mock_post.side_effect = requests.ConnectionError("Connection refused")

        executor = GraphQLExecutor(access_token="test_token")

        with pytest.raises(NetworkError, match="Connection failed"):
            executor.execute("{ account { id } }")

    @patch("requests.post")
    def test_execute_raises_network_error_on_http_error(self, mock_post: Mock) -> None:
        """execute() raises NetworkError when HTTP status indicates error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_post.return_value = mock_response

        executor = GraphQLExecutor(access_token="test_token")

        with pytest.raises(NetworkError, match="HTTP 500"):
            executor.execute("{ account { id } }")

    @patch("requests.post")
    def test_execute_raises_network_error_on_invalid_json(self, mock_post: Mock) -> None:
        """execute() raises NetworkError when response is not valid JSON."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "<html>Error</html>"
        mock_post.return_value = mock_response

        executor = GraphQLExecutor(access_token="test_token")

        with pytest.raises(NetworkError, match="Invalid JSON response"):
            executor.execute("{ account { id } }")

    @patch("requests.post")
    def test_execute_raises_graphql_error_on_query_errors(self, mock_post: Mock) -> None:
        """execute() raises GraphQLError when response contains 'errors' field."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "errors": [{"message": "Field 'invalid' doesn't exist", "path": ["account"]}]
        }
        mock_post.return_value = mock_response

        executor = GraphQLExecutor(access_token="test_token")

        with pytest.raises(GraphQLError, match="GraphQL query failed"):
            executor.execute("{ account { invalid } }")

    @patch("requests.post")
    def test_execute_raises_graphql_error_on_missing_data_field(
        self, mock_post: Mock
    ) -> None:
        """execute() raises GraphQLError when response is missing 'data' field."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # No 'data' field
        mock_post.return_value = mock_response

        executor = GraphQLExecutor(access_token="test_token")

        with pytest.raises(GraphQLError, match="Response missing 'data' field"):
            executor.execute("{ account { id } }")


class TestRateLimiting:
    """Test rate limit threshold checking."""

    @patch("requests.post")
    def test_execute_stores_throttle_status_from_response(self, mock_post: Mock) -> None:
        """execute() stores throttle status from response extensions."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"account": {"id": "123"}},
            "extensions": {
                "cost": {
                    "throttleStatus": {
                        "currentlyAvailable": 9500,
                        "maximumAvailable": 10000,
                        "restoreRate": 500,
                    }
                }
            },
        }
        mock_post.return_value = mock_response

        executor = GraphQLExecutor(access_token="test_token")
        executor.execute("{ account { id } }")

        assert executor.last_throttle_status == {
            "currentlyAvailable": 9500,
            "maximumAvailable": 10000,
            "restoreRate": 500,
        }

    @patch("requests.post")
    def test_execute_raises_rate_limit_error_when_below_threshold(
        self, mock_post: Mock
    ) -> None:
        """execute() raises RateLimitError when available points < 20% threshold."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"account": {"id": "123"}},
            "extensions": {
                "cost": {
                    "throttleStatus": {
                        "currentlyAvailable": 1500,  # 15% of 10,000 (below 20% threshold)
                        "maximumAvailable": 10000,
                        "restoreRate": 500,
                    }
                }
            },
        }
        mock_post.return_value = mock_response

        executor = GraphQLExecutor(access_token="test_token")

        with pytest.raises(RateLimitError, match="Rate limit low"):
            executor.execute("{ account { id } }")

    @patch("requests.post")
    def test_execute_does_not_raise_when_above_threshold(self, mock_post: Mock) -> None:
        """execute() does not raise RateLimitError when available points >= 20%."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"account": {"id": "123"}},
            "extensions": {
                "cost": {
                    "throttleStatus": {
                        "currentlyAvailable": 3000,  # 30% of 10,000 (above 20% threshold)
                        "maximumAvailable": 10000,
                        "restoreRate": 500,
                    }
                }
            },
        }
        mock_post.return_value = mock_response

        executor = GraphQLExecutor(access_token="test_token")

        # Should not raise
        result = executor.execute("{ account { id } }")
        assert result == {"account": {"id": "123"}}

    @patch("requests.post")
    def test_execute_handles_missing_throttle_status_gracefully(
        self, mock_post: Mock
    ) -> None:
        """execute() handles missing throttle status without error."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"account": {"id": "123"}}
            # No 'extensions' field
        }
        mock_post.return_value = mock_response

        executor = GraphQLExecutor(access_token="test_token")

        # Should not raise
        result = executor.execute("{ account { id } }")
        assert result == {"account": {"id": "123"}}
        assert executor.last_throttle_status is None


class TestGetThrottleStatus:
    """Test get_throttle_status method."""

    def test_get_throttle_status_returns_none_initially(self) -> None:
        """get_throttle_status() returns None before any queries executed."""
        executor = GraphQLExecutor(access_token="test_token")
        assert executor.get_throttle_status() is None

    @patch("requests.post")
    def test_get_throttle_status_returns_last_status(self, mock_post: Mock) -> None:
        """get_throttle_status() returns last known throttle status after query."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"account": {"id": "123"}},
            "extensions": {
                "cost": {
                    "throttleStatus": {
                        "currentlyAvailable": 8000,
                        "maximumAvailable": 10000,
                        "restoreRate": 500,
                    }
                }
            },
        }
        mock_post.return_value = mock_response

        executor = GraphQLExecutor(access_token="test_token")
        executor.execute("{ account { id } }")

        status = executor.get_throttle_status()
        assert status == {
            "currentlyAvailable": 8000,
            "maximumAvailable": 10000,
            "restoreRate": 500,
        }


class TestCheckRateLimit:
    """Test _check_rate_limit internal method."""

    def test_check_rate_limit_raises_when_below_threshold(self) -> None:
        """_check_rate_limit() raises RateLimitError when points < 20% threshold."""
        executor = GraphQLExecutor(access_token="test_token")

        throttle = {
            "currentlyAvailable": 1000,  # 10% of 10,000
            "maximumAvailable": 10000,
            "restoreRate": 500,
        }

        with pytest.raises(RateLimitError):
            executor._check_rate_limit(throttle)

    def test_check_rate_limit_does_not_raise_when_above_threshold(self) -> None:
        """_check_rate_limit() does not raise when points >= 20% threshold."""
        executor = GraphQLExecutor(access_token="test_token")

        throttle = {
            "currentlyAvailable": 5000,  # 50% of 10,000
            "maximumAvailable": 10000,
            "restoreRate": 500,
        }

        # Should not raise
        executor._check_rate_limit(throttle)

    def test_check_rate_limit_calculates_wait_time_correctly(self) -> None:
        """_check_rate_limit() calculates correct wait time in error context."""
        executor = GraphQLExecutor(access_token="test_token")

        throttle = {
            "currentlyAvailable": 1000,  # Need 1000 more to reach 2000 (20%)
            "maximumAvailable": 10000,
            "restoreRate": 500,  # 500 points/second
        }

        with pytest.raises(RateLimitError) as exc_info:
            executor._check_rate_limit(throttle)

        # Wait time should be (2000 - 1000) / 500 = 2 seconds
        assert exc_info.value.context["wait_seconds"] == 2.0
