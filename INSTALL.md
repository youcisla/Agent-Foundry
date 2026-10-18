# Install

Agent Foundry is a Python package (`agent-foundry`) plus a cross-platform installer. It installs a local daemon that plans, dispatches, executes, and logs skill runs. Works on macOS, Linux, and Windows. Python 3.10+, or Node 18+ for the installer-only path.

## Quick install

macOS / Linux / Git Bash:

```bash
curl -fsSL https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/install.sh | bash
```

Windows (PowerShell):

```powershell
irm https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/scripts/install.ps1 | iex
```

From npm (cross-platform, Node 18+):

```bash
npm install -g @youcisla/agent-foundry
agent-foundry            # auto-detect harness and install
agent-foundry --list     # show all supported targets
```

From PyPI (Python 3.10+, includes the CLI and MCP runtime):

```bash
pip install agent-foundry-runtime
agent-foundry doctor
uvx agent-foundry-runtime mcp
```

Harness paths, quirks, and dos/don'ts:
[docs/harness-compatibility.md](docs/harness-compatibility.md).

Then set an API key:

```bash
export ANTHROPIC_API_KEY=sk-...   # macOS / Linux
$env:ANTHROPIC_API_KEY="sk-..."   # Windows PowerShell
```

The shell installer is idempotent (re-run to update). It:

1. Checks for Python 3.10+.
2. Clones the repo to `~/.agent-foundry`.
3. Creates a venv at `~/.config/agent-foundry/venv` and runs `pip install -e .`.
4. Links each skill into `~/.claude/skills/<skill>` and the plugin into
   `~/.claude/plugins/agent-foundry` (plugin optional; skills do not need it).
5. Runs `agent-foundry init` (writes `~/.config/agent-foundry/config.toml` + the first skill index).

On Windows the `.ps1` and `.bat` scripts delegate to the same `scripts/install.js` Node entry point, which handles directory junctions with hard-link and copy fallbacks.

## Harness install

`scripts/install.js` writes each skill as a direct child of the harness's
documented discovery root. It records what it installed in
`.agent-foundry-installed.json` and never deletes user-authored skills.

```bash
node scripts/install.js --list
node scripts/install.js --harness=codex --dry-run
node scripts/install.js --harness=codex
node scripts/install.js --harness=cursor --copy   # portable copy
```

| Target | Skill root |
| --- | --- |
| `claude-code` | `~/.claude/skills/` |
| `claude-project` | `<project>/.claude/skills/` |
| `codex` | `~/.agents/skills/` |
| `cursor` | `~/.cursor/skills/` |
| `hermes` | `~/.hermes/skills/agent-foundry/` |
| `gemini-cli` | `~/.gemini/skills/` + extension |
| `opencode` | `~/.config/opencode/skills/` |
| `antigravity` | `~/.gemini/config/skills/`, `~/.gemini/antigravity-cli/skills/`, `~/.agents/skills/` |
| `codebuddy` | `~/.codebuddy/skills/` |
| `joycode` | `~/.joycode/skills/` |
| `qwen` | `~/.qwen/skills/` |
| `kimi` | `~/.kimi-code/skills/` + `~/.agents/skills/` |
| `openclaw` | `~/.openclaw/skills/agent-foundry/` + `~/.agents/skills/` |
| `zed` | `~/.agents/skills/` |

Every run also refreshes `~/.config/agent-foundry/skills/`, the dedicated root
the CLI indexer ranks. Keeping it separate prevents `agent-foundry plan` from
matching unrelated skills installed by other packages.

## Install profiles

```bash
AF_PROFILE=minimal curl -fsSL https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/install.sh | bash   # skills only, no daemon
AF_PROFILE=core    curl -fsSL https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/install.sh | bash   # skills + daemon (default)
AF_PROFILE=full    curl -fsSL https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/install.sh | bash   # skills + daemon + hooks
```

## Manual install

```bash
git clone https://github.com/youcisla/Agent-Foundry.git ~/.agent-foundry
cd ~/.agent-foundry
pip install -e .
agent-foundry init

# Claude Code: one link per skill, directly under the skills root
mkdir -p ~/.claude/skills
for d in "$PWD"/skills/*/*; do
  [ -f "$d/SKILL.md" ] && ln -s "$d" "$HOME/.claude/skills/$(basename "$d")"
done

# Cross-tool root read by Codex, Zed, Gemini, Kimi, and others
mkdir -p ~/.agents/skills
for d in "$PWD"/skills/*/*; do
  [ -f "$d/SKILL.md" ] && ln -s "$d" "$HOME/.agents/skills/$(basename "$d")"
done
```

## Use it

In Claude Code:

```
/plan "audit this API"          # rank the skills that match
/af   "build a react component" # plan + execute the top skill
```

Or from the CLI:

```bash
agent-foundry plan "kill generic AI slop"
agent-foundry run  "refactor the API design"
agent-foundry doctor            # health-check config, index, daemon, API key
agent-foundry --help
```

## Verify the install

```bash
agent-foundry doctor            # config / index / daemon / API key
python3 scripts/foundry-eval.py # quality gate: 34 passed, 0 failed
./scripts/validate.sh           # skill lint: 35 skills, 0 failed
```

## Uninstall

```bash
rm ~/.claude/plugins/agent-foundry   # remove the plugin symlink (macOS/Linux)
find ~/.claude/skills ~/.agents/skills -maxdepth 1 -type l -lname '*Agent-Foundry*' -delete
rm -rf ~/.agent-foundry              # remove the repo
rm -rf ~/.config/agent-foundry       # remove config, venv, and logs
```

On Windows, remove the equivalent paths under `%USERPROFILE%` and `%APPDATA%\agent-foundry`.

## Requirements

- Python 3.10+ (for the daemon) or Node 18+ (for the installer-only path)
- macOS, Linux, or Windows
- An Anthropic or OpenAI API key (the daemon uses LiteLLM, so any supported model works)
