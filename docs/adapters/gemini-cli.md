# Gemini CLI / Antigravity CLI

Gemini CLI loads skills from `~/.gemini/skills/<skill>/SKILL.md` and the
cross-tool alias `~/.agents/skills/<skill>/SKILL.md`. It also supports real
extensions at `~/.gemini/extensions/<name>/gemini-extension.json`.

## Install

```bash
node scripts/install.js --harness=gemini-cli
```

This writes:

- 35 skill links under `~/.gemini/skills/`
- `~/.gemini/extensions/agent-foundry/gemini-extension.json`
- `~/.gemini/extensions/agent-foundry/GEMINI.md`
- 35 skill links under the extension's `skills/` directory

Restart the CLI and run `/extensions list` or `/skills` to verify.

## Antigravity

Antigravity has separate roots:

- App / IDE: `~/.gemini/config/skills/`
- Antigravity CLI: `~/.gemini/antigravity-cli/skills/`
- Workspace: `.agents/skills/`
- Shared: `~/.agents/skills/`

Install all global roots with:

```bash
node scripts/install.js --harness=antigravity
```

Legacy `.agent/skills/` and workflows are deprecated; use skills.
