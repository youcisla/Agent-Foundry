# Agent Foundry — JoyCode Adapter

**Status:** Beta — adapter structure defined.

JoyCode uses skills + commands + agents under `.joycode/` (project) or
`~/.joycode/` (user).

## Layout

```text
.joycode/
  rules/
    agent-foundry.md
  skills/
    api-design/SKILL.md
    plan-before-code/SKILL.md
    ... (39 total)
  commands/
    af.md
```

Skills must be direct children of `.joycode/skills/`.

## Install

```bash
node scripts/install.js --harness=joycode
```
