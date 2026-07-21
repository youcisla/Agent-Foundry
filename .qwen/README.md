# Agent Foundry — Qwen CLI Adapter

**Status:** Beta — adapter structure defined.

Qwen CLI uses `.qwen/` with skills, commands, rules.

## Layout

```
.qwen/
  rules/
    agent-foundry.md
  skills/
    agent-foundry/
      SKILL.md
  commands/
    af.md
```

## Install

```bash
node scripts/install.js --harness=qwen
```