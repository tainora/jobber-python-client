"""
Jobber GraphQL API client.

Main entry point for AI agents to interact with Jobber API.
"""

from typing import Any

from .auth import TokenManager
from .exceptions import AuthenticationError
from .graphql import GraphQLExecutor


class JobberClient:
    """
    Jobber GraphQL API client.

    Usage:
        client = JobberClient.from_doppler()  # Uses jobber/prd by default
        result = client.execute_query("{ clients { totalCount } }")

    Error handling:
        All methods raise exceptions on failure.
        Caller must handle:
        - AuthenticationError: Token invalid, run jobber_auth.py
        - RateLimitError: Too many requests, wait for restore
        - GraphQLError: Invalid query, check syntax
        - NetworkError: Connection failed, check network
    """

    def __init__(self, token_manager: TokenManager):
        """
        Initialize client with token manager.

        Args:
            token_manager: Configured TokenManager instance

        For typical usage, use JobberClient.from_doppler() instead.
        """
        self.token_manager = token_manager
        self._executor: GraphQLExecutor | None = None

    @classmethod
    def from_doppler(
        cls, doppler_project: str = "jobber", doppler_config: str = "prd"
    ) -> "JobberClient":
        """
        Create client loading credentials from Doppler.

        Args:
            doppler_project: Doppler project name (default: "jobber")
            doppler_config: Doppler config name (default: "prd")

        Returns:
            Configured JobberClient

        Raises:
            ConfigurationError: Doppler secrets not found
            AuthenticationError: Token loading fails

        Example:
            # Default (uses jobber/prd)
            client = JobberClient.from_doppler()

            # Custom project/config
            client = JobberClient.from_doppler("jobber", "dev")

            result = client.execute_query("{ clients { totalCount } }")
        """
        token_manager = TokenManager.from_doppler(doppler_project, doppler_config)
        return cls(token_manager)

    def execute_query(
        self, query: str, variables: dict[str, Any] | None = None, operation_name: str | None = None
    ) -> dict[str, Any]:
        """
        Execute GraphQL query.

        Args:
            query: GraphQL query string
            variables: Query variables (optional)
            operation_name: Operation name (optional)

        Returns:
            Response data (response['data'])

        Raises:
            AuthenticationError: Token invalid or expired
            RateLimitError: Rate limit threshold exceeded
            GraphQLError: Query execution failed
            NetworkError: HTTP request failed

        Example:
            result = client.execute_query('''
                query GetClients($first: Int) {
                    clients(first: $first) {
                        nodes { id name }
                    }
                }
            ''', variables={'first': 10})
        """
        # Get current valid token (may refresh if expired)
        access_token = self.token_manager.get_token()

        # Create executor with fresh token
        executor = GraphQLExecutor(access_token)

        try:
            return executor.execute(query, variables, operation_name)
        except AuthenticationError:
            # Token might have expired during request
            # Try refreshing and retrying once
            access_token = self.token_manager.refresh_on_401()
            executor = GraphQLExecutor(access_token)
            return executor.execute(query, variables, operation_name)

    def get_throttle_status(self) -> dict[str, int] | None:
        """
        Get last known rate limit status.

        Returns:
            Throttle status dict with keys:
            - currentlyAvailable: Points available now
            - maximumAvailable: Total point capacity (typically 10,000)
            - restoreRate: Points restored per second (typically 500)

            None if no queries executed yet

        Example:
            status = client.get_throttle_status()
            if status:
                print(f"{status['currentlyAvailable']} points available")
        """
        if self._executor is None:
            return None
        return self._executor.get_throttle_status()
