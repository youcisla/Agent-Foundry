---
name: read-before-build
description: A plan or design document is an aspiration, not a specification. Before
  writing any code, read the actual source files. A significant fraction of plan claims
  will be stale, already-fixed, or flat-out wrong. When the build breaks due to missing
  imports, find the actual symbol name in the source, don't create new ones.
version: 0.1.0
license: MIT
provenance:
  inspired: true
author: Youcisla
---

# Read Before Build

A design document is an aspiration, not a specification. Read the actual source files first.

## Auto-trigger

Activates on: "implement the plan", "execute the design", "build this", "start implementation", "ship phase", "make it happen", "implement".

## When to Use

- User says "implement both plan and design" or "start implementing"
- You have a plan document (PLAN.md, DESIGN.md) and need to build it
- Before writing any code for a multi-file change

## Procedure

### 1 — Read source files before trusting plan claims

Every plan claim about current code state must be verified:

```
| Claim from plan | Source file to read | Verdict |
|-----------------|---------------------|---------|
| "X has fake progress bar" | X.tsx | Read first — may already have real-time phases |
| "Y is minimal" | Y.tsx | Likely true — plan often right about missing features |
| "function N exists" | cases.ts exports | Plan may name the wrong export — read actual signatures |
```

Common findings:
- **Already fixed (🔧)** — skip, don't re-fix
- **Wrong name** — plan says `nudgePartner`, code exports `sendNudge`. Use the real name
- **Already done** — design doc claims feature doesn't exist; code already has it. Skip
- **Partially right** — some aspects correct, some wrong. Implement only the true gaps

### 2 — Batch independent writes, serialize dependent ones

Write all independent new files in one turn. Then edit existing files one at a time, typechecking after each batch.

Order within a phase:
1. Create migration files (.sql up+down) and new hooks/services/utilities
2. Edit existing screens that depend on the new hooks
3. Wire into routing / manifest / index

### 3 — When the build breaks

- Search the actual symbol name in the source before creating a new one
- A "missing" import usually means the name changed; find the new name
- If the symbol truly doesn't exist, check if it should be created or if a different one already covers the use case

### 4 — Update the plan, don't just execute it

When you find a discrepancy, write it back into the plan as a "What was wrong about the plan" note. Future sessions benefit.

## Anti-pattern

Implementing every line of a plan literally, then discovering 30% of it was already done or wrong. Read first, implement only what needs implementing.

## Composes With

- `verify-first` — the broader discipline this is a subset of
- `re-verify-findings` — applies to plan claims specifically
- `plan-then-act` — the action discipline that follows reading
