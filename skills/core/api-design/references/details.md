# Api Design - Details

Deep material that was moved out of the main skill body to keep it under the 150-line cap.

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


## Verification Checklist

- [ ] The claim or action has been verified against a live source
- [ ] The output matches the request's scope (no scope creep)
- [ ] Slop markers are absent (filler, hedging, emoji headers)
