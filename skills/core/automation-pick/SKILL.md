---
name: automation-pick
description: "Before automating a task, decide whether to automate. Decision tree based on volume, frequency, error cost, and reversibility. Use when someone says 'we should automate this' or 'let's build a script for that'."
version: 0.1.0
license: MIT
provenance:
  author: Youcisla
  source: operational methodology
  inspired: true
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

## Common Traps

### "We should automate X"

Often this means "X takes 5 minutes and annoys me." Calculate:

- Time saved per run: 5 min
- Runs per week: 3
- Time saved per year: 13 hours
- Cost to automate: 8 hours (initial) + 4 hours (maintenance/year) = 12 hours first year

Net first year: 1 hour saved. **Not worth it.**

### "This script saved me 2 hours last month"

A one-off script that ran once and was thrown away. The 2 hours you spent writing it aren't amortized.

### "It'll be faster next time"

Unless you've done it ≥3 times, you don't know the pattern well enough to automate. The third time, you actually understand the edge cases.

### "We could automate this entire process"

Big automation projects fail more than they succeed. Start small. Prove value. Expand.

## When Automation Is Clearly Right

| Scenario | Why |
|----------|-----|
| Billing calculations | High error cost, high volume, deterministic |
| Compliance reporting | Auditable, repeatable, time-sensitive |
| Data backups | Catastrophic if skipped, low cost to automate |
| Code formatting | Deterministic, low risk, every file |
| Test running | High volume, deterministic, fast feedback |
| Customer onboarding email | Personalized at scale, measurable |

## When Automation Is Clearly Wrong

| Scenario | Why |
|----------|-----|
| First-time tasks | No pattern yet |
| Creative work | Judgment calls every time |
| Exception handling | Edge cases dominate |
| Decisions requiring trust | User wants a human in the loop |
| Tasks that change weekly | Maintenance cost > savings |

## The Decision Format

When proposing an automation, write one paragraph:

```
[Task] takes [X] minutes per run, [N] runs/week, error cost is [low/med/high],
rules are [static/changing], reversibility is [easy/hard]. 
Automate: [yes/no]. If yes, ROI breakeven: [date].
```

## Anti-patterns

- Automating before understanding the task
- Automating the wrong step (the bottleneck is elsewhere)
- Automating a task that should be eliminated, not done faster
- "Just write a script" without naming the maintenance owner
- Automation with no monitoring (silent failures worse than manual errors)

## Verification Checklist

Before automating:
- [ ] Done manually ≥3 times
- [ ] ≥10 more runs expected in next year
- [ ] Error cost quantified
- [ ] Rules are deterministic
- [ ] Reversibility understood
- [ ] One-paragraph justification written
- [ ] Owner named for maintenance
