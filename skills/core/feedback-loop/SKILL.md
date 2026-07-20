---
name: feedback-loop
description: 'After shipping, set up the loop: instrument → measure → review weekly
  → adjust. Use when shipping a feature, launching a product, or noticing nobody acts
  on data.'
version: 0.1.0
license: MIT
author: Agent Foundry Contributors
---

# Feedback Loop

Shipped is not done. The value comes from the loop after launch.

## The Loop

```
Instrument → Measure → Review → Adjust → Repeat (weekly)
```

Every step is required. Skipping any one breaks the loop.

## 1 — Instrument

Before launch, decide what to measure. Three layers:

| Layer | Tells you | Examples |
|-------|-----------|----------|
| Business | Did the change move the needle? | Activation, retention, revenue |
| Product | Did users do the thing? | Button clicks, feature adoption |
| System | Did the system work? | Errors, latency, uptime |

For a new feature:
- 1 business metric (the one that justifies the feature)
- 2-3 product metrics (the funnel steps)
- 3-5 system metrics (so you know it works)

Add tracking BEFORE launch. Not after.

## 2 — Measure

Don't stare at a dashboard. Measure by **collecting the number once**.

Two formats:
- **Daily metric sheet** (automated): email/Slack at 9am with yesterday's key numbers
- **Weekly review doc** (one page): trends and anomalies

If you can't name the number you expect, you didn't define success.

## 3 — Review Weekly

30 minutes. Same time every week. Same template:

```
Week of [date]

[Big metric]: X (vs. target Y, vs. last week Z)
- Why did it move?
- What surprised me?

[Secondary metric 1]: ...
[Secondary metric 2]: ...

Actions:
1. [One thing we'll do this week]
2. [One thing we'll stop doing]
```

Don't skip weeks. Skipping = loop is dead.

## Anti-patterns

- Skipping verification when the change 'feels small'
- Reasoning by analogy without a real example
