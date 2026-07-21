# Agent Foundry — Antigravity Adapter

**Status:** Beta — adapter structure defined, end-to-end behavior not yet tested.

Antigravity is a code-centric agent harness (similar to Cursor/Claude Code
patterns). It expects:

- Rules: `.agent/rules/*.md`
- Skills: `.agent/skills/<id>/SKILL.md`
- Workflows: `.agent/workflows/*.md`
- Agents: `.agent/agents/<id>.md`

This adapter mirrors that layout.

## Install

```bash
node scripts/install.js --harness=antigravity
```

## Layout

```
.agent/
  rules/
    agent-foundry.md
  skills/
    agent-foundry/
      SKILL.md
  workflows/
    agent-foundry.md
```

## Test status

- [x] Adapter structure created
- [x] Install dry-run succeeds
- [ ] End-to-end test on real Antigravity install