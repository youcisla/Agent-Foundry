---
name: feedback-loop
description: "After shipping, set up the loop: instrument → measure → review weekly → adjust. Use when shipping a feature, launching a product, or noticing nobody acts on data."
version: 0.1.0
license: MIT
provenance:
  author: Youcisla
  source: operational methodology
  inspired: true
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

## 4 — Adjust

One action per week. Not five. Not zero.

| Finding | Action |
|---------|--------|
| Metric dropped >10% | Investigate within 24h |
| Metric unchanged for 4+ weeks | Change strategy, not tactics |
| Metric up >10% | Document what worked |
| New anomaly | Add to next week's review |

The point is to close the loop. First adjustment is rarely right; second or third usually is.

## 5 — Repeat

Same review, next week, same template. Compound effect of weekly reviews is enormous.

## Common Failure Modes

| Pattern | Fix |
|---------|-----|
| Dashboards nobody opens | Replace with auto-emailed metric |
| Don't know what success looks like | Define success metric before launch |
| Shipped, metric didn't move | Check instrument → change feature → re-measure |
| Watching dashboards daily (noise panic) | Force weekly review for signal |
| No owner | Pick one person, name them |

## Cadence by Stage

| Stage | Review |
|-------|--------|
| Pre-launch | Daily standup on launch readiness |
| First week post-launch | Daily metric check |
| Weeks 2-4 | Every 2-3 days |
| Months 2-6 | Weekly |
| Mature | Weekly + monthly trend |

Weekly minimum, always. The habit is the point.

## Anti-patterns

- Instrumenting after launch
- Watching dashboards without deciding
- Reviewing metrics in isolation (no actions)
- Optimizing without changing anything
- Reporting metrics up the chain without acting on them
