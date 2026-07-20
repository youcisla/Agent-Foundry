---
name: plan-then-act
description: Plan first, then act. State the plan in one sentence BEFORE any tool
  call. Every Bash call must include a description field explaining WHY. Use on every
  non-trivial task. Use when a task has multiple steps and the order matters.
version: 0.1.0
license: MIT
provenance:
  inspired: true
author: Agent Foundry Contributors
---

# Plan Then Act

State the plan in one sentence before any tool call. Every Bash call must include a `description` field explaining WHY.

## Core Patterns

### 1. Plan-First with Tool-Description

Every complex task starts with a plan BEFORE any tool call. Every Bash tool call includes a `description` field explaining WHY.

```
ASSISTANT: "Big task. Plan: build [system] — [architecture]. [features]. Then [verification]. First — [step]."
ASSISTANT: Bash(command=..., description="Why this command is needed")
```

The `description` field is mandatory. It structures the agent's own reasoning about what the tool call achieves.

### 2. create-Then-Verify Loop

Every write is immediately followed by verification:
1. create file(s)
2. Start the runtime
3. Take screenshot / check console / run typecheck
4. examine back the output, inspect for errors
5. Iterate based on evidence

Anti-pattern: write files then move on without testing them.

### 3. Batching Independent Calls

Batch parallel reads and writes that don't depend on each other:
- Multiple examine calls in one turn for initial codebase understanding
- Multiple create calls for independent subsystems
- Bash + examine in parallel when read doesn't depend on bash output

### 4. Massive Single-File Outputs (Coherent Subsystems)

When generating code, co-locate tightly-coupled logic in single files. Extract only when:
- The file exceeds 500 lines
- A file has multiple responsibilities that are independently testable
- A module has multiple consumers that don't need the full file

Works because: 1M context window holds the full codebase; single-file coherence avoids cross-file import inconsistencies.

### 5. Headless Playtesting with Real Browser Tools

When building UI, run a real browser. Take screenshots. Click through flows. Compare to design. Don't trust "it compiled."

## When to Use

- Any task beyond a single known-command execution
- Multi-file changes
- UI work where visual correctness matters
- Code generation across multiple subsystems

## When NOT to Use

- Trivial single-tool operations
- Pure read-only queries

## Verification

After applying: confirm every Bash call has a `description` field, every write is followed by a verify step, and independent calls are batched.


## Anti-patterns

- Skipping verification when the change "feels small"
- Reasoning by analogy without a real example
- Acting on a claim you have not verified this session
- Choosing speed over accuracy when accuracy is what the task requires


## Verification Checklist

- [ ] The claim or action has been verified against a live source
- [ ] The output matches the request's scope (no scope creep)
- [ ] Slop markers are absent (filler, hedging, emoji headers)
