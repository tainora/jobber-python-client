"""
GraphQL query executor template (API-agnostic).

Handles:
- HTTP requests to GraphQL endpoint
- Rate limit threshold checking
- Error parsing and exception raising
- Custom headers support
- Pluggable rate limit strategies

Error handling: Fail-fast (raise on any error, no retry)

API-agnostic implementation - configure for your GraphQL API:
- Jobber: api_url="https://api.getjobber.com/api/graphql", custom_headers={"X-JOBBER-GRAPHQL-VERSION": "2023-11-15"}
- Shopify: api_url="https://{shop}.myshopify.com/admin/api/2024-01/graphql.json"
- GitHub: api_url="https://api.github.com/graphql"
- Stripe: api_url="https://api.stripe.com/graphql"
"""

from typing import Any, cast, Callable

import requests


# Exception hierarchy (customize for your application)

class GraphQLException(Exception):
    """Base exception for GraphQL errors."""

    def __init__(self, message: str, context: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}


class NetworkError(GraphQLException):
    """HTTP request failed (timeout, connection error, HTTP error)."""
    pass


class AuthenticationError(GraphQLException):
    """Authentication failed (401, invalid token)."""
    pass


class GraphQLError(GraphQLException):
    """GraphQL query execution failed."""

    def __init__(
        self,
        message: str,
        errors: list[dict[str, Any]],
        query: str,
        context: dict[str, Any] | None = None
    ):
        super().__init__(message, context)
        self.errors = errors
        self.query = query


class RateLimitError(GraphQLException):
    """Rate limit threshold exceeded."""

    def __init__(
        self,
        message: str,
        throttle_status: dict[str, int],
        context: dict[str, Any] | None = None
    ):
        super().__init__(message, context)
        self.throttle_status = throttle_status


# GraphQL Executor

