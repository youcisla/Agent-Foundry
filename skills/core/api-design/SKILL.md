---
name: api-design
description: 'Design REST or GraphQL APIs: resource modeling, URL conventions, error
  contracts, versioning, pagination, idempotency keys, rate-limit headers. Use when
  creating a new API endpoint or reviewing API consistency.'
version: 0.1.0
license: MIT
author: Agent Foundry Contributors
---

# API Design

Design APIs that are predictable, versionable, and self-documenting.

## REST Conventions

- Resources are nouns, plural: `/users`, `/cases`, `/reflections`
- Actions are sub-resources: `/users/{id}/sessions`
- Verbs only when nothing else fits: `/users/{id}/verify-email`

## HTTP Methods

| Method | Action | Idempotent |
|--------|--------|------------|
| GET | examine | Yes |
| POST | Create | No (without key) |
| PUT | Replace | Yes |
| PATCH | Partial update | No |
| DELETE | Delete | Yes |

## Status Codes

| Code | When |
|------|------|
| 200 | Successful read/update |
| 201 | Successful create (include `Location`) |
| 204 | Successful delete / no body |
| 400 | Malformed request |
| 401 | Missing/invalid auth |
| 403 | Not permitted |
| 404 | Resource missing or hidden |
| 409 | State collision |
| 422 | Valid syntax, semantic fail |
| 429 | Rate-limited (`Retry-After`) |
| 500 | Unexpected server error |

## Error Contract

Every error uses the same shape:

```json
{
  "error": {
    "code": "user_not_found",
    "message": "No user with id 'abc123'",
    "param": "user_id",
    "doc_url": "https://api.example.com/docs/errors#user_not_found"
  }
}
```

- `code`: stable, snake_case, machine-readable
- `message`: human-readable, may include the failing value
- `param`: which field caused the issue
- `doc_url`: always present for documented codes

## Anti-patterns

- Skipping verification when the change 'feels small'
- Reasoning by analogy without a real example
