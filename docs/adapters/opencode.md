# OpenCode

OpenCode discovers skills from:

- `.opencode/skills/<skill>/SKILL.md` (project)
- `~/.config/opencode/skills/<skill>/SKILL.md` (global)
- `.claude/skills/`, `~/.claude/skills/`
- `.agents/skills/`, `~/.agents/skills/`

Skills must be direct children of the skills root.

## Install

```bash
node scripts/install.js --harness=opencode
```

This links 41 skills into `~/.config/opencode/skills/` and copies the
instruction files into `~/.config/opencode/agent-foundry/instructions/`.

Agent and command definitions are not auto-merged into
`~/.config/opencode/opencode.json`; the installer prints both paths so you can
merge them deliberately.
