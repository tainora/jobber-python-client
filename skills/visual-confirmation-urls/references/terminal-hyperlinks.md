# Terminal Hyperlinks (ANSI OSC 8)

Modern terminals support clickable hyperlinks via ANSI OSC 8 escape codes. This enables better UX for CLI tools and scripts.

## The Problem

Traditional terminal output shows full URLs:

```
Created client: John Doe
View in Jobber: https://secure.getjobber.com/clients/12345678
```

**Issues**:
- Long URLs clutter output
- User must copy-paste URL to browser
- Noisy output with many URLs

## The Solution: OSC 8

ANSI OSC 8 (Operating System Command 8) enables clickable hyperlinks:

```python
# User sees: "View in Jobber" (clickable)
# Terminal stores: https://secure.getjobber.com/clients/12345678
# Click behavior: Cmd+Click opens URL
```

**Benefits**:
- Clean output (display text instead of full URL)
- Clickable (Cmd+Click or Ctrl+Click to open)
- Better UX (no copy-paste needed)

## OSC 8 Standard

**Format**:
```
ESC ] 8 ;; URL ESC \ TEXT ESC ] 8 ;; ESC \
```

**Components**:
- `ESC ] 8 ;;` - Start hyperlink
- `URL` - Target URL
- `ESC \` - String terminator
- `TEXT` - Clickable text (what user sees)
- `ESC ] 8 ;; ESC \` - End hyperlink

**Python Implementation**:
```python
def clickable_link(url: str, text: str | None = None) -> str:
    """
    Create ANSI hyperlink for terminal output.

    Args:
        url: Target URL
        text: Link text (defaults to URL if not provided)

    Returns:
        ANSI hyperlink string
    """
    display_text = text or url

    # OSC 8 format: \033]8;;URL\033\\TEXT\033]8;;\033\\
    return f"\033]8;;{url}\033\\{display_text}\033]8;;\033\\"


# Usage
print(clickable_link("https://example.com", "Example"))
# User sees: "Example" (clickable)
```

## Terminal Support

**Fully Supported** (Cmd+Click to open):
- ✅ iTerm2 (macOS)
- ✅ VSCode integrated terminal
- ✅ GNOME Terminal (Linux)
- ✅ Windows Terminal
- ✅ Hyper
- ✅ Warp

**Not Supported** (shows plain text):
- ❌ macOS Terminal.app (default terminal)
- ❌ PuTTY
- ❌ tmux (without pass-through)
- ❌ screen

**Graceful Fallback**: Unsupported terminals display text normally (no broken rendering).

## Implementation Examples

### Basic Usage

```python
from jobber.url_helpers import clickable_link

url = "https://secure.getjobber.com/clients/123"
print(f"View client: {clickable_link(url, 'John Doe')}")

# Output in iTerm2/VSCode: "View client: John Doe" (clickable)
# Output in Terminal.app: "View client: John Doe" (plain text)
```

### Success Messages

```python
from jobber.url_helpers import format_success

resource_data = {
    'id': '123',
    'name': 'John Doe',
    'jobberWebUri': 'https://secure.getjobber.com/clients/123'
}

# Uses clickable_link internally
message = format_success("Client", resource_data, name_field="name")
print(message)

# Output:
# ✅ Client created: John Doe
# 🔗 View in Jobber: https://... (clickable in supported terminals)
```

### Batch Results

```python
clients = [
    {'id': '1', 'name': 'Alice', 'jobberWebUri': 'https://...'},
    {'id': '2', 'name': 'Bob', 'jobberWebUri': 'https://...'},
    {'id': '3', 'name': 'Carol', 'jobberWebUri': 'https://...'},
]

print("Recent clients:")
for client in clients:
    link = clickable_link(client['jobberWebUri'], client['name'])
    print(f"  • {link}")

# Output: List of clickable names
```

## Error Handling

```python
def clickable_link(url: str, text: str | None = None) -> str:
    """Create ANSI hyperlink with error handling."""
    if not isinstance(url, str):
        raise TypeError(f"url must be str, got {type(url).__name__}")

    if text is not None and not isinstance(text, str):
        raise TypeError(f"text must be str or None, got {type(text).__name__}")

    display_text = text or url

    try:
        return f"\033]8;;{url}\033\\{display_text}\033]8;;\033\\"
    except (UnicodeEncodeError, ValueError):
        # Fallback to plain text if ANSI encoding fails
        return f"{display_text} ({url})" if text else url
```

**Error Cases**:
- **TypeError**: Invalid input types (not strings)
- **UnicodeEncodeError**: URL contains invalid characters (fallback to plain)
- **ValueError**: ANSI escape encoding fails (fallback to plain)

## Testing

**Manual Testing**:
```bash
# Test in iTerm2/VSCode terminal
uv run python -c "
from jobber.url_helpers import clickable_link
print(clickable_link('https://google.com', 'Google'))
"

