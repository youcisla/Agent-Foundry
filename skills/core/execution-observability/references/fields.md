# Observation fields

| Field | Meaning |
|---|---|
| `trace_digest` | canonical identity of the request and output |
| `request_meta_json` | model revision, runtime, hashes, roles, sizes |
| `phases_json` | inclusive stage durations in milliseconds |
| `judge_status` | ok / unparseable / call_failed / timeout |
| `failure_kind` | provider / schema / policy / attest / budget / internal |
| `output_ref` | full-output artifact, inline preview is bounded |
