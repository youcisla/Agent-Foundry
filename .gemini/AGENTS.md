# Agent Foundry — Gemini CLI / Antigravity CLI Guide

Agent Foundry installs as an agent-skills bundle plus a Gemini extension.

## Skill discovery

| Scope | Path |
| --- | --- |
| Gemini CLI user | `~/.gemini/skills/<skill>/SKILL.md` |
| Cross-tool user | `~/.agents/skills/<skill>/SKILL.md` |
| Gemini extension | `~/.gemini/extensions/agent-foundry/skills/<skill>/SKILL.md` |
| Workspace | `.gemini/skills/` or `.agents/skills/` |

Skills must be **direct children** of the skills root. Do not nest a shared
parent folder: the scanner reads `<root>/<skill>/SKILL.md`.

## Install

```bash
node scripts/install.js --harness=gemini-cli
```

This writes 39 skill links, a `gemini-extension.json`, and `GEMINI.md`.
Restart the CLI, then run `/extensions list` or `/skills` to verify.

## Antigravity

Antigravity has three global roots:

| Product | Global skills |
| --- | --- |
| App / IDE | `~/.gemini/config/skills/` |
| Antigravity CLI | `~/.gemini/antigravity-cli/skills/` |
| Shared by npx skills | `~/.agents/skills/` |

```bash
node scripts/install.js --harness=antigravity
```

Workspace skills live in `.agents/skills/`; legacy `.agent/skills/` is still
read but should not be used for new installs. Legacy workflows are deprecated;
use skills.
