---
name: execution-observability
description: 'Log what ran, on which model, with which skill, at what cost, and whether
  it succeeded, without storing prompts or secrets. Query history to debug routing
  and spend. Use after adding execution paths or when a run must be auditable.'
version: 0.1.0
license: MIT
author: Agent Foundry Contributors
---

# Execution Observability

An execution you cannot inspect is an execution you cannot debug, bill, or trust.

## Auto-trigger

- New code path calls a model, or a routing decision changes behavior.
- The user asks why a run was slow, expensive, or wrong, or an audit needs evidence.

## When to Use

- After wiring an executor, loop, or batch runner.
- When cost or quality regressions appear.
- When multiple models or skills can serve the same request, or before claiming a
  pipeline is production-ready.

## Procedure

### 1 — Define the record

One row per execution, with at minimum:

| Field | Why |
|---|---|
| timestamp | Ordering and incident windows |
| skill id | Attribution and routing quality |
| model | Which engine answered |
| tokens and cost | Spend accounting |
| duration | Latency regressions |
| success and error | Failure taxonomy |
| fallback flag | Separates routed runs from preferred-model runs |
| schema validity | Distinguishes valid structure from best-effort text |

### 2 — Store hashes, not prompts

Prompts can contain user data, credentials, or private context. Persist a hash
and the skill id. Keep full output only when the user explicitly opts in and the
storage location is agreed. Never log API keys or authorization headers.

### 3 — Record both outcomes

Log success and failure. A table that only records successes hides the failures
that matter most. Include the error text, truncated, and the model that failed.

### 4 — Query, do not dump

Expose a bounded history read: newest first, optional skill filter, limit and
offset. Do not return full output bodies by default. A caller debugging a run
needs metadata, not a wall of generated text.

### 5 — Correlate

The useful questions are joins:
- Which skill has the highest failure rate?
- Which model serves fallback runs most often?
- Did cost per success rise after a prompt change?
- Are schema failures concentrated in one skill?

If the record cannot answer these, add fields before adding dashboards.

## Anti-patterns

- Logging prompts or secrets "for debugging".
- Recording only successful runs.
- Storing unbounded output in the index table.
- No model field, so cost changes are unattributable.
- A history endpoint that returns everything with no limit.

## Verification Checklist

- [ ] Every execution path writes one record
- [ ] Failures are recorded with their error
- [ ] Prompts are hashed, not stored
- [ ] The model and fallback flag are present
- [ ] History reads are bounded and exclude full output bodies

## Record Contract

- Record `trace_digest` over canonical messages, model chain, seed, temperature, schema, skill hash, runtime version, and output.
- Record `request_meta_json` with model revision, git SHA, message hash, roles, and char counts. A model-visible request must be reconstructable from the log.
- Record `phases` for plan, completion, schema, judge, and persist. A missing phase is a blind spot, not a zero.
- Record `judge_status` (`ok`, `unparseable`, `call_failed`, `timeout`) separately from the score. Never collapse judge failure into a low score.
- Record `failure_kind` (`provider`, `schema`, `policy`, `attest`, `budget`, `internal`) so callers do not parse error strings.
- Store success and failure latency separately, and keep the full output behind `output_ref`, not in the row.
