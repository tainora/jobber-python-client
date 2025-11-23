"""
URL formatting utilities for visual confirmation pattern.

Provides helpers for:
- Formatting success messages with web links
- Creating ANSI hyperlinks for terminal output
- Validating jobberWebUri presence

Error handling: Fail-fast (raise on invalid input, caller decides recovery)
"""

from typing import Any


def format_success(
    resource_type: str,
    resource_data: dict[str, Any],
    name_field: str = "name"
) -> str:
    """
    Format success message with web link for visual confirmation.

    Args:
        resource_type: Resource type (e.g., "Client", "Job", "Quote")
        resource_data: Resource data dict (must contain 'id' and 'jobberWebUri')
        name_field: Field name for resource display name (default: "name")

    Returns:
        Formatted success message with web link

    Raises:
        TypeError: If resource_data is not a dict
        KeyError: If required fields missing (id, jobberWebUri)

    Example:
        >>> data = {'id': '123', 'name': 'John Doe', 'jobberWebUri': 'https://...'}
        >>> format_success("Client", data, name_field="name")
        '✅ Client created: John Doe
        🔗 View in Jobber: https://...'
    """
    if not isinstance(resource_data, dict):
        raise TypeError(f"resource_data must be dict, got {type(resource_data).__name__}")

    # Validate required fields (fail-fast)
    if 'id' not in resource_data:
        raise KeyError("resource_data missing required field: 'id'")

    if 'jobberWebUri' not in resource_data:
        raise KeyError(
            f"resource_data missing required field: 'jobberWebUri'. "
            f"Include this field in your GraphQL query for visual confirmation."
        )

    # Get display name (fallback to ID if name field missing)
    display_name = resource_data.get(name_field, resource_data['id'])

    return (
        f"✅ {resource_type} created: {display_name}\n"
        f"🔗 View in Jobber: {resource_data['jobberWebUri']}"
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

        In terminal: Shows "Example" as clickable link
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


def validate_url(resource_data: dict[str, Any], field: str = "jobberWebUri") -> str:
    """
    Validate that URL field is present in resource data.

    Use for URL-based validation: if jobberWebUri present, resource exists and is accessible.

    Args:
        resource_data: Resource data dict from API response
        field: URL field name (default: "jobberWebUri")

    Returns:
        URL string if present

    Raises:
        TypeError: If resource_data is not a dict
        KeyError: If URL field missing or null
        ValueError: If URL field is empty string

    Example:
        >>> data = {'id': '123', 'jobberWebUri': 'https://...'}
        >>> validate_url(data)
        'https://...'

        >>> validate_url({'id': '123'})
        KeyError: "jobberWebUri field missing or null..."
    """
    if not isinstance(resource_data, dict):
        raise TypeError(f"resource_data must be dict, got {type(resource_data).__name__}")

    if field not in resource_data or resource_data[field] is None:
        raise KeyError(
            f"{field} field missing or null. "
            f"Include '{field}' in your GraphQL query or check resource permissions."
        )

    url = resource_data[field]

    if not isinstance(url, str):
        raise TypeError(f"{field} must be str, got {type(url).__name__}")

    if not url.strip():
        raise ValueError(f"{field} is empty string")

    return url
