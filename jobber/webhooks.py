"""
Webhook signature validation and event parsing for Jobber GraphQL API.

Provides HMAC-SHA256 signature validation to verify webhook events are
authentic and parsers to convert JSON payloads into Python dictionaries.

Example usage:
    from jobber.webhooks import validate_signature, parse_event

    # Validate webhook signature
    if not validate_signature(request.data, request.headers['X-Jobber-Signature'], secret):
        raise ValueError("Invalid webhook signature")

    # Parse event payload
    event = parse_event(request.data)
    if event['event_type'] == QUOTE_APPROVED:
        handle_quote_approved(event['data'])
"""

import hashlib
import hmac
import json
from typing import Any

from .exceptions import JobberException

# Webhook event type constants
# Source: https://developer.getjobber.com/docs/webhooks
CLIENT_CREATE = "client.create"
CLIENT_UPDATE = "client.update"
CLIENT_DELETE = "client.delete"

QUOTE_CREATE = "quote.create"
QUOTE_UPDATE = "quote.update"
QUOTE_APPROVED = "quote.approved"
QUOTE_CONVERTED = "quote.converted"

VISIT_CREATE = "visit.create"
VISIT_UPDATE = "visit.update"
VISIT_COMPLETE = "visit.complete"
VISIT_DELETE = "visit.delete"

INVOICE_CREATE = "invoice.create"
INVOICE_UPDATE = "invoice.update"
INVOICE_PAID = "invoice.paid"
INVOICE_SENT = "invoice.sent"

JOB_CREATE = "job.create"
JOB_UPDATE = "job.update"
JOB_COMPLETE = "job.complete"

REQUEST_CREATE = "request.create"
REQUEST_UPDATE = "request.update"
REQUEST_APPROVED = "request.approved"


def validate_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Validate HMAC-SHA256 signature from Jobber webhook.

    Jobber sends webhook events with X-Jobber-Signature header containing
    HMAC-SHA256 digest. This function verifies the signature matches the
    payload to ensure the event is authentic and not spoofed.

    Args:
        payload: Raw webhook payload bytes (request body)
        signature: Signature from X-Jobber-Signature header (format: "sha256=<hex_digest>")
        secret: Webhook secret from Jobber Developer Portal (stored in Doppler)

    Returns:
        True if signature is valid, False otherwise

    Raises:
        ValueError: If signature format is invalid (not "sha256=..." format)

    Example:
        >>> payload = b'{"event_type": "quote.approved", "data": {...}}'
        >>> signature = "sha256=abc123..."
        >>> secret = "my_webhook_secret"
        >>> is_valid = validate_signature(payload, signature, secret)
        >>> if not is_valid:
        ...     raise ValueError("Invalid webhook signature")
    """
    if not signature.startswith("sha256="):
        raise ValueError(
            f"Invalid signature format: expected 'sha256=<hex_digest>', got '{signature}'"
        )

    # Extract hex digest from signature
    received_digest = signature[7:]  # Remove "sha256=" prefix

    # Compute expected digest
    expected_digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_digest, received_digest)


def parse_event(payload: bytes) -> dict[str, Any]:
    """
    Parse webhook event payload from JSON bytes to Python dictionary.

    Args:
        payload: Raw webhook payload bytes (request body)

    Returns:
        Dictionary with event data (includes 'event_type' and 'data' keys)

    Raises:
        JobberException: If payload is not valid JSON

    Example:
        >>> payload = b'{"event_type": "quote.approved", "data": {"id": "123", "client": {...}}}'
        >>> event = parse_event(payload)
        >>> event['event_type']
        'quote.approved'
        >>> event['data']['id']
        '123'
    """
    try:
        return json.loads(payload)  # type: ignore[no-any-return]
    except json.JSONDecodeError as e:
        raise JobberException(
            "Invalid webhook payload: not valid JSON",
            context={"payload": payload.decode("utf-8", errors="replace"), "error": str(e)},
        ) from e


__all__ = [
    # Functions
    "validate_signature",
    "parse_event",
    # Event type constants
    "CLIENT_CREATE",
    "CLIENT_UPDATE",
    "CLIENT_DELETE",
    "QUOTE_CREATE",
    "QUOTE_UPDATE",
    "QUOTE_APPROVED",
    "QUOTE_CONVERTED",
    "VISIT_CREATE",
    "VISIT_UPDATE",
    "VISIT_COMPLETE",
    "VISIT_DELETE",
    "INVOICE_CREATE",
    "INVOICE_UPDATE",
    "INVOICE_PAID",
    "INVOICE_SENT",
    "JOB_CREATE",
    "JOB_UPDATE",
    "JOB_COMPLETE",
    "REQUEST_CREATE",
    "REQUEST_UPDATE",
    "REQUEST_APPROVED",
]
