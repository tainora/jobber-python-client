# Visual Confirmation URLs

**Quick Win Validation**: Get web UI links from Jobber API for visual confirmation of operations.

## Problem Statement

API operations can feel abstract without visual confirmation. Users create a client via API but have no immediate way to verify it exists in Jobber's web interface. This creates uncertainty and requires manual navigation.

**User Question**: "Can I see what I just created via API in the Jobber web interface?"

**Answer**: YES! Include `jobberWebUri` in your GraphQL queries.

## Solution

Jobber's GraphQL API returns `jobberWebUri` fields on most resources. This field contains the direct web URL to view the resource in Jobber's interface.

### Available URL Fields

| Field          | Type   | Description               | Use Case                      |
| -------------- | ------ | ------------------------- | ----------------------------- |
| `jobberWebUri` | String | Web URL in Jobber account | Team members view resource    |
| `previewUrl`   | String | Client Hub preview URL    | Customers view/approve quotes |

### Supported Resources

Resources with `jobberWebUri`:

- ✅ Client
- ✅ Job
- ✅ Quote (also has `previewUrl`)
- ✅ Invoice
- ✅ Visit
- ✅ Request
- ✅ Property
- ⚠️ Check Jobber API docs for complete list

## Quick Start

### Pattern: Always Include jobberWebUri

**❌ Without URL (No Visual Confirmation)**:

```python
mutation = """
    mutation CreateClient($input: ClientCreate!) {
        clientCreate(input: $input) {
            client {
                id
                firstName
            }
        }
    }
"""

result = client.execute_query(mutation, variables)
print(f"Created client ID: {result['clientCreate']['client']['id']}")
# User thinks: "Okay... but how do I verify this worked?"
```

**✅ With URL (Visual Confirmation)**:

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
# User clicks link → sees client in Jobber → CONFIDENCE!
```

## Use Cases

### Use Case 1: Create Operations

Provide immediate visual confirmation after creating resources.

```python
# Create client with URL feedback
result = client.execute_query(CREATE_CLIENT_MUTATION, variables)
client_data = result['clientCreate']['client']

print(f"✅ Client created!")
print(f"   Name: {client_data['firstName']} {client_data['lastName']}")
print(f"   🔗 View: {client_data['jobberWebUri']}")
```

**User Experience**: Click link → Verify in Jobber web UI → Trust established

### Use Case 2: Query Operations

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

**User Experience**: Browse list → Click interesting client → Opens in Jobber

### Use Case 3: Automation Reports

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

### Use Case 4: Validation

Use URL presence as validation that resource exists.

```python
# Validation pattern
result = client.execute_query(GET_CLIENT_QUERY, {'id': client_id})

if result['client'] and result['client']['jobberWebUri']:
    print(f"✅ Client exists: {result['client']['jobberWebUri']}")
else:
    print("❌ Client not found or access denied")