# Cmd+Click "Google" → Should open browser
```

**Unit Testing**:
```python
import pytest
from jobber.url_helpers import clickable_link

def test_produces_ansi_osc8_format():
    """ANSI OSC 8 hyperlink format correctly generated."""
    result = clickable_link("https://example.com", "Example")

    # OSC 8 format: \033]8;;URL\033\\TEXT\033]8;;\033\\
    expected = "\033]8;;https://example.com\033\\Example\033]8;;\033\\"
    assert result == expected

def test_text_defaults_to_url_when_not_provided():
    """When text=None, uses URL as display text."""
    result = clickable_link("https://example.com")

    assert "https://example.com" in result
    assert "\033]8;;" in result  # ANSI codes present
```

See [`../../tests/test_url_helpers.py`](../../tests/test_url_helpers.py) for complete test suite (19 tests).

## CLI Integration

### Click Framework

```python
import click
from jobber.url_helpers import clickable_link

@click.command()
def create_client():
    """Create client with clickable URL."""
    result = client.execute_query(CREATE_CLIENT, variables)
    client_data = result['clientCreate']['client']

    click.echo(f"✅ Created: {client_data['firstName']}")
    click.echo(f"🔗 {clickable_link(client_data['jobberWebUri'], 'View in Jobber')}")
```

### argparse

```python
import argparse
from jobber.url_helpers import clickable_link

parser = argparse.ArgumentParser()
# ... argument setup ...

if __name__ == "__main__":
    args = parser.parse_args()
    result = create_client(args.name)

    print(f"✅ Created client!")
    print(f"🔗 {clickable_link(result['jobberWebUri'], 'View')}")
```

## API-Agnostic Usage

### GitHub

```python
issue = github.create_issue(repo="owner/repo", title="Bug")
print(f"Created issue: {clickable_link(issue['html_url'], f'#{issue['number']}')}")

# Output: "Created issue: #123" (clickable)
```

### Stripe

```python
charge = stripe.Charge.create(amount=1000, currency="usd")
print(f"Receipt: {clickable_link(charge['receipt_url'], 'View Receipt')}")

# Output: "Receipt: View Receipt" (clickable)
```

### Linear

```python
issue = linear.create_issue(title="Feature request")
print(f"Issue created: {clickable_link(issue['url'], issue['identifier'])}")

# Output: "Issue created: ENG-123" (clickable)
```

## Advanced: Custom Parameters

OSC 8 supports optional parameters for hover text, etc.:

```
ESC ] 8 ; params ; URL ESC \ TEXT ESC ] 8 ;; ESC \
```

**Example with ID parameter**:
```python
def clickable_link_with_id(url: str, text: str, link_id: str) -> str:
    """Hyperlink with ID parameter (for hover text, etc.)."""
    return f"\033]8;id={link_id};{url}\033\\{text}\033]8;;\033\\"

# Usage
print(clickable_link_with_id(
    "https://example.com",
    "Example",
    link_id="example-link-1"
))
```

**Note**: Parameter support varies by terminal.

## Debugging

**View raw escape codes**:
```bash
# Show ANSI codes (don't render)
uv run python -c "
from jobber.url_helpers import clickable_link
print(repr(clickable_link('https://google.com', 'Google')))
"

# Output: '\x1b]8;;https://google.com\x1b\\Google\x1b]8;;\x1b\\'
```

**Check terminal support**:
```bash
# Test if terminal supports OSC 8
printf '\e]8;;https://example.com\e\\Example\e]8;;\e\\\n'

# If supported: "Example" is clickable
# If not supported: "Example" is plain text
```

## References

- **OSC 8 Spec**: https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda
- **iTerm2 Documentation**: https://iterm2.com/documentation-escape-codes.html
- **Template Implementation**: [`../assets/url_helpers_template.py`](../assets/url_helpers_template.py)
- **Unit Tests**: [`../../tests/test_url_helpers.py`](../../tests/test_url_helpers.py)
- **Use Cases**: [`use-cases.md`](use-cases.md)

## Summary

ANSI OSC 8 enables clickable terminal links:

1. **Better UX**: Click instead of copy-paste
2. **Clean output**: Display text instead of full URLs
3. **Wide support**: iTerm2, VSCode, GNOME Terminal, Windows Terminal
4. **Graceful fallback**: Plain text in unsupported terminals

**Quick Start**:
```python
from jobber.url_helpers import clickable_link

print(clickable_link("https://example.com", "Example"))
# Cmd+Click to open in browser (supported terminals)
```
