---
name: cron-troubleshoot
description: 'Debug a cron job that failed or didn''t run: timezone, drift, overlap,
  missing logs, dependency failure. Use when a scheduled job is missing, late, or
  producing wrong results.'
version: 0.1.0
license: MIT
provenance:
  inspired: true
author: Youcisla
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

## Step 5 — Check for Overlap

Slow job + frequent schedule = overlapping runs. Symptoms: double counts, DB locks.

Fixes:
1. `flock`: `* * * * * flock -n /tmp/job.lock /path/to/job.sh`
2. Systemd timer with `Persistent=true`
3. Queue + worker pattern

## Step 6 — Verify Environment

Cron env is minimal. No aliases, no shell init, no interactive paths.

Diagnose:

```cron
* * * * * env > /tmp/cron.env
```

Replicate:

```bash
env -i $(cat /tmp/cron.env | grep -v '^#' | xargs) /path/to/job.sh
```

Common missing: `PATH` (use full paths), `HOME`, API keys, virtualenv activation.

## Step 7 — Check Dependencies

```bash
psql -c "select 1"
curl -fsS https://api.example.com/health
df -h /var/log && free -m
```

Pre-flight checks at job start:

```bash
[[ -d /var/data ]] || { echo "data dir missing"; exit 1; }
curl -fsS https://api.example.com/health >/dev/null || { echo "api down"; exit 1; }
```

## Step 8 — Check Clock Drift

```bash
chronyc tracking   # or ntpq -p
```

Fix: enable NTP or use a managed scheduler (systemd timers, k8s CronJob, GitHub Actions).

## Step 9 — Check Secret / Permission Drift

After deploys, secrets rotate. Cron doesn't refresh until the daemon restarts.

```bash
systemctl restart cron
# Or: source latest secrets inline
* * * * * source /etc/secrets.env && /path/to/job
```

## Step 10 — Replay

```bash
env -i $(cat /tmp/cron.env | grep -v '^#' | xargs) /path/to/job.sh
tail -f /var/log/cronjob.log
```

## Anti-patterns

- Silent `MAILTO=""` without redirecting output
- Two crons at the same minute doing the same thing
- "It worked on my laptop" — cron env ≠ interactive env
- No `flock` on a frequent job, hard-coded paths that break when cwd changes