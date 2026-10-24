---
name: cache-identity
description: "Use when caching model results, latency, or artifacts: build a versioned key, bound the store, publish atomically, and never trust an unvalidated cache path."
version: 0.1.0
author: Agent Foundry Contributors
---

# cache-identity

A cache is a claim about identity. If the key is wrong, every hit is a bug.

## Contract

- Key fields: runtime version, git SHA (dirty marker), model revision, effective parameters, prompt or skill hash, load bucket.
- Length-prefix each field before hashing so concatenation cannot collide.
- Store numbers and references only. Never deserialize executable content from a cache path.
- Enforce a TTL and a row or byte cap; evict oldest first.
- Publish atomically: temp file, flush, fsync, rename, marker. A losing concurrent publish is success.
- A cache read failure returns a miss, never an exception to the caller.
- Success and failure latency are separate fields.

## Procedure

1. Compute the key from resolved values, not raw user input.
2. Look up; return a miss when the row is absent, expired, malformed, or version-mismatched.
3. On write, update running means and the timestamp in one statement.
4. Prune on a schedule or at write time; never let the store grow unbounded.
5. On release, record the format version so a shape change cannot mix generations.

## Anti-patterns

- Keying on model name alone while parameters change.
- A cache directory trusted as a code or binary source.
- Unbounded grammar or prompt caches; they are denial-of-service vectors.
- Deleting a file a reader may still have open; expire first, delete after a slack window.

## Verification Checklist

- [ ] Changing any key field produces a miss.
- [ ] Expired rows are invisible.
- [ ] Concurrent publish loses safely.
- [ ] Corrupt entries are ignored.
- [ ] The store stays under its cap.
- [ ] Success and failure latencies stay separate.

## Composes With

- `measure-first` — benchmark baselines are a separate artifact
- `execution-observability` — cache identity appears in request metadata
- `context-optimization` — artifact spill uses the same publish rules
