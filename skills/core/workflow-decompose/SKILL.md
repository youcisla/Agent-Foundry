---
name: workflow-decompose
description: 'Decompose any workflow into a DAG: trigger → conditions → actions →
  retries → observability. Mental model for n8n, Temporal, Airflow, GitHub Actions,
  or hand-rolled scripts. Use when designing or debugging an automation.'
version: 0.1.0
license: MIT
author: Agent Foundry Contributors
---

# Workflow Decompose

Decompose any workflow into a reusable DAG. Same model works for cron, n8n, GitHub Actions, or scripts.

## The DAG Model

Every workflow is a directed acyclic graph with five node types:

```
[trigger] → [condition] → [action] → [retry] → [observe]
```

| Type | Purpose | Example |
|------|---------|---------|
| Trigger | Starts the workflow | Cron, webhook, event, manual |
| Condition | Gate; skip branch if false | "user has paid plan" |
| Action | Does the work | API call, DB write, email |
| Retry | Recovery on failure | Backoff, max attempts, DLQ |
| Observe | Logs, metrics, alerts | Log to DB, emit metric, page |

## Worked Example: "Send weekly digest"

```
Trigger:  cron(0 9 * * 1)
Condition: db.users.count(active_in_last_7d > 0)
Action:    fetch eligible_users
Condition: eligible_users.length > 0
Action:    render digest HTML
Action:    send via email provider
Retry:     exponential backoff, 3 attempts, fail → DLQ
Observe:   log sent_count, failed_count, duration_ms
Observe:   emit metric('digest.sent')
Observe:   if failed_count > 0 → alert
```

## Trigger Design

| Trigger | Use when | Watch out for |
|---------|----------|---------------|
| Cron | Time-based, batch | Timezone drift, DST |
| Webhook | External event | Replay, ordering, idempotency |
| Event bus | Internal service event | Schema evolution, lost events |
| Manual | On-demand | No automation, easy to forget |
| File watch | File lands in S3 | Missed events, partial uploads |

Rule: **one trigger per workflow.** Multiple triggers = multiple workflows.

## Conditions

Conditions save you from:
- Running on empty data ("send to 0 users")
- Running outside business hours
- Running during maintenance
- Re-running an already-completed step

```python
if eligible_users.empty:
    logger.info("no eligible users; skipping")
    return
```

## Anti-patterns

- Skipping verification when the change 'feels small'
- Reasoning by analogy without a real example
