# Agent Foundry — Claude Code Project Adapter

**Status:** Beta — installs every skill as a direct child of the project's
`.claude/skills/` directory.

Claude Code scans `<project>/.claude/skills/<skill>/SKILL.md`. Nesting skills
under a shared parent folder is not supported.

## Layout

```text
.claude/
  skills/
    api-design/SKILL.md
    plan-before-code/SKILL.md
    verify-first/SKILL.md
    ... (35 total)
    .agent-foundry-installed.json
```

## Install

Run from the target project root:

```bash
node /path/to/Agent-Foundry/scripts/install.js --harness=claude-project
```

Re-runs replace only skills recorded in `.agent-foundry-installed.json`;
project-specific skills with other names are preserved.
