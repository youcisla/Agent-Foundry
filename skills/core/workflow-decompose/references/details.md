# Workflow Decompose - Details

Deep material that was moved out of the main skill body to keep it under the 150-line cap.

## Action Best Practices

- **Idempotent**: running twice = same result. Use upserts, not inserts.
- **Scoped**: one thing, not five.
- **Auditable**: log what you did with an ID linking back to the trigger.
- **Bounded**: set a timeout. Long actions should be split.

## Retry Patterns

### Linear backoff
```python
for attempt in range(3):
    try:
        action()
        break
    except RetryableError:
        sleep(attempt * 5)
```

### Exponential with jitter
```python
for attempt in range(5):
    try:
        action()
        break
    except RetryableError:
        sleep((2 ** attempt) + random.uniform(0, 1))
```

### Dead-letter queue
```python
except MaxRetriesExceeded:
    db.dlq.insert({workflow, payload, error, attempts})
    alert("workflow failed permanently")
```

## Idempotency Mechanisms

- **Idempotency keys**: pass through to the action
- **State check**: "did we already process this?"
- **Unique constraints**: DB-level dedup
- **Marker files**: `~/.workflows/weekly-digest.2026-07-20.done`

## Observability

Every workflow logs:

```python
log.info("workflow.start", workflow=NAME, trigger=trigger_id)
log.info("workflow.step", step="send_email", count=N)
log.info("workflow.end", status="ok", duration_ms=ELAPSED)
```

Emit metrics:
- `workflow.runs.total` (counter)
- `workflow.runs.failed` (counter)
- `workflow.duration_ms` (histogram)
- `workflow.last_success` (gauge)

Alert on:
- Failure rate > 5%
- Duration > 2× normal
- No success in expected interval (stalled)

## Anti-patterns

- "Just retry forever" — masks the real problem
- "If it fails, log and move on" — silent failures
- Multiple triggers for one workflow — operational nightmare
- No idempotency — duplicate sends/writes
- Logging payload without an ID — can't correlate
- No timeout — one slow action stalls the pipeline


## Verification Checklist

- [ ] The claim or action has been verified against a live source
- [ ] The output matches the request's scope (no scope creep)
- [ ] Slop markers are absent (filler, hedging, emoji headers)
