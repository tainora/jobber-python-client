"""
Tests for exception hierarchy.
"""

import pytest

from jobber.exceptions import (
    JobberException,
    AuthenticationError,
    RateLimitError,
    GraphQLError,
    NetworkError,
    ConfigurationError,
)


def test_base_exception():
    """Test JobberException base class"""
    exc = JobberException("test error", context={'key': 'value'})

    assert str(exc) == "test error (key=value)"
    assert exc.message == "test error"
    assert exc.context == {'key': 'value'}


def test_exception_without_context():
    """Test exception without context"""
    exc = JobberException("simple error")

    assert str(exc) == "simple error"
    assert exc.context == {}


def test_authentication_error():
    """Test AuthenticationError inherits from JobberException"""
    exc = AuthenticationError("token expired")

    assert isinstance(exc, JobberException)
    assert str(exc) == "token expired"


def test_rate_limit_error():
    """Test RateLimitError includes throttle status"""
    throttle = {
        'currentlyAvailable': 1000,
        'maximumAvailable': 10000,
        'restoreRate': 500
    }
    exc = RateLimitError("rate limit exceeded", throttle_status=throttle)

    assert isinstance(exc, JobberException)
    assert exc.throttle_status == throttle


def test_graphql_error():
    """Test GraphQLError includes errors and query"""
    errors = [{'message': 'Field not found'}]
    query = "{ invalid { field } }"

    exc = GraphQLError("query failed", errors=errors, query=query)

    assert isinstance(exc, JobberException)
    assert exc.errors == errors
    assert exc.query == query
    assert 'errors' in exc.context
    assert 'query' in exc.context


def test_network_error():
    """Test NetworkError"""
    exc = NetworkError("connection timeout")

    assert isinstance(exc, JobberException)
    assert str(exc) == "connection timeout"


def test_configuration_error():
    """Test ConfigurationError"""
    exc = ConfigurationError("doppler not found")

    assert isinstance(exc, JobberException)
    assert str(exc) == "doppler not found"
