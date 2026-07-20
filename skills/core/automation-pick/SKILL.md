---
name: automation-pick
description: Before automating a task, decide whether to automate. Decision tree based
  on volume, frequency, error cost, and reversibility. Use when someone says 'we should
  automate this' or 'let's build a script for that'.
version: 0.1.0
license: MIT
provenance:
  inspired: true
author: Youcisla
---

# Automation Pick

A framework for deciding which tasks are worth automating. Most tasks aren't.

## When to Use

- Someone says "we should automate this"
- You're tempted to write a script for a one-off task
- Reviewing a backlog of "automate X" requests
- Building automation that turned out to be wrong

## The Decision Tree

Answer in order. Stop at the first "no".

### 1. Has this been done manually at least 3 times?

If no → **don't automate yet**. Do it manually 3 times. Patterns only emerge with repetition.

### 2. Will it be done ≥10 more times in the next year?

If no → **don't automate**. Even a 2-hour script doesn't pay back.

### 3. Does manual execution have a real error cost?

| Cost | Examples | Automate? |
|------|----------|-----------|
| Catastrophic | Billing, security, data loss | ✅ Yes, urgently |
| Annoying | Wrong formatting, missed deadlines | ✅ Yes, eventually |
| Cosmetic | Looks bad | ❌ Probably not |
| Zero | "It would be nice" | ❌ No |

### 4. Is the task fully understood and deterministic?

If the rules keep changing, or humans make judgement calls → **don't automate** (yet). Standardize first, automate second.

### 5. Is the task reversible?

If the automation runs and gets the wrong answer:
- Easy to detect and revert → automate
- Hard to detect, propagates → **don't automate** without safeguards

## The 4-Quadrant Matrix

| | Low error cost | High error cost |
|---|---|---|
| **High volume** | Automate freely | Automate carefully (with monitoring) |
| **Low volume** | Don't automate | Don't automate (do it manually + check) |

## Anti-patterns

- Skipping verification when the change 'feels small'
- Reasoning by analogy without a real example
