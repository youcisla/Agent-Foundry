---
name: verify-first
description: Every assertion about the codebase, product, or market is a hypothesis. Verify it against live sources before committing to action. The master discipline: verify first, act second. Always on.
version: 0.1.0
license: MIT
provenance:
  author: Youcisla
  source: operational methodology
  inspired: true
---

# Verify First

Every assertion is a hypothesis. Verify before committing.

## Auto-trigger

Always active. This is the meta-discipline that governs all work.

## When to Use

- Always. This is the foundation.
- Especially: when inheriting work from another agent or audit
- When the user says "the code does X"
- When a plan depends on an assumption about the system

## Procedure

### 1 — Tag every input as a hypothesis

Before accepting anything as fact, mentally tag it:
- Untested assumption (brief says X)
- Verified fact (I checked: X is true)
- Stale truth (was X, now Y)

### 2 — Triangle verification

For any important claim, verify from at least 2 independent sources:

```
Claim: "The Stripe account is ready for billing"
- Source 1: Stripe MCP (products list → 0 products)
- Source 2: Code search (VITE_BILLING unset, test key only)
- Conclusion: ❌ wrong — wrong account entirely
```

Best sources to triangulate:
1. Live DB query (what's actually stored)
2. Live API call (what the server actually does)
3. Source code (what the repo says)
4. Browser (what users actually see)
5. Git log (when was it last changed)

### 3 — Log and generalize

When you discover a new type of stale claim, add it to known-patterns so future sessions don't fall for the same trap.

## Composes With

- `re-verify-findings` — for audit/bug claim context
- `measure-first` — adds live data to the triangulation
- `read-before-build` — applies the same discipline to plan claims
