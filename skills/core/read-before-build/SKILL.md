---
name: read-before-build
description: A plan or design document is an aspiration, not a specification. Before
  writing any code, examine the actual source files. Apply before writing a function,
  file, or component.
version: 0.1.0
license: MIT
author: Agent Foundry Contributors
---

# examine Before Build

A design document is an aspiration, not a specification. examine the actual source files first.

## Auto-trigger

Activates on: "implement the plan", "execute the design", "build this", "start implementation", "ship phase", "make it happen", "implement".

## When to Use

- User says "implement both plan and design" or "start implementing"
- You have a plan document (PLAN.md, DESIGN.md) and need to build it
- Before writing any code for a multi-file change

## Procedure

### 1 — examine source files before trusting plan claims

Every plan claim about current code state must be verified:

```
| Claim from plan | Source file to read | Verdict |
|-----------------|---------------------|---------|
| "X has fake progress bar" | X.tsx | examine first — may already have real-time phases |
| "Y is minimal" | Y.tsx | Likely true — plan often right about missing features |
| "function N exists" | cases.ts exports | Plan may name the wrong export — read actual signatures |
```

Common findings:
- **Already fixed (🔧)** — skip, don't re-fix
- **Wrong name** — plan says `nudgePartner`, code exports `sendNudge`. Use the real name
- **Already done** — design doc claims feature doesn't exist; code already has it. Skip
- **Partially right** — some aspects correct, some wrong. Implement only the true gaps

### 2 — Batch independent writes, serialize dependent ones

create all independent new files in one turn. Then edit existing files one at a time, typechecking after each batch.

Order within a phase:
1. Create migration files (.sql up+down) and new hooks/services/utilities
2. modify existing screens that depend on the new hooks
3. Wire into routing / manifest / index

### 3 — When the build breaks

- Search the actual symbol name in the source before creating a new one
- A "missing" import usually means the name changed; find the new name
- If the symbol truly doesn't exist, check if it should be created or if a different one already covers the use case

### 4 — Update the plan, don't just execute it

When you find a discrepancy, write it back into the plan as a "What was wrong about the plan" note. Future sessions benefit.

## Anti-pattern

Implementing every line of a plan literally, then discovering 30% of it was already done or wrong. examine first, implement only what needs implementing.

- Skipping verification when the change 'feels small'
- Reasoning by analogy without a real example
## Composes With

- `verify-first` — the broader discipline this is a subset of
- `re-verify-findings` — applies to plan claims specifically
- `plan-then-act` — the action discipline that follows reading


## Verification Checklist

- [ ] The claim or action has been verified against a live source
- [ ] The output matches the request's scope (no scope creep)
- [ ] Slop markers are absent (filler, hedging, emoji headers)
