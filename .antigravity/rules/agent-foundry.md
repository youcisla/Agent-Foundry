---
trigger: always_on
description: "Plan before code, verify before done, and avoid generic AI output when Agent Foundry skills are installed."
---

# Agent Foundry rules for Antigravity

Apply these rules when Agent Foundry skills are installed:

- Skills are direct children of `.agents/skills/` (workspace),
  `~/.gemini/config/skills/` (App/IDE), or
  `~/.gemini/antigravity-cli/skills/` (CLI).
- Use `plan-before-code` before non-trivial edits.
- Use `verify-first` before claiming work is done.
- Run `af-critic` when the harness exposes the subagent.
- Quality gates: `foundry-eval`, schema validation, no generic AI slop.
