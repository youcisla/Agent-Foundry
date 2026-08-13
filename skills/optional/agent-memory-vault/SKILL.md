---
name: agent-memory-vault
description: Shared, structured memory store that survives agent sessions - lets an autonomous agent remember context, user preferences, prior decisions, and project state across cron-driven runs. Use when the user says 'remember this', 'what did we decide last time', 'pick up where we left off', or any autonomous workflow that needs persistent memory.
version: 1.0.0
license: MIT
author: Agent Foundry Contributors
category: optional
tags: [agent-foundry, agent, memory, persistent, autonomous, cron, state]
platforms: [linux, macos, windows]
---

# Agent Memory Vault

Persistent, structured memory for autonomous agents. Survives session restarts, works across cron-driven runs, supports multi-agent shared state.

## Architecture

- Storage: ~/.agent-memory/ (project-local) or AGENT_MEMORY_HOME env var
- Format: JSON Lines (.jsonl) per topic + index .json
- Concurrency: file-locked reads/writes (cross-platform fcntl/msvcrt)

## Usage

```bash
# Append a memory entry
python scripts/memory.py put --topic=preferences --key=code-style --value="2-space indent"

# Retrieve
python scripts/memory.py get --topic=preferences --key=code-style

# List topics and entries
python scripts/memory.py list

# Show context for next session
python scripts/memory.py context --last=10
```

## Memory topics

| Topic | What goes here |
|-------|----------------|
| preferences | User preferences (style, tools, languages) |
| decisions | Architecture / design decisions with rationale |
| project-state | What is in progress, blockers, recent changes |
| errors | Errors encountered and fixes |
| people | Names, roles, contact info |
| glossary | Domain-specific terms |

## Cron use case

```bash
# Daily research agent uses memory-vault to track what it learned
0 9 * * * cd ~/agent && pi run "use --agent-memory-vault to read preferences and append today's findings"

# Weekly audit reads recent decisions
0 17 * * 5 cd ~/agent && pi run "use --agent-memory-vault to list --topic=decisions --last=30"
```

## Companion skills

- agent-self-scheduling (installed) for the cron wrapper
- goal-loop (installed) for the autonomous agent loop
- handoff (installed) for cross-session context transfer
