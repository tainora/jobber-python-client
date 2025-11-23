# GraphQL Query Patterns

Common GraphQL query construction patterns and best practices.

## Basic Query Structure

```graphql
query QueryName {
  resource {
    field1
    field2
  }
}
```

**Components**:
- `query`: Operation type (query, mutation, subscription)
- `QueryName`: Optional operation name (recommended for debugging)
- `resource`: Root field
- `field1, field2`: Selected fields

## Query with Variables

```graphql
query GetUser($id: ID!) {
  user(id: $id) {
    id
    name
    email
  }
}
```

**Variables** (passed separately):
```json
{
  "id": "123"
}
```

**Benefits**:
- Type safety (`$id: ID!`)
- Reusability (same query, different variables)
- Security (prevents injection)

## Fragments

Reusable field selections:

```graphql
fragment UserFields on User {
  id
  name
  email
  createdAt
}

query GetUsers {
  users {
    ...UserFields
  }
}

query GetUser($id: ID!) {
  user(id: $id) {
    ...UserFields
    posts {
      id
      title
    }
  }
}
```

## Aliases

Rename fields in response:

```graphql
query {
  admin: user(id: "1") {
    id
    name
  }
  regularUser: user(id: "2") {
    id
    name
  }
}
```

**Response**:
```json
{
  "admin": {"id": "1", "name": "Admin"},
  "regularUser": {"id": "2", "name": "User"}
}
```

## Inline Fragments (Unions/Interfaces)

```graphql
query {
  search(query: "test") {
    ... on User {
      id
      name
    }
    ... on Post {
      id
      title
    }
  }
}
```

## Directives

### @include

Conditionally include fields:

```graphql
query GetUser($id: ID!, $includeEmail: Boolean!) {
  user(id: $id) {
    id
    name
    email @include(if: $includeEmail)
  }
}
```

### @skip

Conditionally skip fields:

```graphql
query GetUser($id: ID!, $skipPosts: Boolean!) {
  user(id: $id) {
    id
    name
    posts @skip(if: $skipPosts) {
      id
      title
    }
  }
}
```

## Mutations

### Basic Mutation

```graphql
mutation CreateUser($input: UserInput!) {
  userCreate(input: $input) {
    user {
      id
      name
    }
    errors {
      message
      path
    }
  }
}
```

**Variables**:
```json
{
  "input": {
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

### Multiple Mutations

```graphql
mutation CreateAndUpdate(
  $createInput: UserInput!,
  $updateId: ID!,
  $updateInput: UserInput!
) {
  create: userCreate(input: $createInput) {
    user { id }
  }
  update: userUpdate(id: $updateId, input: $updateInput) {
    user { id }
  }
}
```

## Pagination Patterns

### Cursor-Based (Relay)

```graphql
query GetUsers($first: Int!, $after: String) {
  users(first: $first, after: $after) {
    nodes {
      id
      name
    }
    pageInfo {
      hasNextPage
      endCursor
    }
    totalCount
  }
}
```

### Offset-Based

```graphql
query GetUsers($limit: Int!, $offset: Int!) {
  users(limit: $limit, offset: $offset) {
    id
    name
  }
  usersCount
}
```

## Filtering

```graphql
query GetUsers($filter: UserFilter) {
  users(filter: $filter) {
    id
    name
    email
  }
}
```

**Variables**:
```json
{
  "filter": {
    "status": "ACTIVE",
    "createdAfter": "2024-01-01"
  }
}
```

## Sorting

```graphql
query GetUsers($sortBy: UserSortField, $sortOrder: SortOrder) {
  users(sortBy: $sortBy, sortOrder: $sortOrder) {
    id
    name
    createdAt
  }
}
```

**Variables**:
```json
{
  "sortBy": "CREATED_AT",
  "sortOrder": "DESC"
}
```

## Nested Queries

```graphql
query {
  user(id: "123") {
    id
    name
    posts {
      id
      title
      comments {
        id
        text
        author {
          id
          name
        }
      }
    }
  }
}
```

**Warning**: Deep nesting increases query cost. Limit nesting depth.

## Query Complexity Optimization

### ❌ Over-Fetching

```graphql
query {
  users {
    id
    name
    email
    address
    phoneNumber
    posts {
      id
      title
      content
      comments {
        id
        text
        author {
          id
          name
          email
        }
      }
    }
  }
}
```

### ✅ Fetch Only Required Fields

```graphql
query {
  users {
    id
    name
  }
}
```

### ✅ Separate Queries

```graphql
# Query 1: Get users
query GetUsers {
  users {
    id
    name
  }
}

# Query 2: Get specific user's posts (when needed)
query GetUserPosts($userId: ID!) {
  user(id: $userId) {
    posts {
      id
      title
    }
  }
}
```

## Introspection Queries

### Schema Types

```graphql
query {
  __schema {
    types {
      name
      kind
    }
  }
}
```

### Type Fields

```graphql
query {
  __type(name: "User") {
    name
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

### Query Cost (if supported)

```graphql
query {
  __schema {
    queryType {
      name
    }
  }
}
```

## Best Practices

### 1. Always Use Variables

```graphql
# ❌ Avoid: Inline values
query {
  user(id: "123") {
    name
  }
}

# ✅ Good: Variables
query GetUser($id: ID!) {
  user(id: $id) {
    name
  }
}
```

### 2. Name Your Operations

```graphql
# ❌ Avoid: Anonymous query
query {
  users { id }
}

# ✅ Good: Named query
query GetAllUsers {
  users { id }
}
```

### 3. Use Fragments for Reusability

```graphql
# ❌ Avoid: Duplicated fields
query {
  user(id: "1") {
    id
    name
    email
  }
  users {
    id
    name
    email
  }
}

# ✅ Good: Fragment
fragment UserFields on User {
  id
  name
  email
}

query {
  user(id: "1") {
    ...UserFields
  }
  users {
    ...UserFields
  }
}
```

### 4. Limit Result Set Size

```graphql
# ❌ Avoid: Unbounded queries
query {
  users {
    id
    name
  }
}

# ✅ Good: Limited result set
query {
  users(first: 100) {
    nodes {
      id
      name
    }
  }
}
```

### 5. Handle Errors Gracefully

```graphql
mutation CreateUser($input: UserInput!) {
  userCreate(input: $input) {
    user {
      id
      name
    }
    userErrors {
      message
      field
      code
    }
  }
}
```

**Check for errors**:
```python
result = executor.execute(mutation, variables)

if result['userCreate']['userErrors']:
    errors = result['userCreate']['userErrors']
    for error in errors:
        print(f"Error on {error['field']}: {error['message']}")
    return

user = result['userCreate']['user']
```

## API-Specific Patterns

### Jobber

```graphql
# Jobber uses Global IDs (gid://)
query GetClient($id: ID!) {
  client(id: $id) {
    id  # gid://jobber/Client/123
    firstName
    jobberWebUri  # Always include for visual confirmation
  }
}
```

### Shopify

```graphql
# Shopify uses gid:// format
query GetProduct($id: ID!) {
  product(id: $id) {
    id  # gid://shopify/Product/123
    title
    handle
  }
}
```

### GitHub

```graphql
# GitHub uses owner/repo format
query GetRepository($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    id
    name
    url
  }
}
```

## Related References

- [Error Handling](error-handling.md) - Handle GraphQL query errors
- [Pagination](pagination.md) - Pagination query patterns
- [Rate Limiting](rate-limiting.md) - Optimize query cost
- [SKILL.md](../SKILL.md) - Hub document with quick start
