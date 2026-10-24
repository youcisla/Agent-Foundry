---
name: fallback-model-routing
description: 'Route around provider overload, rate limits, and timeouts without hiding
  the switch. Retry the primary within a bounded budget, try declared fallbacks in
  order, and report which model answered. Use when a model call can fail and work
  must continue.'
version: 0.1.0
license: MIT
author: Agent Foundry Contributors
---

# Fallback Model Routing

A failed model call is a routing event, not a reason to abandon the task. Route
it deliberately and leave a trail.

## Auto-trigger

- A provider returns overload, rate-limit, timeout, or 5xx errors.
- A model is unavailable in the current region or account.
- The task has a declared fallback model or a smaller backup tier.
- A long batch cannot afford to stop on one failed call.

## When to Use

- Production paths with a latency or availability budget.
- Batch jobs where one provider outage should not kill the run.
- Tiered routing: frontier model first, balanced model as backup.
- Any call where the prompt is unchanged and only the engine differs.

## Procedure

### 1 — Declare the chain up front

Order matters. Put the preferred model first and the cheapest acceptable backup
last. Resolve aliases to full model IDs before the first call so logs are stable.

```
primary: claude-sonnet-5-5
fallbacks: [claude-haiku-5-5]
```

### 2 — Classify the failure before retrying

| Failure | Action |
|---|---|
| Timeout, overload, 429, 5xx | Try the next model |
| Auth rejected (401/403) | Stop. A fallback cannot fix credentials |
| Invalid request (schema, context too long) | Fix the request, do not reroute |
| Budget exhausted | Stop and report spend |

Blind retries on auth or budget errors burn time and hide the real cause.

### 3 — Bound the attempts

Retry the primary within its configured retry count, then walk the fallback list
once. Cap the chain length. No fallback loops, no re-walking a model that already
failed.

### 4 — Preserve the request

Use the same messages for every model in the chain. Do not silently shorten the
prompt or drop the schema to make a smaller model fit; that changes the task.

### 5 — Report provenance

Return the model that actually answered. A caller comparing quality, cost, or
latency needs to know when a fallback served the request.

## Anti-patterns

- Falling back on a 401 and reporting "provider outage".
- Retrying the same overloaded model five times with no delay budget.
- Hiding the switch so cost reports look flat.
- Changing the prompt between primary and fallback.
- Falling back to a model that cannot satisfy the required schema.

## Verification Checklist

- [ ] Chain is ordered and bounded
- [ ] Auth and budget failures stop immediately
- [ ] The request is byte-identical across models
- [ ] The answering model is recorded
- [ ] A test injects a primary failure and asserts the fallback result

## Composes With

- `structured-output-contract` — keeps the schema fixed across models
- `budget-guard` — stops the chain when spend hits the ceiling
- `execution-observability` — records which model served each run

## Capability-Aware Routing

- Inspect per-model capabilities before building messages: system-prompt support, context window, default temperature, stop tokens per mode.
- When a model rejects the system role, fold the skill text into the user turn. Never send an unsupported role and hope.
- Reject an over-context request before the call; do not silently truncate.
- Forward `seed` and `temperature` only when the caller set them, and record them in the request digest.
- Retry transport failures with backoff; never retry an auth error or a refusal into another model.
- Gate adaptive attempt allocation on queue depth. The optimization is negative at low load.
- Cache and score identity include runtime version, git SHA, model revision, and effective params.
