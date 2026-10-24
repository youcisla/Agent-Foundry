---
name: budget-guard
description: 'Set a hard spend ceiling before a paid loop starts, measure each call,
  and stop at the limit with a report. Covers tokens, dollars, retries, and wall
  clock. Use for any agent loop, batch, or retry policy that spends money.'
version: 0.1.0
license: MIT
author: Agent Foundry Contributors
---

# Budget Guard

Every paid call consumes a finite budget. Decide the ceiling first, then make the
loop prove it stayed under.

## Auto-trigger

- A task runs more than one paid model call.
- A retry or repair loop is introduced.
- A batch processes an unknown number of items.
- The user names a cost, token, or time limit.
- A fallback chain can multiply attempts.

## When to Use

- Agent loops and multi-step workflows.
- Batch extraction, evaluation, or judging runs.
- Retry policies around flaky providers.
- Anything that could run unattended.

## Procedure

### 1 — Set the ceiling before the first call

Name the limit in the unit you can measure:

| Unit | Use when |
|---|---|
| USD | Prices are known per model |
| Tokens | The provider reports usage but not cost |
| Calls | Every item costs roughly the same |
| Seconds | Latency is the constraint |

Record the limit in the run configuration, not in a comment.

### 2 — Estimate before, measure after

Before the loop, estimate the worst case: items x calls per item x tokens per
call. After each call, add the reported usage. Do not estimate from input length
alone; output and repairs also cost.

### 3 — Stop at the boundary

Check the running total before the next call. If the next call could cross the
ceiling, stop. Return partial results with the amount spent and what was skipped.
A hard stop is not a failure of the task; it is the guard working.

### 4 — Make retries count against the budget

A retry is a new paid call. A fallback is a new paid call. Include both in the
same running total so the chain cannot multiply spend invisibly.

### 5 — Report the spend

Return: limit, spent, remaining, calls made, and items skipped. A run that says
"done" without spend numbers is unaudited.

## Anti-patterns

- Setting a budget after the run.
- Counting input tokens only.
- Treating retries as free.
- Continuing because "one more call is small".
- Stopping silently without naming what was skipped.

## Verification Checklist

- [ ] A numeric ceiling exists before the first call
- [ ] Usage is measured from provider responses, not guessed
- [ ] Retries and fallbacks count toward the total
- [ ] Exceeding the ceiling stops the loop
- [ ] The final report includes spent and skipped

## Composes With

- `fallback-model-routing` — bounded chains, counted against the same budget
- `measure-first` — replaces estimates with observed usage
- `execution-observability` — persists cost per execution

## Two Caps and Measured Input

- Enforce a per-call cap and a per-session aggregate cap. A single global ceiling lets one call consume the whole budget.
- Prefer provider-reported prompt tokens for the same model when available; fall back to a character estimate only on a miss.
- Count every model attempt, including repair rounds and judge escalations. A retry that is not counted is a budget leak.
- Report `max_attempts`, `max_concurrency`, and `checkpoint_every` beside the token budget; tokens alone cannot bound wall-clock or fan-out.
- Compaction and spill change the effective prompt size. Re-estimate after either runs, not before.
