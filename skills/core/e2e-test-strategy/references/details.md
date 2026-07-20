# E2E Test Strategy - Details

Deep material that was moved out of the main skill body to keep it under the 150-line cap.

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


## Verification Checklist

- [ ] The claim or action has been verified against a live source
- [ ] The output matches the request's scope (no scope creep)
- [ ] Slop markers are absent (filler, hedging, emoji headers)
