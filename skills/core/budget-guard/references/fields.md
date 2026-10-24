# Budget fields

- `token_budget` — per-session aggregate.
- `per_call_token_budget` — single-call ceiling; 0 disables.
- `max_attempts` — distinct chain entries, not transport retries.
- `max_concurrency` — fan-out ceiling.
- `checkpoint_every` — durable progress cadence.
