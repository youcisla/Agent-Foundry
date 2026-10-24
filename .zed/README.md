# Agent Foundry â€” Zed Adapter

**Status:** Beta â€” skills install into Zed's supported global root.

Zed loads skills from:

| Scope | Path |
| --- | --- |
| Global | `~/.agents/skills/<skill>/SKILL.md` |
| Project | `.agents/skills/<skill>/SKILL.md` |

Each skill must be a direct child. Zed does not support nested skill folders.

## Install

```bash
node scripts/install.js --harness=zed
```

The installer links 41 skills into `~/.agents/skills`. It also prints the
platform-specific personal instructions path:

- macOS / Linux: `~/.config/zed/AGENTS.md`
- Windows: `%APPDATA%\Zed\AGENTS.md`

Project instructions can use `AGENTS.md`, `.rules`, `.cursorrules`,
`.windsurfrules`, `.clinerules`, or `.github/copilot-instructions.md`.
