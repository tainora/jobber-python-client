# Visual Confirmation URLs - Use Cases

Five detailed patterns for leveraging web URL fields in API responses.

## Use Case 1: Create Operations

Provide immediate visual confirmation after creating resources.

```python
# Create client with URL feedback
result = client.execute_query(CREATE_CLIENT_MUTATION, variables)
client_data = result['clientCreate']['client']

print(f"✅ Client created!")
print(f"   Name: {client_data['firstName']} {client_data['lastName']}")
print(f"   🔗 View: {client_data['jobberWebUri']}")
```

**User Experience**: Click link → Verify in web UI → Trust established

**Example Mutation**:
```graphql
mutation CreateClient($input: ClientCreate!) {
    clientCreate(input: $input) {
        client {
            id
            firstName
            lastName
            jobberWebUri  # <-- Essential for visual confirmation
        }
    }
}
```

## Use Case 2: Query Operations

Show clickable links in query results.

```python
# Query recent clients with URLs
query = """
    query GetClients {
        clients(first: 10) {
            nodes {
                id
                firstName
                jobberWebUri
            }
        }
    }
"""

result = client.execute_query(query)

print("Recent clients:")
for client_data in result['clients']['nodes']:
    print(f"• {client_data['firstName']}: {client_data['jobberWebUri']}")
```

**User Experience**: Browse list → Click interesting client → Opens in web UI

**API-Agnostic Pattern**:
```python
# Works with any API providing URL fields
# GitHub: html_url
# Stripe: receipt_url
# Linear: url

for item in results:
    print(f"• {item['name']}: {item['url_field']}")
```

## Use Case 3: Automation Reports

Include web links in Slack notifications, emails, dashboards.

```python
# Automation: Create job and notify team
result = client.execute_query(CREATE_JOB_MUTATION, variables)
job = result['jobCreate']['job']

# Send Slack message with clickable link
slack_message = (
    f"🔔 New job created: {job['title']}\n"
    f"🔗 View in Jobber: {job['jobberWebUri']}"
)
send_slack(slack_message)
```

**Team Experience**: Slack notification → Click link → Job details open → No manual search

**Slack Link Format**:
```python
# Slack markdown format for clickable links
slack_message = f"New job created: <{job['jobberWebUri']}|{job['title']}>"
```

**Email Example**:
```python
email_body = f"""
New invoice created!

Invoice #: {invoice['invoiceNumber']}
Amount: ${invoice['total']}

View in Jobber: {invoice['jobberWebUri']}
"""
send_email(to=team_email, subject="New Invoice", body=email_body)
```

## Use Case 4: Validation

Use URL presence as validation that resource exists.

```python
# Validation pattern
result = client.execute_query(GET_CLIENT_QUERY, {'id': client_id})

if result['client'] and result['client']['jobberWebUri']:
    print(f"✅ Client exists: {result['client']['jobberWebUri']}")
else:
    print("❌ Client not found or access denied")
```

**Logic**: If API returns web URL, resource is accessible and valid.

**Advanced Validation**:
```python
from jobber.url_helpers import validate_url

try:
    url = validate_url(resource_data, field="jobberWebUri")
    print(f"✅ Resource accessible: {url}")
except KeyError:
    print("❌ Resource not found or no web access")
```

**Error Handling**:
- **KeyError**: URL field missing → Resource inaccessible or field not requested
- **ValueError**: URL field empty string → API bug or permissions issue
- **TypeError**: URL field not string → API response malformed

## Use Case 5: Quote Dual URLs

Quotes have TWO URLs for different audiences.

```python
mutation = """
    mutation CreateQuote($input: QuoteCreate!) {
        quoteCreate(input: $input) {
            quote {
                id
                quoteNumber
                jobberWebUri  # Internal team view
                previewUrl    # Client approval link
            }
        }
    }
"""

result = client.execute_query(mutation, variables)
quote = result['quoteCreate']['quote']

print(f"✅ Quote #{quote['quoteNumber']} created")
print(f"   Team view: {quote['jobberWebUri']}")
print(f"   Client approval: {quote['previewUrl']}")
```

**Workflow**:
1. Team clicks `jobberWebUri` → Edit quote in Jobber
2. Send `previewUrl` to customer → Customer approves/declines

**Security Considerations**:
- `jobberWebUri`: Requires login, safe to share within team
- `previewUrl`: Contains token, treat as semi-sensitive (safe to send to customer, don't publish publicly)

**API-Agnostic Dual URL Pattern**:

Similar patterns exist in other APIs:

- **Stripe Invoices**: `hosted_invoice_url` (customer view) + Stripe Dashboard link (internal)
- **GitHub PRs**: `html_url` (public view) + internal review URL
- **Linear Issues**: `url` (team view) + public share link

## Best Practices

### 1. Always Include URL Fields

Default pattern for ANY create/update operation:

```graphql
mutation CreateX($input: XCreate!) {
    xCreate(input: $input) {
        x {
            id
            # ... other fields
            jobberWebUri  # <-- ALWAYS include
        }
        userErrors { message }
    }
}
```

### 2. Always Display in Output

User-facing output should ALWAYS show web links:

```python
# ✅ Good: Show URL
print(f"✅ Created! View: {result['jobberWebUri']}")

# ❌ Bad: Hide URL
print(f"Created ID: {result['id']}")  # User can't verify
```

### 3. Include in Error Context

If operation fails, show URL of related resource:

```python
try:
    result = client.execute_query(UPDATE_JOB, variables)
except GraphQLError as e:
    # If job exists, user can click to see current state
    print(f"❌ Update failed: {e}")
    print(f"   View current state: {existing_job_url}")
```

### 4. Batch Operations

Collect all URLs and display summary:

```python
created_urls = []

for item in items_to_create:
    result = client.execute_query(mutation, {'input': item})
    created_urls.append(result['xCreate']['x']['jobberWebUri'])

print(f"✅ Created {len(created_urls)} items:")
for i, url in enumerate(created_urls, 1):
    print(f"   {i}. {url}")
```

## Runnable Examples

See [`../examples/`](../examples/) for PEP 723 runnable examples:

- `create_with_url.py` - Create resource with URL confirmation
- `query_with_urls.py` - Query results with clickable links
- `batch_with_urls.py` - Batch operations with URL feedback
- `validation.py` - URL-based resource validation

## Related References

- [API Integration](api-integration.md) - API-specific URL field mappings
- [Terminal Hyperlinks](terminal-hyperlinks.md) - ANSI OSC 8 clickable links
- [SKILL.md](../SKILL.md) - Hub document with quick start
