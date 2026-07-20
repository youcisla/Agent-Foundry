# Automation Pick - Details

Deep material that was moved out of the main skill body to keep it under the 150-line cap.

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
