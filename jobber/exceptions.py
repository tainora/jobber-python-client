"""
Jobber API exception hierarchy.

All exceptions include context for debugging. No silent failures.
"""

from typing import Any


class JobberException(Exception):  # noqa: N818
    """
    Base exception for all Jobber API errors.

    Attributes:
        message: Human-readable error description
        context: Additional error context (request details, response, etc.)
    """

    def __init__(self, message: str, context: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} ({context_str})"
        return self.message


class AuthenticationError(JobberException):
    """
    OAuth authentication failed.

    Raised when:
    - Access token is invalid or expired
    - Token refresh fails
    - Credentials not found in Doppler

    Resolution:
    - Run jobber_auth.py to re-authenticate
    - Check Doppler credentials exist
    """

    pass


class RateLimitError(JobberException):
    """
    API rate limit threshold exceeded.

    Raised when:
    - Available points < threshold (default 20% of max)
    - Query would exceed available points

    Resolution:
    - Wait for points to restore (500 points/second)
    - Reduce query frequency
    - Check throttleStatus in exception context

    Attributes:
        throttle_status: Current rate limit status
    """

    def __init__(
        self,
        message: str,
        throttle_status: dict[str, int] | None = None,
        context: dict[str, Any] | None = None,
    ):
        super().__init__(message, context)
        self.throttle_status = throttle_status or {}


class GraphQLError(JobberException):
    """
    GraphQL query execution failed.

    Raised when:
    - Query syntax is invalid
    - Requested fields don't exist
    - Missing required arguments
    - Server-side validation fails

    Resolution:
    - Check query against GraphQL schema
    - Verify field names and types
    - Check errors list in exception context

    Attributes:
        errors: List of GraphQL error objects
        query: The failed query string
    """

    def __init__(
        self, message: str, errors: list, query: str, context: dict[str, Any] | None = None
    ):
        context = context or {}
        context.update({"errors": errors, "query": query})
        super().__init__(message, context)
        self.errors = errors
        self.query = query


class NetworkError(JobberException):
    """
    HTTP request failed.

    Raised when:
    - Connection timeout
    - DNS resolution fails
    - Server unreachable
    - SSL/TLS errors

    Resolution:
    - Check network connectivity
    - Verify Jobber API is accessible
    - Check firewall/proxy settings
    """

    pass


class ConfigurationError(JobberException):
    """
    Library configuration is invalid.

    Raised when:
    - Doppler project/config not found
    - Required secrets missing
    - Invalid configuration values

    Resolution:
    - Run jobber_auth.py
    - Verify Doppler project and config names
    - Check credentials in Doppler
    """

    pass
