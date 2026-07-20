---
name: measure-first
description: Before planning any change, query live data (DB, API, analytics, logs) to find the actual bottleneck. Static analysis reveals structure; live data reveals truth. Plans must sequence by measured bottleneck, not by requested order.
version: 0.1.0
license: MIT
provenance:
  author: Youcisla
  source: operational methodology
  inspired: true
---

# Measure First

The plan is only as good as the data it's based on. Static analysis reveals code structure; live data reveals where users actually churn.

## Auto-trigger

Activates on any prompt containing "plan", "fix", "improve", "build", "redesign", "add feature", "optimize", "priority".

## When to Use

- Before creating any plan or roadmap
- Before deciding what to fix first
- When asked to build a new feature (should we invest here?)
- When the user says "our problem is X" (measure it first)

## Procedure

### 1 — Identify the metrics that matter

Ask: what is the single number that tells us if the product is working?
- For a funnel product: activation rate (users who complete step N)
- For billing: conversion rate, LTV, churn
- For a content product: retention, time-to-value

### 2 — Query live data

Connect to whatever live sources are available:
- Database (SQL, direct Postgres, Supabase, etc.)
- Analytics provider (if connected via API)
- Logs (Sentry, edge function logs, app logs)
- Usage metrics (API rate limits, active users, event counts)

Sample queries:

```sql
-- Funnel: how many users complete each step?
select event, count(*), count(distinct user_id)
from funnel_events
where created_at > now() - interval '30 days'
group by 1;

-- State distribution: where are users stuck?
select status, count(*) from cases group by 1;
```

### 3 — Let the data reorder the plan

If 86% of cases die at step 1, the funnel is the bottleneck — not the dashboard polish. Sequence the plan accordingly.

### 4 — Document the bottleneck finding

```
Measured: [what we found]
Implication: [phase sequence change]
Sources: [DB query / API / logs]
```

## Anti-pattern

Planning based on the order things were requested. The user asked for feature X but the data says Y is the bottleneck — fix Y first.

## Composes With

- `verify-first` — uses live data as one triangle source
- `bottleneck-gating` — uses this measurement to set phase gates
- `pushback-when-wrong` — delivers the "your order is wrong" message
