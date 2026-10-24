---
name: context-optimization
description: Keep tool outputs small, sandbox large files, reference not repeat. Use
  on any task with >2K-token outputs, big files, or repeated reads. Use on any task
  that touches files > 50 KB or runs longer than a few minutes.
version: 0.1.0
license: MIT
author: Agent Foundry Contributors
---

# Context Optimization

Small context is fast context. Apply these rules on any task that reads files or calls tools.

## The rules

1. **Don't dump — summarize.** When a tool returns >2K tokens, return a summary + the path. Not the whole blob.
2. **Sandbox large files.** A 5,000-line file → write the interesting parts to a sandbox path, return the path + a grep tool the agent can use. Re-reads are free.
3. **Reference, don't repeat.** If you read it once, don't paste it again. Quote the file path and the line range.
4. **One tool call, one purpose.** Don't bundle a read + a search + a write in one step. Each call has its own tool result overhead.
5. **Stop when you have enough.** First successful outcome is enough. Don't run the test 10 times to "be sure."

## When output really is the answer

Some outputs must be verbatim:
- Stack traces with file:line
- Exact error messages
- Test diffs
- The user's quoted text

For these, the rule is **truncate the noise, keep the signal** — remove timestamps, request IDs, repeated headers.

## When this conflicts with other goals

If the user asks for a literal paste of a file, do it. Context is a default, not a law.

## When to skip

- The user is debugging interactively and needs the full output once.
- The tool returns <500 tokens — already small enough.


## Anti-patterns

- Skipping verification when the change "feels small"
- Reasoning by analogy without a real example
- Acting on a claim you have not verified this session
- Choosing speed over accuracy when accuracy is what the task requires


## Verification Checklist

- [ ] The claim or action has been verified against a live source
- [ ] The output matches the request's scope (no scope creep)
- [ ] Slop markers are absent (filler, hedging, emoji headers)

## Compaction and Spill

- Cap history by estimated tokens and keep the newest N turns. Record `compacted_turns` and dropped tokens; silent loss is a correctness bug.
- Compaction is destructive. State the approximation: dropped turns are gone, not summarized, unless a summary backend exists.
- Spill the full output to a private artifact and keep a bounded inline preview. Never truncate the only copy.
- Return an opaque locator plus retrieval guidance. Treat the locator as a handle, not a path to parse.
- A spill failure keeps the inline result; it must not fail the model call.
- Create artifact directories private (0700) and files exclusively (0600). Never derive a filename from user text.
- Publish artifacts by temp file, fsync, rename. A half-written artifact is worse than a missing one.
