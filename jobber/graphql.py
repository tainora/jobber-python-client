"""
GraphQL query executor for Jobber API.

Handles:
- HTTP requests to GraphQL endpoint
- Rate limit threshold checking
- Error parsing and exception raising

Error handling:
- Raises on any error (no retry)
- Exposes throttle status for caller inspection
"""

from typing import Any, cast

import requests

from .exceptions import AuthenticationError, GraphQLError, NetworkError, RateLimitError


class GraphQLExecutor:
    """
    Execute GraphQL queries against Jobber API.

    Responsibilities:
    - Format and send GraphQL requests
    - Parse responses and extract data
    - Check rate limits and raise if low
    - Surface throttle status to caller
    """

    API_URL = "https://api.getjobber.com/api/graphql"
    API_VERSION = "2023-11-15"
    RATE_LIMIT_THRESHOLD = 0.20  # Raise exception if < 20% points available

    def __init__(self, access_token: str):
        """
        Initialize GraphQL executor.

        Args:
            access_token: OAuth access token for Authorization header
        """
        self.access_token = access_token
        self.last_throttle_status: dict[str, int] | None = None

    def execute(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        operation_name: str | None = None
    ) -> dict[str, Any]:
        """
        Execute GraphQL query.

        Args:
            query: GraphQL query string
            variables: Query variables
            operation_name: Optional operation name

        Returns:
            Response data dict (response['data'])

        Raises:
            NetworkError: HTTP request failed
            GraphQLError: Query execution failed
            RateLimitError: Rate limit threshold exceeded
            AuthenticationError: Token invalid (401)
        """
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-JOBBER-GRAPHQL-VERSION': self.API_VERSION
        }

        payload: dict[str, Any] = {'query': query}
        if variables:
            payload['variables'] = variables
        if operation_name:
            payload['operationName'] = operation_name

        try:
            response = requests.post(
                self.API_URL,
                json=payload,
                headers=headers,
                timeout=30
            )

            # Check for authentication errors
            if response.status_code == 401:
                raise AuthenticationError(
                    "Access token invalid or expired",
                    context={'status_code': 401}
                )

            # Check for other HTTP errors
            response.raise_for_status()

        except requests.Timeout as e:
            raise NetworkError(
                "Request timeout after 30 seconds",
                context={'url': self.API_URL}
            ) from e
        except requests.ConnectionError as e:
            raise NetworkError(
                f"Connection failed: {e}",
                context={'url': self.API_URL}
            ) from e
        except requests.HTTPError as e:
            raise NetworkError(
                f"HTTP {response.status_code}: {response.text}",
                context={'status_code': response.status_code, 'response': response.text}
            ) from e

        # Parse JSON response
        try:
            result = response.json()
        except ValueError as e:
            raise NetworkError(
                f"Invalid JSON response: {response.text}",
                context={'response': response.text}
            ) from e

        # Extract rate limit info
        if 'extensions' in result and 'cost' in result['extensions']:
            cost = result['extensions']['cost']
            if 'throttleStatus' in cost:
                self.last_throttle_status = cost['throttleStatus']
                self._check_rate_limit(self.last_throttle_status)

        # Check for GraphQL errors
        if 'errors' in result:
            raise GraphQLError(
                f"GraphQL query failed: {result['errors'][0].get('message', 'Unknown error')}",
                errors=result['errors'],
                query=query,
                context={'variables': variables}
            )

        # Return data
        if 'data' not in result:
            raise GraphQLError(
                "Response missing 'data' field",
                errors=[],
                query=query,
                context={'response': result}
            )

        return cast(dict[str, Any], result['data'])

    def get_throttle_status(self) -> dict[str, int] | None:
        """
        Get last known rate limit status.

        Returns:
            Throttle status dict with keys:
            - currentlyAvailable: Points available now
            - maximumAvailable: Total point capacity
            - restoreRate: Points restored per second

            None if no queries executed yet
        """
        return self.last_throttle_status

    def _check_rate_limit(self, throttle: dict[str, int]) -> None:
        """
        Check if rate limit is below threshold.

        Args:
            throttle: Throttle status from API response

        Raises:
            RateLimitError: Available points < threshold
        """
        currently_available = throttle.get('currentlyAvailable', 0)
        maximum_available = throttle.get('maximumAvailable', 10000)

        threshold = self.RATE_LIMIT_THRESHOLD * maximum_available

        if currently_available < threshold:
            restore_rate = throttle.get('restoreRate', 500)
            wait_seconds = (threshold - currently_available) / restore_rate

            raise RateLimitError(
                f"Rate limit low: {currently_available}/{maximum_available} points available. "
                f"Wait {wait_seconds:.1f}s for points to restore.",
                throttle_status=throttle,
                context={'wait_seconds': wait_seconds, 'threshold_pct': self.RATE_LIMIT_THRESHOLD}
            )
