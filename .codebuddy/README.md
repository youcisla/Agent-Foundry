# Agent Foundry — CodeBuddy Adapter

**Status:** Beta — adapter structure defined, end-to-end behavior not yet tested.

CodeBuddy uses a flattened rules/skills/commands/agents layout.

## Layout

```text
.codebuddy/
  rules/
    agent-foundry.md
  skills/
    api-design/SKILL.md
    plan-before-code/SKILL.md
    ... (39 total)
  commands/
    af.md
  agents/
    af-critic.md
```

Skills must be direct children of `.codebuddy/skills/`. Nested skill folders
are not scanned.

## Install

```bash
node scripts/install.js --harness=codebuddy
```
