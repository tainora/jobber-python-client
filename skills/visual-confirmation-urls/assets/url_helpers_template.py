"""
URL formatting utilities for visual confirmation pattern.

Provides helpers for:
- Formatting success messages with web links
- Creating ANSI hyperlinks for terminal output
- Validating URL field presence in API responses

Error handling: Fail-fast (raise on invalid input, caller decides recovery)

API-agnostic implementation - configure field names for your API:
- Jobber: url_field="jobberWebUri"
- Stripe: url_field="receipt_url" or "hosted_invoice_url"
- GitHub: url_field="html_url"
- Linear: url_field="url"
"""

from typing import Any


def format_success(
    resource_type: str,
    resource_data: dict[str, Any],
    name_field: str = "name",
    url_field: str = "web_url",
    service_name: str = "Web UI"
) -> str:
    """
    Format success message with web link for visual confirmation.

    Args:
        resource_type: Resource type (e.g., "Client", "Issue", "Invoice")
        resource_data: Resource data dict (must contain 'id' and url_field)
        name_field: Field name for resource display name (default: "name")
        url_field: Field name for web URL (default: "web_url")
        service_name: Service name for display (default: "Web UI")

    Returns:
        Formatted success message with web link

    Raises:
        TypeError: If resource_data is not a dict
        KeyError: If required fields missing (id, url_field)

    Examples:
        # Jobber
        >>> data = {'id': '123', 'name': 'John Doe', 'jobberWebUri': 'https://...'}
        >>> format_success("Client", data, url_field="jobberWebUri", service_name="Jobber")
        '✅ Client created: John Doe\\n🔗 View in Jobber: https://...'

        # GitHub
        >>> data = {'id': 123, 'title': 'Bug fix', 'html_url': 'https://github.com/...'}
        >>> format_success("Issue", data, name_field="title", url_field="html_url", service_name="GitHub")
        '✅ Issue created: Bug fix\\n🔗 View in GitHub: https://github.com/...'

        # Stripe
        >>> data = {'id': 'ch_123', 'amount': 1000, 'receipt_url': 'https://...'}
        >>> format_success("Charge", data, name_field="id", url_field="receipt_url", service_name="Stripe")
        '✅ Charge created: ch_123\\n🔗 View in Stripe: https://...'
    """
    if not isinstance(resource_data, dict):
        raise TypeError(f"resource_data must be dict, got {type(resource_data).__name__}")

    # Validate required fields (fail-fast)
    if 'id' not in resource_data:
        raise KeyError("resource_data missing required field: 'id'")

    if url_field not in resource_data:
        raise KeyError(
            f"resource_data missing required field: '{url_field}'. "
            f"Include this field in your API request for visual confirmation."
        )

    # Get display name (fallback to ID if name field missing)
    display_name = resource_data.get(name_field, resource_data['id'])

    return (
        f"✅ {resource_type} created: {display_name}\n"
        f"🔗 View in {service_name}: {resource_data[url_field]}"
    )


def clickable_link(url: str, text: str | None = None) -> str:
    """
    Create ANSI hyperlink for terminal output.

    Follows OSC 8 standard for terminal hyperlinks. Supported in:
    - iTerm2 (macOS)
    - VSCode integrated terminal
    - GNOME Terminal
    - Windows Terminal

    Falls back gracefully to plain URL in unsupported terminals.

    Args:
        url: Target URL
        text: Link text (defaults to URL if not provided)

    Returns:
        ANSI hyperlink string (or plain URL if ANSI encoding fails)

    Raises:
        TypeError: If url or text are not strings

    Example:
        >>> clickable_link("https://example.com", "Example")
        '\\x1b]8;;https://example.com\\x1b\\\\Example\\x1b]8;;\\x1b\\\\'

        In terminal: Shows "Example" as clickable link (Cmd+Click to open)
    """
    if not isinstance(url, str):
        raise TypeError(f"url must be str, got {type(url).__name__}")

    if text is not None and not isinstance(text, str):
        raise TypeError(f"text must be str or None, got {type(text).__name__}")

    display_text = text or url

    try:
        # OSC 8 hyperlink format: \033]8;;URL\033\\TEXT\033]8;;\033\\
        # \033 = ESC character
        # ]8;; = OSC 8 hyperlink start
        # URL\033\\ = URL followed by ST (string terminator)
        # TEXT = clickable text
        # \033]8;;\033\\ = OSC 8 hyperlink end
        return f"\033]8;;{url}\033\\{display_text}\033]8;;\033\\"

    except (UnicodeEncodeError, ValueError):
        # Fallback to plain URL if ANSI encoding fails
        return f"{display_text} ({url})" if text else url


def validate_url(
    resource_data: dict[str, Any],
    field: str = "web_url"
) -> str:
    """
    Validate that URL field is present in resource data.

    Use for URL-based validation: if web URL present, resource exists and is accessible.

    Args:
        resource_data: Resource data dict from API response
        field: URL field name (default: "web_url")
               - Jobber: "jobberWebUri" or "previewUrl"
               - GitHub: "html_url"
               - Stripe: "receipt_url", "hosted_invoice_url"
               - Linear: "url"

    Returns:
        URL string if present

    Raises:
        TypeError: If resource_data is not a dict
        KeyError: If URL field missing or null
        ValueError: If URL field is empty string

    Examples:
        # Jobber
        >>> data = {'id': '123', 'jobberWebUri': 'https://...'}
        >>> validate_url(data, field="jobberWebUri")
        'https://...'

        # GitHub
        >>> data = {'id': 123, 'html_url': 'https://github.com/...'}
        >>> validate_url(data, field="html_url")
        'https://github.com/...'

        # Missing field
        >>> validate_url({'id': '123'}, field="web_url")
        KeyError: "web_url field missing or null..."
    """
    if not isinstance(resource_data, dict):
        raise TypeError(f"resource_data must be dict, got {type(resource_data).__name__}")

    if field not in resource_data or resource_data[field] is None:
        raise KeyError(
            f"{field} field missing or null. "
            f"Include '{field}' in your API request or check resource permissions."
        )

    url = resource_data[field]

    if not isinstance(url, str):
        raise TypeError(f"{field} must be str, got {type(url).__name__}")

    if not url.strip():
        raise ValueError(f"{field} is empty string")

    return url


# API-specific configuration examples

# Jobber configuration
JOBBER_CONFIG = {
    "url_field": "jobberWebUri",
    "service_name": "Jobber",
    "name_fields": {
        "Client": "name",
        "Job": "title",
        "Quote": "quoteNumber",
        "Invoice": "invoiceNumber"
    }
}

# Stripe configuration
STRIPE_CONFIG = {
    "url_fields": {
        "Charge": "receipt_url",
        "Invoice": "hosted_invoice_url",
        "PaymentIntent": "receipt_url"
    },
    "service_name": "Stripe Dashboard"
}

# GitHub configuration
GITHUB_CONFIG = {
    "url_field": "html_url",
    "service_name": "GitHub",
    "name_fields": {
        "Issue": "title",
        "PullRequest": "title",
        "Commit": "sha"
    }
}

# Linear configuration
LINEAR_CONFIG = {
    "url_field": "url",
    "service_name": "Linear",
    "name_fields": {
        "Issue": "title",
        "Project": "name"
    }
}
