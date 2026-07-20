---
name: plan-before-code
description: No implementation without an approved spec for non-trivial work. Brainstorm
  → write spec → get approval → then code. Use before any feature, component, behavior
  change, or refactor. Use before writing any non-trivial code change.
version: 0.1.0
license: MIT
author: Agent Foundry Contributors
---

# Plan Before Code

The gate between "I have an idea" and "I'm writing code." Skipping it is the #1 cause of wasted work.

## The 4 steps

### 1. Brainstorm

Ask clarifying questions **one at a time**. Purpose, constraints, success criteria. Don't dump 10 questions. If the user gave a detailed spec, skip to step 2.

Propose 2-3 approaches with tradeoffs and your recommendation. Let the user pick.

### 2. create the spec

Save to `docs/specs/YYYY-MM-DD-<topic>.md`. Required sections:

- **Goal** — one sentence, what we're building and why
- **Success criteria** — how we know it's done (verifiable, not vibes)
- **Non-goals** — what we're explicitly NOT doing
- **Approach** — chosen path, with rationale
- **Steps** — numbered, each with a verify check
- **Risks** — what could go wrong, mitigation
- **Open questions** — anything unresolved

### 3. Get approval

Ask the user to review the spec **file**, not just your summary. Don't proceed until they say yes. "Sure, go" doesn't count — they need to have read the file.

### 4. Implement

Follow the steps in the spec. If reality diverges, update the spec first, then the code.

## The hard gate

```
No implementation skill, code, scaffolding, or implementation action
until a spec is written and approved.
```

This applies to **every** project, even the "simple" ones. The spec for a one-line change is one sentence. The spec for a rewrite is 200 lines. Both count.

## When to skip

- One-line typo fix
- The user has already given a clear, complete spec in their message — write code, link to the spec
- Throwaway scripts that will be deleted in 10 minutes

## Why this works

- Catches unstated assumptions before they become code
- Forces the user to think about success criteria
- Gives you a reference document to consult when the work gets fuzzy
- Makes it easy to abandon a bad plan — you lose a doc, not a codebase


## Anti-patterns

- Skipping verification when the change "feels small"
- Reasoning by analogy without a real example
- Acting on a claim you have not verified this session
- Choosing speed over accuracy when accuracy is what the task requires


## Verification Checklist

- [ ] The claim or action has been verified against a live source
- [ ] The output matches the request's scope (no scope creep)
- [ ] Slop markers are absent (filler, hedging, emoji headers)
