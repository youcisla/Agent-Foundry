---
name: re-verify-findings
description: Before executing any audit finding, claimed bug, or reported issue, re-verify
  it against LIVE sources (repo, DB, API, browser). Never accept stale assertions
  — a significant fraction of external claims are already fixed or wrong by the time
  you see them. Use after any prior verification claimed a finding.
version: 0.1.0
license: MIT
author: Agent Foundry Contributors
---

# Re-Verify Findings

Never execute a finding without re-verifying it against current code.

## Auto-trigger

Activates on any prompt containing "audit", "fix", "bug", "issue", "according to", "was reported", "the plan says", "as stated in".

## When to Use

- Before executing any plan, fix, or audit item
- When user says "the audit found X" or "as reported by Y"
- When inheriting work from another agent or model
- Before deploying a fix for a claimed problem

## Procedure

### 1 — Tag every claim as hypothesis

Every claim from an external source gets a status before execution:
- ✅ confirmed (verified against live source)
- 🔧 already fixed (verified current code is correct)
- ❌ wrong (brief contradicts reality)

Do NOT accept the brief's severity without verifying.

### 2 — Verify against every live source available

| Source | What to check |
|--------|---------------|
| Repo (read_file/grep/git) | Is the claimed code still present? Exact line number? |
| Git log | Was it already fixed? When? |
| Live DB (SQL query) | Schema, data, migration state match claim? |
| Live API (curl/browser) | Does the deployed endpoint behave as claimed? |
| Stripe/3rd-party MCP | Does the connected account have what the claim asserts? |
| Browser (live app) | Does the UI actually look/behave as described? |

### 3 — Document discrepancies

When a claim is wrong or stale, state clearly:

```
Claim: [from the brief/audit]
Reality: [what you verified]
Implication: [plan change or skip]
```

This goes in the final report so the user understands why an item was skipped or modified.

## Anti-pattern

Accepting the brief's claim at face value, executing, then discovering the fix was unnecessary. Wastes work and erodes trust.

- Skipping verification when the change 'feels small'
- Reasoning by analogy without a real example
## Composes With

- `verify-first` — broader discipline this is a subset of
- `pushback-when-wrong` — the delivery vehicle for the discrepancy


## Verification Checklist

- [ ] The claim or action has been verified against a live source
- [ ] The output matches the request's scope (no scope creep)
- [ ] Slop markers are absent (filler, hedging, emoji headers)
