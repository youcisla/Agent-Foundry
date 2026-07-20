---
name: cron-troubleshoot
description: 'Debug a cron job that failed or didn''t run: timezone, drift, overlap,
  missing logs, dependency failure. Use when a scheduled job is missing, late, or
  producing wrong results.'
version: 0.1.0
license: MIT
author: Agent Foundry Contributors
---

# Cron Troubleshoot

A systematic checklist for cron jobs that failed, ran twice, didn't run, or produced wrong output.

## Seven Failure Modes

| Mode | Symptom | Common cause |
|------|---------|--------------|
| Wrong schedule | Runs at wrong time | Timezone, DST, misread cron syntax |
| No overlap protection | Two runs collide | Slow previous run + frequent schedule |
| Missing env | Fails immediately | Cron env is empty; PATH different |
| Dependency down | Fails partway | DB / API / cache unreachable |
| Silent failure | No logs | Output redirected or discarded |
| Permission drift | Fails after deploy | File ownership, secret rotation |
| Clock drift | Late by minutes | Server NTP not synced |

## Step 1 — Verify It Ran

```bash
grep CRON /var/log/syslog
journalctl -u cron --since "1 hour ago"
crontab -l
```

No log entry → schedule didn't fire (Step 2). Log entry, no output → silent failure (Step 4).

## Step 2 — Verify the Schedule

Common mistakes:

```cron
# WRONG — runs every minute of midnight (1440 runs/day)
0 * * * *
# RIGHT — runs at midnight
0 0 * * *
```

Verify at crontab.guru.

## Step 3 — Check Timezone

```bash
date && timedatectl && TZ=America/New_York date
```

Fix: set `TZ=...` at the top of crontab, or convert to UTC.

## Step 4 — Check for Silent Failure

Cron emails output by default. If you don't read mail, failures are silent.

Fix:

```cron
MAILTO=""
* * * * * /path/to/job >> /var/log/cronjob.log 2>&1
```

Or wrap:

```bash
#!/bin/bash
exec >> /var/log/cronjob.log 2>&1
echo "=== $(date) ==="
/path/to/real-job
```

## Anti-patterns

- Skipping verification when the change 'feels small'
- Reasoning by analogy without a real example
