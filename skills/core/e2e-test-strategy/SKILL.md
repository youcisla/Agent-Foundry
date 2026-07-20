---
name: e2e-test-strategy
description: "Plan an end-to-end test pyramid: which flows to E2E, which to integration, which to unit. Seeding strategy, auth state handling, flake mitigation, parallel execution. Use when designing test coverage for a web app or API."
version: 0.1.0
license: MIT
provenance:
  author: Youcisla
  source: operational methodology
  inspired: true
---

# E2E Test Strategy

A test pyramid that catches the bugs that matter, runs fast, and doesn't flake.

## The Pyramid

```
       ╱  E2E  ╲              few — 5-20 critical flows
      ╱─────────╲
     ╱Integration╲           some — key API + DB combinations
    ╱─────────────╲
   ╱     Unit     ╲         many — every function, every branch
  ╱─────────────────╲
```

Don't invert it. Lots of E2E = slow, flaky, low-signal.

## Decision Tree

For any test case, ask in order:

1. **Can I test it with a pure function?** → Unit
2. **Can I test it with one module + mocked deps?** → Integration
3. **Does it span network / browser / external service?** → E2E

| Behavior | Layer |
|----------|-------|
| `validateEmail(s)` rejects bad input | Unit |
| `UserRepo.create()` inserts and returns | Integration |
| `POST /signup` returns 201 + sends email | E2E |
| Drag-drop reorders list | E2E |
| Pricing tier changes entitlement | Integration |
| Stripe webhook triggers subscription | E2E |

## Which E2E Flows Matter

E2E is expensive. Pick the 5-20 flows where a regression would cost the most.

| Always E2E | Never E2E |
|------------|-----------|
| Sign-up → first value moment | Internal helpers |
| Core monetization (checkout, subscription) | Pure UI styling |
| Critical auth (login, password reset) | Bulk data imports |
| Cross-service contracts (webhooks) | Background jobs |
| Critical admin actions | |

Rule: **"What is the user-visible failure cost if this regresses?"** Catastrophic → E2E. Cosmetic → unit or skip.

## Test Data: Seeding

**Bad**: production DB or saved dumps.

**Good**: deterministic per-test seeding.

```typescript
async function seedUser(opts: { plan?: 'free' | 'pro' } = {}) {
  const id = `test-${randomUUID()}`;
  await db.users.insert({ id, email: `${id}@test.com`, plan: opts.plan ?? 'free' });
  return id;
}
```

Rules:
- Each test seeds only what it needs
- Cleanup in `afterEach`, not `afterAll`
- Unique IDs per run (parallel-safe)
- Pin time-relative data to fixtures

## Auth State in E2E

Three patterns, ranked:

1. **Programmatic login** (best): bypass UI, set auth cookie
   ```typescript
   await page.context().addCookies([{ name: 'session', value: token }]);
   ```
2. **API-driven login**: POST credentials, use returned token
3. **UI login** (avoid): click through form. Slow, fragile.

## Flake Mitigation

Five common causes:

| Cause | Fix |
|-------|-----|
| Race condition | Wait for a specific element, not a timeout |
| Network timing | Mock external calls; deterministic seeds |
| Test ordering | Isolate each test; no shared state |
| Time-of-day | Freeze time or use relative durations |
| Animation / transition | `await page.waitForLoadState('networkidle')` |

Rule: **the test waits for an observable state, not a time.** Never `sleep(2000)` — always `await expect(element).toBeVisible()`.

## Parallel Execution

Run E2E in parallel across:
- Multiple workers (CI: 4-8)
- Multiple browsers (Chromium + Firefox + WebKit)
- Multiple shards (split by file)

Database options:
- One DB per worker (transactional reset)
- Schema-per-test (slower setup, fully isolated)
- Per-test cleanup with unique IDs (simplest)

Pick one. Don't mix.

## Cost / Time Budget

| Layer | Target time | Count |
|-------|-------------|-------|
| Unit | <5ms each | hundreds-thousands |
| Integration | <500ms each | dozens-hundreds |
| E2E | <30s each, total <10 min | 5-20 flows |

E2E suite >15 min → inverted pyramid. Cut some.

## Anti-patterns

- E2E testing every UI variation
- `sleep()` instead of waiting for state
- Sharing state between tests
- Hard-coded credentials in test files
- Testing internal implementations via E2E
