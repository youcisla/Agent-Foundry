# Cache key fields

| Field | Why it changes identity |
|---|---|
| runtime version + git SHA | prompt assembly or validation code changed |
| dirty marker | uncommitted code cannot be reproduced |
| model revision | provider weights or serving stack changed |
| effective params | temperature, seed, max tokens, stop tokens |
| prompt/skill hash | the bytes sent changed |
| load bucket | latency regime changed with concurrency |
| format version | the stored value shape changed |

Length-prefix each field: `len(field) + ":" + field`, joined in a fixed order,
then hashed once. A missing field is represented explicitly, never skipped.