class GraphQLExecutor:
    """
    Execute GraphQL queries against any GraphQL API.

    Responsibilities:
    - Format and send GraphQL requests
    - Parse responses and extract data
    - Check rate limits and raise if low
    - Surface throttle status to caller
    """

    def __init__(
        self,
        access_token: str,
        api_url: str = "https://api.example.com/graphql",
        api_version: str | None = None,
        rate_limit_threshold: float = 0.20,
        custom_headers: dict[str, str] | None = None,
        throttle_extractor: Callable[[dict[str, Any]], dict[str, int] | None] | None = None
    ):
        """
        Initialize GraphQL executor.

        Args:
            access_token: OAuth access token for Authorization header
            api_url: GraphQL endpoint URL
            api_version: API version (optional, added to custom_headers if provided)
            rate_limit_threshold: Raise exception if available points < threshold (0.0-1.0)
            custom_headers: Additional headers to include in requests
            throttle_extractor: Function to extract throttle status from response
                                (default: extracts from extensions.cost.throttleStatus)
        """
        self.access_token = access_token
        self.api_url = api_url
        self.api_version = api_version
        self.rate_limit_threshold = rate_limit_threshold
        self.custom_headers = custom_headers or {}
        self.throttle_extractor = throttle_extractor or self._default_throttle_extractor
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
            **self.custom_headers
        }

        payload: dict[str, Any] = {'query': query}
        if variables:
            payload['variables'] = variables
        if operation_name:
            payload['operationName'] = operation_name

        try:
            response = requests.post(
                self.api_url,
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
                context={'url': self.api_url}
            ) from e
        except requests.ConnectionError as e:
            raise NetworkError(
                f"Connection failed: {e}",
                context={'url': self.api_url}
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

        # Extract rate limit info using pluggable extractor
        throttle_status = self.throttle_extractor(result)
        if throttle_status:
            self.last_throttle_status = throttle_status
            self._check_rate_limit(throttle_status)

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

        threshold = self.rate_limit_threshold * maximum_available

        if currently_available < threshold:
            restore_rate = throttle.get('restoreRate', 500)
            wait_seconds = (threshold - currently_available) / restore_rate

            raise RateLimitError(
                f"Rate limit low: {currently_available}/{maximum_available} points available. "
                f"Wait {wait_seconds:.1f}s for points to restore.",
                throttle_status=throttle,
                context={'wait_seconds': wait_seconds, 'threshold_pct': self.rate_limit_threshold}
            )

    @staticmethod
    def _default_throttle_extractor(result: dict[str, Any]) -> dict[str, int] | None:
        """
        Default throttle status extractor (Jobber/Shopify format).

        Extracts from: extensions.cost.throttleStatus

        Args:
            result: GraphQL response dict

        Returns:
            Throttle status or None if not present
        """
        if 'extensions' in result and 'cost' in result['extensions']:
            cost = result['extensions']['cost']
            if 'throttleStatus' in cost:
                return cost['throttleStatus']
        return None


# API-specific configurations

def create_jobber_executor(access_token: str) -> GraphQLExecutor:
    """Create GraphQL executor for Jobber API."""
    return GraphQLExecutor(
        access_token=access_token,
        api_url="https://api.getjobber.com/api/graphql",
        custom_headers={"X-JOBBER-GRAPHQL-VERSION": "2023-11-15"},
        rate_limit_threshold=0.20
    )


def create_shopify_executor(access_token: str, shop_domain: str) -> GraphQLExecutor:
    """Create GraphQL executor for Shopify Admin API."""
    return GraphQLExecutor(
        access_token=access_token,
        api_url=f"https://{shop_domain}/admin/api/2024-01/graphql.json",
        rate_limit_threshold=0.25
    )


def create_github_executor(access_token: str) -> GraphQLExecutor:
    """
    Create GraphQL executor for GitHub API.

    Note: GitHub uses different throttle format (data.rateLimit).
    """

    def github_throttle_extractor(result: dict[str, Any]) -> dict[str, int] | None:
        """Extract rate limit from GitHub format (data.rateLimit)."""
        if 'data' in result and 'rateLimit' in result['data']:
            rate_limit = result['data']['rateLimit']
            return {
                'currentlyAvailable': rate_limit.get('remaining', 0),
                'maximumAvailable': rate_limit.get('limit', 5000),
                'restoreRate': 5000 // 3600  # GitHub resets hourly
            }
        return None

    return GraphQLExecutor(
        access_token=access_token,
        api_url="https://api.github.com/graphql",
        rate_limit_threshold=0.30,
        throttle_extractor=github_throttle_extractor
    )


def create_stripe_executor(access_token: str) -> GraphQLExecutor:
    """Create GraphQL executor for Stripe API."""
    return GraphQLExecutor(
        access_token=access_token,
        api_url="https://api.stripe.com/graphql",
        rate_limit_threshold=0.20
    )


# Usage examples

def example_basic_usage():
    """Basic GraphQL query execution."""
    executor = GraphQLExecutor(
        access_token="your_token",
        api_url="https://api.example.com/graphql"
    )

    query = """
        query GetUsers {
            users(first: 10) {
                nodes {
                    id
                    name
                }
            }
        }
    """

    result = executor.execute(query)
    users = result['users']['nodes']

    for user in users:
        print(f"{user['name']}")


def example_with_variables():
    """Query with variables."""
    executor = create_jobber_executor(access_token="your_token")

    query = """
        query GetClient($id: ID!) {
            client(id: $id) {
                id
                firstName
                lastName
            }
        }
    """

    variables = {'id': 'gid://jobber/Client/123'}
    result = executor.execute(query, variables)
    print(f"Client: {result['client']['firstName']}")


def example_rate_limit_check():
    """Check rate limit status."""
    executor = create_shopify_executor(
        access_token="your_token",
        shop_domain="your-shop.myshopify.com"
    )

    query = "query { shop { name } }"
    result = executor.execute(query)

    # Check throttle status
    throttle = executor.get_throttle_status()
    if throttle:
        available = throttle['currentlyAvailable']
        maximum = throttle['maximumAvailable']
        print(f"Rate limit: {available}/{maximum} ({available/maximum*100:.1f}%)")
