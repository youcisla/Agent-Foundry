# Agent Foundry — JoyCode Adapter

**Status:** Beta — adapter structure defined.

JoyCode uses skills + commands + agents under `.joycode/`.

## Layout

```
.joycode/
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
node scripts/install.js --harness=joycode
```