# Agent Foundry — Claude Project Adapter

**Status:** Coming soon — `claude-project` is identical to claude-code but
installs into `./.claude/` (per-project) instead of `~/.claude/`. We ship it
as a separate target once the local install path is verified.

## Expected layout

```
.claude/
  skills/
    agent-foundry/
      SKILL.md  (linked from skills/)
```

## Install

```bash
node scripts/install.js --harness=claude-project
```

Currently aliases to the standard claude-code install path.