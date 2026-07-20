---
name: persistent-memory
description: Persistent context across sessions for any agent — captures tool calls,
  file edits, and decisions; compresses the transcript with AI; injects relevant past
  context into future sessions. Works with Claude Code, Codex, Gemini, Hermes, OpenCode.0).
  Use when persisting context across sessions or threading memory across agents.
version: 0.1.0
license: Apache-2.0
author: Agent Foundry Contributors
---

# Persistent Memory

A cross-session persistent memory system for AI agents. Captures every tool call, file edit, and decision; compresses the transcript; injects relevant past context into future sessions.

## When to Use

- Long-running projects where context compounds across sessions
- You want every agent action logged, compressed, and retrievable
- Repeated question: "what did we do about X last week?"
- Multiple agents working on the same repo (shared memory)

## How It Works

1. **Capture**: every tool call and file edit is recorded via hooks
2. **Compress**: an AI model summarizes the session into observations
3. **Store**: observations are persisted to a knowledge graph
4. **Inject**: relevant past observations are injected into future sessions

## Platform Support

| Platform | Status |
|----------|--------|
| Claude Code | ✅ Full support |
| Codex | ✅ Full support |
| Cursor | ✅ Full support |
| Gemini CLI | ✅ Full support |
| Hermes | ✅ Full support |
| OpenCode | ✅ Full support |

## Installation

Refer to the upstream repository for the latest install instructions.

## Key Concepts

- **Entity**: a thing being tracked (user, codebase, decision, file)
- **Observation**: a fact about an entity (the decision made, the file changed)
- **Relation**: a link between two entities (this depends on that)
- **Cross-session injection**: before each session starts, relevant past observations are pulled and injected into the prompt

## Anti-patterns

- Using this as a substitute for project docs (it captures state, not design rationale)
- Expecting it to work without configuring the platform adapter
- Relying on it for first session (no history to inject yet)


## Verification Checklist

- [ ] The claim or action has been verified against a live source
- [ ] The output matches the request's scope (no scope creep)
- [ ] Slop markers are absent (filler, hedging, emoji headers)
