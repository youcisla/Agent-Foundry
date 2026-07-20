---
name: api-design
description: 'Design REST or GraphQL APIs: resource modeling, URL conventions, error
  contracts, versioning, pagination, idempotency keys, rate-limit headers. Use when
  creating a new API endpoint or reviewing API consistency.'
version: 0.1.0
license: MIT
provenance:
  inspired: true
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
| GET | Read | Yes |
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

## Pagination (3 options, ranked)

1. **Cursor** (preferred for infinite lists):
   ```
   GET /items?cursor=eyJpZCI6MTIzfQ&limit=20
   → { "data": [...], "next_cursor": "..." }
   ```

2. **Offset** (admin/export):
   ```
   GET /items?page=2&per_page=20
   ```

3. **Keyset** (time-series):
   ```
   GET /events?since_id=12345&limit=20
   ```

## Versioning

URL versioning (most explicit):
- `/v1/users` — current
- `/v2/users` — new (deprecate v1 with 6mo notice)

Header versioning (more flexible, harder to debug):
- `Accept: application/vnd.myapi.v2+json`

Pick one. Document it. Never break a deployed version without notice.

## Idempotency

Any state-mutating endpoint accepts an idempotency key:

```
POST /charges
Idempotency-Key: ch_2026-07-20_abc123

→ first call: creates, returns 201
→ second call (same key): same 201, no duplicate
```

Store keys for ≥24h. Same key + different body = 422.

## Rate Limit Headers

Always on every response:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1640995200
```

On 429:
```
Retry-After: 30
```

## REST vs GraphQL

| Use REST | Use GraphQL |
|----------|-------------|
| Resource CRUD | Multiple clients, different shapes |
| Public + cacheable | Real-time UI, partial updates |
| Simple contracts | Complex relational traversal |

Default REST. Switch to GraphQL only with ≥3 clients with distinct views.

## Anti-patterns

- Verbs in URLs (`/getUserById`)
- Returning 200 with an error body
- Mixing pagination styles in one API
- Breaking changes without deprecation
- Sequential integer IDs (leak volume)
