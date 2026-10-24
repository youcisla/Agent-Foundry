---
name: judge-integrity
description: "Use when a model judges model output: separate judge failure from a low score, run deterministic checks first, gate escalation, and keep scoring separate from generation."
version: 0.1.0
author: Agent Foundry Contributors
---

# judge-integrity

A judge is a measurement instrument. An instrument that returns zero when it is
broken is worse than no instrument.

## Contract

- Every judge attempt returns a status: `ok`, `unparseable`, `call_failed`, or `timeout`.
- `scores` is present only when status is `ok`. A parse failure is never a zero.
- Transport errors retry with backoff. Refusals and parse failures do not retry into another score.
- A deterministic verifier runs before the paid judge. A definitive pass may skip the judge; `unknown` falls through.
- Judge and evaluation calls pin temperature 0 and preserve structural markers.
- Escalate to a stronger judge only below an explicit score threshold.
- Store the judge prompt hash and status beside the score.

## Procedure

1. Parse the response with balanced-brace extraction; fences and nested objects are normal.
2. Run the task verifier. Stop on `pass` or `fail` only if the task declares the verifier authoritative.
3. Call the judge with a timeout. Record status and duration even on failure.
4. Store scores, status, model, and prompt hash. Never overwrite the generation record.
5. Re-score stored output with a separate command; do not re-run generation to re-judge.

## Anti-patterns

- Mapping unparseable output to `0.0` and calling it a score.
- Treating a provider outage as a low-quality answer.
- Re-running the full generation to apply a new judge.
- Pooling judge scores across model revisions or rubric versions.

## Verification Checklist

- [ ] A raising provider yields `call_failed`, not a score.
- [ ] Prose output yields `unparseable`, not a score.
- [ ] Nested JSON parses correctly.
- [ ] Re-scoring a stored execution performs no completion call.
- [ ] Every score has a status and a model fingerprint.

## Composes With

- `structured-output-contract` — parsing and constraint precedence
- `execution-observability` — judge status and request metadata
- `feedback-loop` — calibration against human feedback
