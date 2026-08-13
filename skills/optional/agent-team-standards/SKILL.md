---
name: agent-team-standards
description: Per-project locked agent skill set with version pins. Share the same agent setup across a team (or your own projects) by locking skill versions in a manifest file. Use when the user wants reproducible agent behavior across repos, or team-wide skill governance.
version: 1.0.0
license: MIT
author: Agent Foundry Contributors
category: optional
tags: [agent-foundry, agent, team, standards, lockfile, capshelf, governance, reproducible]
platforms: [linux, macos, windows]
---

# Agent Team Standards

Lock the agent skill set + config per project, so every run (CI, cron, dev's laptop) gets the identical toolchain.

## Usage

```bash
# Lock current installed skills to a manifest
python scripts/ats.py lock --project-dir=. --output=agent-teams.lock.json

# Apply a manifest (install exact versions)
python scripts/ats.py apply --manifest=agent-teams.lock.json

# Diff current state vs manifest
python scripts/ats.py diff --manifest=agent-teams.lock.json

# Validate manifest
python scripts/ats.py validate --manifest=agent-teams.lock.json
```

## Manifest format

```json
{
  "schema_version": "1.0",
  "project": "my-project",
  "generated_at": "2026-08-13T...",
  "skills": [
    {
      "name": "agent-memory-vault",
      "category": "agentic",
      "version": "1.0.0",
      "installed": true,
      "path": "agentic/agent-memory-vault"
    }
  ],
  "config_fragments": {
    "AGENTS.md": "...",
    "models": ["openai/gpt-4.1", "anthropic/claude-fable-5"]
  }
}
```

## Companion skills

- effective-agent-skills (installed): per-skill authoring standards
- global-agent-guardrails (installed): safety policies to bundle
- distribute-skill-to-all-agents (installed): sync mechanism
- agent-memory-vault (installed): remember which standards applied where

## Use case

Every project that runs in cron should have an `agent-teams.lock.json`. New devs / fresh clones / CI just run `ats apply` and get the exact same skill versions.
