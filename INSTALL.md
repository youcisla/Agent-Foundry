# Install

Agent-Foundry v0.1.0 installs as a single skills namespace into any supported harness.

## Quick install (auto-detect)

```bash
git clone https://github.com/youcisla/Agent-Foundry.git
cd Agent-Foundry
./scripts/install.sh
```

The script auto-detects your harness (Claude Code → Codex → Cursor → Hermes → Gemini CLI → OpenCode in that order) and creates the right symlink.

## Explicit harness

```bash
./scripts/install.sh --harness=claude-code
./scripts/install.sh --harness=codex
./scripts/install.sh --harness=hermes
./scripts/install.sh --harness=gemini-cli
./scripts/install.sh --harness=opencode
```

## Manual install (Cursor)

Cursor reads `.cursor/rules/` directly. Copy what you want:

```bash
cp skills/core/prompt-discipline/SKILL.md .cursor/rules/agent-foundry-prompt-discipline.mdc
```

(`.mdc` extension tells Cursor it's a rule file.)

## What gets installed

- `~/.claude/skills/agent-foundry/` (or harness equivalent) — symlink to this repo's `skills/` dir
- 16 core skills (in `skills/core/`): `prompt-discipline`, `context-optimization`, `anti-slop`, `plan-before-code`, `plan-then-act`, `constraint-then-solve`, `quality-protocol`, `verify-first`, `re-verify-findings`, `measure-first`, `bottleneck-gating`, `pushback-when-wrong`, `read-before-build`, `show-your-work`, `landscape-first`, `session-closeout`
- 6 optional skills (in `skills/optional/`): `design-language`, `chrome-devtools-mcp-bridge`, `claude-mem-persistent-memory`, `headroom-token-compression`, `funnel-pr-guard`, `sql-migration-trio`
- **Total: 22 skills installed.**

The harness picks them up via the standard `description` field trigger mechanism. No force-loading.

## Verify

```bash
# In your harness
# Trigger any core skill by name or trigger phrase

# Or run our validator
./scripts/validate.sh
```

## Uninstall

```bash
rm ~/.claude/skills/agent-foundry     # Claude Code
rm ~/.codex/skills/agent-foundry      # Codex
rm ~/.hermes/skills/agent-foundry     # Hermes
# (etc.)
```

The symlink is removed; the repo stays on disk.
