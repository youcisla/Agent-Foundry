# Agent Foundry — Codebuddy Adapter

**Status:** Beta — adapter structure defined, end-to-end behavior not yet tested.

Codebuddy uses a flattened rules/skills/commands/agents layout.

## Layout

```
.codebuddy/
  rules/
    agent-foundry.md
  skills/
    agent-foundry/
      SKILL.md
  commands/
    af.md
  agents/
    af-critic.md
```

## Install

```bash
node scripts/install.js --harness=codebuddy
```