---
name: quality-protocol
description: The unified maximum-quality protocol — restate → catalog constraints
  → plan → single-file subsystems → write-verify → self-verify → batch. Always on
  for every non-trivial task. Distilled from 50+ high-quality agent traces (Fable-5,
  Reasoning Corpus, UltraX, OpenThoughts).
version: 0.1.0
license: MIT
provenance:
  inspired: true
author: Agent Foundry Contributors
---

# Quality Protocol — Maximum Quality Every Session

For every non-trivial task (anything beyond a single known-command execution), follow this sequence.

## The Protocol

### Step 1: Problem Restatement

Restate what you're being asked in your own words. State what you DO know and what you DON'T know.

```
The user wants [goal]. I know [context]. I don't know [gaps]. I'll infer [assumptions].
```

### Step 2: Constraint Catalog

List every constraint explicitly BEFORE beginning work:
- Technical constraints (framework, version, platform)
- Quality constraints (must be executable, must have verify step)
- Output constraints (format, file location)
- Boundary conditions (read-only, no commit, no credentials)

### Step 3: Plan + First Action

State the plan in one sentence, then immediately execute the first action:

```
Plan: [build/fix/audit X]. First — [first concrete action].
```

### Step 4: Single-File Subsystems

When generating code, co-locate tightly-coupled logic in single files. Extract only when:
- The file exceeds 500 lines
- A file has multiple responsibilities that are independently testable
- A module has multiple consumers that don't need the full file

### Step 5: Write → Verify Loop

EVERY write is immediately followed by verification:
1. Write the file
2. Run the typecheck / compile / test command
3. Inspect the output
4. Fix any errors before the next write

### Step 6: Self-Verification

After reaching a conclusion, explicitly verify against every constraint from Step 2:

```
Verify: [solution] satisfies [constraint A] ✓, [constraint B] ✓, [constraint C] ✓
```

### Step 7: Batching

Batch INDEPENDENT tool calls in a single response:
- Multiple Read calls when they don't depend on each other
- Multiple independent Write calls

## Composes With

- `plan-then-act` — the action layer of this protocol
- `constraint-then-solve` — the reasoning layer of this protocol
- `verify-first` — adds triangle verification to the whole flow
- `prompt-discipline` — applies the same rules at code level

## Verification

After applying: confirm each of the 7 steps appears in the response in order, and the final output includes the constraint-by-constraint self-verify line.
