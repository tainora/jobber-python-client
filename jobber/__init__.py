"""
Jobber GraphQL API Python Client

Minimal client for Jobber API with OAuth 2.0 support.

Quick start:
    1. Run one-time authentication:
       $ uv run jobber_auth.py

    2. Use in AI agent code:
       from jobber import JobberClient

       client = JobberClient.from_doppler()
       result = client.execute_query("{ clients { totalCount } }")

Error handling:
    All methods raise exceptions on failure. Handle:
    - AuthenticationError: Re-run jobber_auth.py
    - RateLimitError: Wait for points to restore
    - GraphQLError: Check query syntax
    - NetworkError: Check connectivity
"""

from .client import JobberClient
from .exceptions import (
    AuthenticationError,
    ConfigurationError,
    GraphQLError,
    JobberException,
    NetworkError,
    RateLimitError,
)

__version__ = "0.1.0"

__all__ = [
    "JobberClient",
    "JobberException",
    "AuthenticationError",
    "RateLimitError",
    "GraphQLError",
    "NetworkError",
    "ConfigurationError",
]
