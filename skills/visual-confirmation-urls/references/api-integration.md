# API Integration - Visual Confirmation URLs

API-specific field mappings, URL patterns, and integration strategies for major platforms.

## API Coverage

### Jobber GraphQL API

**URL Fields**:
- `jobberWebUri`: Web URL in Jobber account (team view)
- `previewUrl`: Client Hub preview URL (customer view, quotes only)

**Supported Resources**:
- ✅ Client
- ✅ Job
- ✅ Quote (both `jobberWebUri` and `previewUrl`)
- ✅ Invoice
- ✅ Visit
- ✅ Request
- ✅ Property
- ⚠️  Check [Jobber API docs](https://developer.getjobber.com/docs/) for complete list

**URL Structure**:
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

**GraphQL Query Example**:
```graphql
query GetClient($id: ID!) {
    client(id: $id) {
        id
        firstName
        lastName
        jobberWebUri  # Always include for visual confirmation
    }
}
```

**Mutation Example**:
```graphql
mutation CreateClient($input: ClientCreate!) {
    clientCreate(input: $input) {
        client {
            id
            firstName
            jobberWebUri  # Essential for confirmation
        }
        userErrors { message }
    }
}
```

**Introspection** (check which resources support `jobberWebUri`):
```graphql
query IntrospectJobberWebUri {
    __type(name: "Client") {
        fields {
            name
            type { name }
        }
    }
}
```

Filter results for `jobberWebUri` to confirm availability.

### Stripe API

**URL Fields**:
- `receipt_url`: Receipt URL for charges
- `hosted_invoice_url`: Customer-facing invoice URL
- `url`: Dashboard link for various resources

**Examples**:

**Charge with Receipt**:
```python
import stripe

charge = stripe.Charge.create(
    amount=1000,
    currency="usd",
    source="tok_visa"
)
print(f"Receipt: {charge.receipt_url}")
# https://pay.stripe.com/receipts/...
```

**Invoice with Hosted URL**:
```python
invoice = stripe.Invoice.create(customer="cus_123")
print(f"View invoice: {invoice.hosted_invoice_url}")
# https://invoice.stripe.com/i/...
```

**PaymentIntent**:
```python
payment_intent = stripe.PaymentIntent.create(
    amount=1000,
    currency="usd"
)
# Access via charges[0].receipt_url after confirmation
```

**Configuration**:
```python
STRIPE_CONFIG = {
    "url_fields": {
        "Charge": "receipt_url",
        "Invoice": "hosted_invoice_url",
        "PaymentIntent": "receipt_url"  # Via charges
    },
    "service_name": "Stripe Dashboard"
}
```

### GitHub API

**URL Field**: `html_url` (universal across resources)

**Supported Resources**:
- ✅ Issues
- ✅ Pull Requests
- ✅ Commits
- ✅ Repositories
- ✅ Users
- ✅ Organizations

**REST API Example**:
```python
import requests

# Create issue
response = requests.post(
    "https://api.github.com/repos/owner/repo/issues",
    headers={"Authorization": f"token {github_token}"},
    json={"title": "Bug report", "body": "Description"}
)
issue = response.json()
print(f"View issue: {issue['html_url']}")
# https://github.com/owner/repo/issues/123
```

**GraphQL API Example**:
```graphql
query GetIssue($owner: String!, $repo: String!, $number: Int!) {
    repository(owner: $owner, name: $repo) {
        issue(number: $number) {
            id
            title
            url  # GraphQL uses 'url' instead of 'html_url'
        }
    }
}
```

**Configuration**:
```python
GITHUB_CONFIG = {
    "url_field": "html_url",  # REST API
    # "url_field": "url",     # GraphQL API
    "service_name": "GitHub",
    "name_fields": {
        "Issue": "title",
        "PullRequest": "title",
        "Commit": "sha"
    }
}
```

### Linear API

**URL Field**: `url` (universal across resources)

**Supported Resources**:
- ✅ Issues
- ✅ Projects
- ✅ Teams
- ✅ Cycles

**GraphQL Example**:
```graphql
mutation CreateIssue($input: IssueCreateInput!) {
    issueCreate(input: $input) {
        issue {
            id
            identifier  # e.g., "ENG-123"
            title
            url  # Direct link to issue
        }
    }
}
```

**Python SDK Example**:
```python
from linear import LinearClient

linear = LinearClient(api_key)

issue = linear.create_issue(
    team_id="team_id",
    title="Feature request",
    description="Details"
)
print(f"Issue created: {issue.url}")
# https://linear.app/team/issue/ENG-123
```

**Configuration**:
```python
LINEAR_CONFIG = {
    "url_field": "url",
    "service_name": "Linear",
    "name_fields": {
        "Issue": "identifier",  # ENG-123 format
        "Project": "name"
    }
}
```

### Asana API

**URL Field**: `permalink_url`

**REST API Example**:
```python
import asana

client = asana.Client.access_token(access_token)

task = client.tasks.create_task({
    "name": "Task name",
    "projects": [project_id]
}, opt_fields=["permalink_url"])

print(f"View task: {task['permalink_url']}")
# https://app.asana.com/0/{project_id}/{task_id}
```

**Configuration**:
```python
ASANA_CONFIG = {
    "url_field": "permalink_url",
    "service_name": "Asana",
    "name_field": "name"
}
```

## URL Validation Patterns

### Check URL Field Availability

**GraphQL Introspection**:
```graphql
query IntrospectFields($typeName: String!) {
    __type(name: $typeName) {
        fields {
            name
            type {
                name
                kind
            }
        }
    }
}
```

**Filter for URL fields**:
```python
def has_url_field(type_name: str, field_name: str) -> bool:
    """Check if type has URL field via introspection."""
    query = """
        query IntrospectFields($typeName: String!) {
            __type(name: $typeName) {
                fields {
                    name
                }
            }
        }
    """
    result = client.execute_query(query, {"typeName": type_name})
    fields = [f['name'] for f in result['__type']['fields']]
    return field_name in fields

# Usage
has_jobber_web_uri = has_url_field("Client", "jobberWebUri")
```

### Runtime Validation

```python
from jobber.url_helpers import validate_url

# Jobber
url = validate_url(client_data, field="jobberWebUri")

# GitHub
url = validate_url(issue_data, field="html_url")

# Stripe
url = validate_url(charge_data, field="receipt_url")

# Linear
url = validate_url(issue_data, field="url")
```

**Error Handling**:
- **KeyError**: Field missing or null
- **ValueError**: Field is empty string
- **TypeError**: Field value not a string

## Integration Patterns

### Pattern 1: CLI Tool with URLs

```python
import click
from jobber.url_helpers import clickable_link

@click.command()
@click.option('--name', required=True)
def create_client(name: str):
    """Create client and show web link."""
    client = JobberClient.from_doppler()

    result = client.execute_query(CREATE_CLIENT, {'input': {'firstName': name}})
    created = result['clientCreate']['client']

    click.echo(f"✅ Created: {created['firstName']}")
    click.echo(f"🔗 {clickable_link(created['jobberWebUri'], 'View in Jobber')}")
```

### Pattern 2: Web Dashboard

```python
from flask import Flask, jsonify

@app.route('/clients', methods=['POST'])
def create_client():
    """API endpoint with web URL in response."""
    client = JobberClient.from_doppler()
    result = client.execute_query(mutation, variables)

    return jsonify({
        'id': result['clientCreate']['client']['id'],
        'webUrl': result['clientCreate']['client']['jobberWebUri'],
        'message': 'Client created! Click link to view.'
    })
```

**Frontend Integration**:
```javascript
fetch('/clients', {method: 'POST', body: JSON.stringify(data)})
  .then(res => res.json())
  .then(data => {
    showNotification(data.message);
    // Show clickable link
    document.getElementById('result').innerHTML =
      `<a href="${data.webUrl}" target="_blank">View Client</a>`;
  });
```

### Pattern 3: Slack Bot

```python
from slack_sdk import WebClient

def handle_create_job(job_data):
    """Create job and notify Slack channel."""
    client = JobberClient.from_doppler()
    result = client.execute_query(CREATE_JOB, {'input': job_data})
    job = result['jobCreate']['job']

    slack_client = WebClient(token=slack_token)
    slack_client.chat_postMessage(
        channel='#operations',
        text=f"New job created: <{job['jobberWebUri']}|{job['title']}>"
    )
```

**Slack Link Format**: `<URL|TEXT>`

### Pattern 4: Email Notifications

```python
from email.mime.text import MIMEText

def send_creation_email(resource_type: str, resource_data: dict):
    """Send email with web link."""
    email_body = f"""
    New {resource_type} created!

    Name: {resource_data['name']}
    View in web UI: {resource_data['jobberWebUri']}

    ---
    This is an automated notification.
    """

    msg = MIMEText(email_body)
    msg['Subject'] = f"New {resource_type} Created"
    msg['To'] = team_email

    smtp.send_message(msg)
```

### Pattern 5: Batch Operations

```python
def create_batch_with_urls(items: list[dict]) -> list[str]:
    """Create multiple resources, return all URLs."""
    created_urls = []

    for item in items:
        result = client.execute_query(mutation, {'input': item})
        created_urls.append(result['xCreate']['x']['jobberWebUri'])

    return created_urls

# Usage
items = [{'name': 'Client 1'}, {'name': 'Client 2'}]
urls = create_batch_with_urls(items)

print(f"✅ Created {len(urls)} clients:")
for i, url in enumerate(urls, 1):
    print(f"   {i}. {url}")
```

## Troubleshooting

### URL Field Returns Null

**Symptom**: Field is null even though resource created successfully.

**Possible Causes**:
1. Insufficient permissions (API token can't access resource)
2. Resource type doesn't support URL field (check API docs)
3. Query syntax error (field name typo)

**Resolution**:
```graphql
# Verify field name spelling (case-sensitive)
query GetClient($id: ID!) {
    client(id: $id) {
        jobberWebUri  # Check: correct spelling, case
    }
}
```

### URL Returns 404 When Clicked

**Symptom**: URL provided, but clicking returns "Not Found".

**Possible Causes**:
1. Resource deleted after creation
2. User not logged into account
3. Browser cookie/session issue

**Resolution**:
1. Verify resource still exists via API query
2. Ensure logged into correct account
3. Try opening URL in incognito/private browsing

### Preview URL Access Denied

**Symptom**: `previewUrl` returns 403 Forbidden.

**Possible Causes** (Jobber-specific):
1. Client Hub not enabled for account
2. Quote not yet sent to client
3. Preview link expired

**Resolution**:
- Check Client Hub settings in account
- Send quote to client first (triggers preview generation)
- Regenerate preview link if expired

## Performance Considerations

### Minimal Overhead

Adding URL fields to queries has minimal performance impact:

- **Field cost**: Negligible (string field, already computed)
- **Network**: +50 bytes per resource (URL length)
- **No extra API calls**: URL included in same response

**Recommendation**: ALWAYS include URL fields. The UX benefit vastly outweighs minimal overhead.

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

**Jobber `jobberWebUri`** contains NO sensitive information:
- ✅ Safe to log
- ✅ Safe to display in UI
- ✅ Safe to send in notifications
- ❌ NOT authentication token (requires login to access)

**Jobber `previewUrl`** (quote preview) contains token:
- ⚠️  Treat as semi-sensitive
- ✅ Safe to send to customer
- ⚠️  Don't publish publicly
- ⚠️  Token may expire

**GitHub `html_url`**:
- ✅ Safe to share (public repos)
- ⚠️  Respect privacy settings (private repos)

**Stripe URLs**:
- ✅ `receipt_url`: Safe to share with customers
- ✅ `hosted_invoice_url`: Safe to share with customers
- ⚠️  Dashboard links: Internal use only

### Access Control

Clicking URLs requires:
1. Valid account login
2. Permission to view resource
3. Resource exists in that account

**Implication**: URLs are safe to share within team (all must have account access).

## Template Usage

See [`../assets/url_helpers_template.py`](../assets/url_helpers_template.py) for parameterized implementation:

```python
from url_helpers_template import format_success, validate_url

# Jobber
message = format_success(
    "Client",
    client_data,
    url_field="jobberWebUri",
    service_name="Jobber"
)

# GitHub
message = format_success(
    "Issue",
    issue_data,
    name_field="title",
    url_field="html_url",
    service_name="GitHub"
)

# Stripe
message = format_success(
    "Charge",
    charge_data,
    name_field="id",
    url_field="receipt_url",
    service_name="Stripe"
)
```

## References

- **Jobber API**: https://developer.getjobber.com/docs/
- **Stripe API**: https://stripe.com/docs/api
- **GitHub API**: https://docs.github.com/en/rest
- **Linear API**: https://developers.linear.app/docs/graphql/working-with-the-graphql-api
- **Asana API**: https://developers.asana.com/docs

## Related References

- [Use Cases](use-cases.md) - 5 detailed use case patterns
- [Terminal Hyperlinks](terminal-hyperlinks.md) - ANSI OSC 8 clickable links
- [SKILL.md](../SKILL.md) - Hub document with quick start