```

**Logic**: If API returns `jobberWebUri`, resource is accessible and valid.

### Use Case 5: Quote Dual URLs

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

## Best Practices

### 1. Always Include in Mutations

Default pattern for ANY create/update mutation:

```graphql
mutation CreateX($input: XCreate!) {
  xCreate(input: $input) {
    x {
      id
      # ... other fields
      jobberWebUri # <-- ALWAYS include
    }
    userErrors {
      message
    }
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

### 3. Use ANSI Hyperlinks (Terminal)

Make URLs clickable in terminal output:

```python
def clickable_link(url: str, text: str) -> str:
    """Generate ANSI hyperlink for terminal."""
    return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"

print(f"✅ Created! {clickable_link(url, 'View in Jobber')}")
```

### 4. Include in Error Context

If operation fails, show URL of related resource:

```python
try:
    result = client.execute_query(UPDATE_JOB, variables)
except GraphQLError as e:
    # If job exists, user can click to see current state
    print(f"❌ Update failed: {e}")
    print(f"   View current state: {existing_job_url}")
```

### 5. Batch Operations

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

## URL Structure

Jobber web URLs follow this pattern:

```
https://secure.getjobber.com/{resource_type}/{id}
```

**Examples**:

- Client: `https://secure.getjobber.com/clients/123456`
- Job: `https://secure.getjobber.com/jobs/789012`
- Quote: `https://secure.getjobber.com/quotes/345678`
- Invoice: `https://secure.getjobber.com/invoices/901234`

**Client Hub Preview URLs** (quotes):

```
https://clienthub.getjobber.com/client_hubs/{token}/quotes/{id}
```

## Implementation Example

See `/Users/terryli/own/jobber/examples/visual_confirmation_urls.py` for complete working examples.

**Run example**:

```bash
uv run examples/visual_confirmation_urls.py
```

**Output includes**:

- Create client with URL feedback
- Query clients with clickable links
- Quote dual URLs (internal + client hub)
- URL-based validation
- Batch operations with URL summary

## Integration Patterns

### Pattern 1: CLI Tool with URLs

```python
import click

@click.command()
@click.option('--name', required=True)
def create_client(name: str):
    """Create client and show web link."""
    client = JobberClient.from_doppler()

    result = client.execute_query(CREATE_CLIENT, {'input': {'firstName': name}})
    created = result['clientCreate']['client']

    click.echo(f"✅ Created: {created['firstName']}")
    click.echo(f"🔗 {created['jobberWebUri']}")
```

### Pattern 2: Web Dashboard

```python
from flask import Flask, jsonify

@app.route('/clients', methods=['POST'])
def create_client():
    client = JobberClient.from_doppler()
    result = client.execute_query(mutation, variables)

    return jsonify({
        'id': result['clientCreate']['client']['id'],
        'webUrl': result['clientCreate']['client']['jobberWebUri'],
        'message': 'Client created! Click link to view.'
    })
```

### Pattern 3: Slack Bot

```python
def handle_create_job(job_data):
    client = JobberClient.from_doppler()
    result = client.execute_query(CREATE_JOB, {'input': job_data})
    job = result['jobCreate']['job']

    slack_client.post_message(
        channel='#operations',
        text=f"New job created: <{job['jobberWebUri']}|{job['title']}>"
    )
```

## Troubleshooting

### jobberWebUri Returns Null

**Symptom**: Field is null even though resource created successfully.

**Possible Causes**:

1. Insufficient permissions (API token can't access resource)
2. Resource type doesn't support jobberWebUri (check Jobber docs)
3. GraphQL query syntax error (field name typo)

**Resolution**:

```graphql
# Verify field name spelling
query GetClient($id: ID!) {
  client(id: $id) {
    jobberWebUri # Check: case-sensitive, correct spelling
  }
}
```

### URL Returns 404 When Clicked

**Symptom**: jobberWebUri provided, but clicking returns "Not Found".

**Possible Causes**:

1. Resource deleted after creation
2. User not logged into Jobber account
3. Browser cookie/session issue

**Resolution**:

1. Verify resource still exists via API query
2. Ensure logged into correct Jobber account
3. Try opening URL in incognito/private browsing

### Preview URL Access Denied

**Symptom**: previewUrl returns 403 Forbidden.

**Possible Causes**:

1. Client Hub not enabled for account
2. Quote not yet sent to client
3. Preview link expired

**Resolution**:

- Check Client Hub settings in Jobber account
- Send quote to client first (triggers preview generation)
- Regenerate preview link if expired

## Performance Considerations

### Minimal Overhead

Adding `jobberWebUri` to queries has minimal performance impact:

- **Field cost**: Negligible (string field, already computed)
- **Network**: +50 bytes per resource (URL length)
- **No extra API calls**: URL included in same response

**Recommendation**: ALWAYS include `jobberWebUri`. The UX benefit vastly outweighs minimal overhead.

### Batch Queries

For large batches (100+ resources), consider pagination:

```graphql
query GetClientURLs($cursor: String) {
  clients(first: 100, after: $cursor) {
    nodes {
      id
      jobberWebUri
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

## Security Considerations

### URL Exposure

**jobberWebUri** contains NO sensitive information:

- ✅ Safe to log
- ✅ Safe to display in UI
- ✅ Safe to send in notifications
- ❌ NOT authentication token (requires login to access)

**previewUrl** (quote preview) contains token:

- ⚠️ Treat as semi-sensitive
- ✅ Safe to send to customer
- ⚠️ Don't publish publicly
- ⚠️ Token may expire

### Access Control

Clicking jobberWebUri requires:

1. Valid Jobber account login
2. Permission to view resource
3. Resource exists in that account

**Implication**: URLs are safe to share within team (all must have Jobber access).

## API Coverage

Check which resources support `jobberWebUri`:

```graphql
query IntrospectJobberWebUri {
  __type(name: "Client") {
    fields {
      name
      type {
        name
      }
    }
  }
}
```

Filter results for `jobberWebUri` to confirm availability.

## Future Enhancements

Potential improvements to this pattern:

1. **URL Helper Utility**: Generate URLs client-side from IDs
2. **Deep Linking**: URLs with pre-selected tabs (e.g., client contacts tab)
3. **Bulk URL Export**: CSV export with web links for external dashboards
4. **QR Codes**: Generate QR codes from jobberWebUri for mobile access

## References

- **Jobber GraphQL API**: https://developer.getjobber.com/docs/
- **Example Code**: `/Users/terryli/own/jobber/examples/visual_confirmation_urls.py`
- **GraphQL Executor**: `/Users/terryli/own/jobber/jobber/graphql.py`

## Summary

**The Pattern**:

1. Add `jobberWebUri` to ALL queries and mutations
2. Display web URLs in ALL user-facing output
3. Enable users to visually verify API operations
4. Build trust through immediate visual confirmation

**Quick Win**: 5 minutes to implement, massive UX improvement.

**Result**: Users trust API operations because they can SEE the results in Jobber's web interface.
