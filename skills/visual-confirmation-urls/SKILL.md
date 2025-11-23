---
name: visual-confirmation-urls
description: Get web UI links from APIs for instant visual verification. Use when creating resources via API and need clickable links to verify in web interface (Jobber, Stripe, GitHub, Linear).
---

# Visual Confirmation URLs

**Quick Win Validation**: Get web UI links from APIs for visual confirmation of operations.

## Problem Statement

API operations can feel abstract without visual confirmation. Users create resources via API but have no immediate way to verify they exist in the web interface. This creates uncertainty and requires manual navigation.

**User Question**: "Can I see what I just created via API in the web interface?"

**Answer**: YES! Include web URL fields in your API requests.

## Solution

Many modern APIs return web URL fields that link directly to resources in their web interfaces:

- **Jobber**: `jobberWebUri` field on most resources
- **Stripe**: `receipt_url` on charges, `hosted_invoice_url` on invoices
- **GitHub**: `html_url` on most resources (issues, PRs, commits)
- **Linear**: `url` field on issues, projects

### Pattern: Always Include URL Fields

**❌ Without URL (No Visual Confirmation)**:
```python
# Generic API pattern
result = api_client.create_resource({
    "name": "Example Resource"
})
print(f"Created resource ID: {result['id']}")
# User thinks: "Okay... but how do I verify this worked?"
```

**✅ With URL (Visual Confirmation)**:
```python
# Request URL field in response
result = api_client.create_resource(
    data={"name": "Example Resource"},
    fields=["id", "name", "web_url"]  # Include web URL field
)
print(f"✅ Created resource: {result['name']}")
print(f"🔗 View in web UI: {result['web_url']}")
# User clicks link → sees resource in web UI → CONFIDENCE!
```

## Quick Start

### Jobber Example

```python
mutation = """
    mutation CreateClient($input: ClientCreate!) {
        clientCreate(input: $input) {
            client {
                id
                firstName
                jobberWebUri  # <-- ADD THIS
            }
        }
    }
"""

result = client.execute_query(mutation, variables)
created = result['clientCreate']['client']
print(f"✅ Created client: {created['firstName']}")
print(f"🔗 View in Jobber: {created['jobberWebUri']}")
```

### Implementation Pattern

1. **Identify URL field**: Check API docs for web URL fields
2. **Include in request**: Add field to query/response schema
3. **Display clickable link**: Use terminal hyperlinks (ANSI OSC 8) or plain URLs
4. **Enable verification**: User clicks → visual confirmation

## URL Helper Utilities

This skill includes utilities for formatting success messages with clickable terminal hyperlinks:

```python
from jobber.url_helpers import format_success

# Format success message with clickable link
resource_data = {
    'id': '123',
    'name': 'John Doe',
    'jobberWebUri': 'https://secure.getjobber.com/clients/123'
}

message = format_success("Client", resource_data, name_field="name")
print(message)
# ✅ Client created: John Doe
# 🔗 View in Jobber: https://secure.getjobber.com/clients/123 (clickable in terminal)
```

See [`assets/url_helpers_template.py`](assets/url_helpers_template.py) for parameterized template.

## Use Cases

This pattern applies to:

1. **Create Operations**: Immediate visual confirmation after creating resources
2. **Query Operations**: Clickable links in query results
3. **Update Operations**: Verify changes in web UI
4. **Batch Operations**: Links for each created/updated resource
5. **Debugging**: Quick navigation to problem resources

For detailed examples, see [`references/use-cases.md`](references/use-cases.md).

## API Integration Examples

### Jobber GraphQL

```python
# Always include jobberWebUri in selections
query = """
    query {
        clients {
            nodes {
                id
                name
                jobberWebUri
            }
        }
    }
"""
```

### Stripe API

```python
# Charge with receipt URL
charge = stripe.Charge.create(
    amount=1000,
    currency="usd",
    source="tok_visa"
)
print(f"Receipt: {charge.receipt_url}")

# Invoice with hosted URL
invoice = stripe.Invoice.create(customer="cus_123")
print(f"View invoice: {invoice.hosted_invoice_url}")
```

### GitHub API

```python
# Issue with HTML URL
issue = github_client.create_issue(
    repo="owner/repo",
    title="Bug report"
)
print(f"View issue: {issue['html_url']}")
```

See [`references/api-integration.md`](references/api-integration.md) for complete API coverage.

## Terminal Hyperlinks (ANSI OSC 8)

Modern terminals support clickable hyperlinks via ANSI OSC 8 escape codes. This enables:

- **Cmd+Click** (macOS) or **Ctrl+Click** (Linux) to open URLs
- **Clean output**: Display text shows link label, not full URL
- **Better UX**: No copy-paste needed

See [`references/terminal-hyperlinks.md`](references/terminal-hyperlinks.md) for ANSI implementation details.

## Examples

Runnable examples with inline dependencies (PEP 723):

- [`examples/create_with_url.py`](examples/create_with_url.py) - Create resource with URL confirmation
- [`examples/query_with_urls.py`](examples/query_with_urls.py) - Query results with clickable links
- [`examples/batch_with_urls.py`](examples/batch_with_urls.py) - Batch operations with URL feedback
- [`examples/terminal_hyperlinks.py`](examples/terminal_hyperlinks.py) - ANSI OSC 8 clickable links

## Error Handling

URL helpers follow fail-fast error handling:

```python
from jobber.url_helpers import validate_url

# Raises TypeError if resource_data not dict
# Raises KeyError if URL field missing
# Raises ValueError if URL field empty string
url = validate_url(resource_data, field="jobberWebUri")
```

No fallbacks, defaults, or silent failures. Caller controls recovery strategy.

## References

- [API Integration Guide](references/api-integration.md) - Complete API coverage (Jobber, Stripe, GitHub, Linear)
- [Terminal Hyperlinks](references/terminal-hyperlinks.md) - ANSI OSC 8 implementation
- [Use Cases](references/use-cases.md) - 5 detailed use case patterns
- [Unit Tests](../../tests/test_url_helpers.py) - 19 tests validating URL helpers

## Validation

This pattern is production-validated:

- **ADR-0003**: Visual confirmation URL pattern decision
- **ADR-0004**: URL helpers unit testing (19 tests, 100% pass)
- **Implementation**: `jobber/url_helpers.py` (156 LOC)
- **Guide**: `docs/visual-confirmation-urls.md` (495 lines)

## Reusability

This pattern is API-agnostic and reusable for any API providing web UI URLs:

- ✅ **Jobber**: `jobberWebUri`, `previewUrl`
- ✅ **Stripe**: `receipt_url`, `hosted_invoice_url`
- ✅ **GitHub**: `html_url`
- ✅ **Linear**: `url`
- ✅ **Asana**: `permalink_url`
- ✅ **Any REST/GraphQL API** with web URL fields
