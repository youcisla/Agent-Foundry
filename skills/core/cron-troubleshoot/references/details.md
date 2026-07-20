# Cron Troubleshoot - Details

Deep material that was moved out of the main skill body to keep it under the 150-line cap.

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


## Verification Checklist

- [ ] The claim or action has been verified against a live source
- [ ] The output matches the request's scope (no scope creep)
- [ ] Slop markers are absent (filler, hedging, emoji headers)
