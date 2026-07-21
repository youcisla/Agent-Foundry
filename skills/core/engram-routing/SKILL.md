---
name: engram-routing
description: "Route prompts via N-gram keyed lookup table (Engram-style conditional memory). Use when prompts are frequent and trigger patterns should match in O(1) instead of linear scan."
version: 0.1.0
author: Agent Foundry Contributors
---

# engram-routing

Engram-style routing for skill selection. Inverted from
[DeepSeek's Engram paper](https://github.com/deepseek-ai/Engram):

> **Conditional memory via scalable lookup.** We don't recompute the skill
> match for every prompt — we hash the prompt's N-gram signature and look it
> up in a precomputed table.

## When to use

- A prompt pattern repeats across sessions (same user, similar tasks)
- Linear scan over 30 skills is wasteful for hot patterns
- You want O(1) routing for the top 5% of prompts that drive 80% of usage

## Procedure

### 1 - Build the lookup table

Normalize the prompt to lowercase, strip punctuation, tokenize on
whitespace. Generate 2-grams and 3-grams from the token sequence. For each
N-gram, compute a stable hash (e.g. SHA-1 truncated to 16 hex chars).

### 2 - Index by skill

For each N-gram, record which skill(s) historically matched it and
with what confidence. This is the Engram table.

### 3 - Route via lookup

For an incoming prompt: extract its N-grams, hash them, look up each
in the table. If a high-confidence match exists, dispatch directly.
Otherwise, fall back to the standard `plan` flow.

### 4 - Update from feedback

When the standard plan flow matches a skill for a prompt, record the
N-gram hash → skill mapping in the Engram table. Over time, hot prompts
get O(1) routing.

## Anti-patterns

- Do NOT use Engram routing as the only routing mechanism — fall back to
  plan for cold/cold-warm prompts.
- Do NOT let the Engram table grow unbounded — cap at 10k entries; evict
  LRU when full.
- Do NOT trust Engram matches above confidence 0.95 without a verification
  pass — fast routing must not bypass quality.

## Verification

After implementing, run the smoke test:

```python
python scripts/smoke-test.py
# Should report: Engram table size, hit rate, fallback rate
```
