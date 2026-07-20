# Install

Agent Foundry is a Python package (`agent-foundry`) plus a thin Claude Code plugin. It installs a local daemon that plans, dispatches, executes, and logs skill runs. macOS and Linux; Python 3.10+.

## Quick install (recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/install.sh | bash
export ANTHROPIC_API_KEY=sk-...   # or OPENAI_API_KEY
```

The installer is idempotent (re-run to update). It:

1. Checks for Python 3.10+.
2. Clones the repo to `~/.agent-foundry`.
3. Creates a venv at `~/.config/agent-foundry/venv` and runs `pip install -e .`.
4. Symlinks the plugin into `~/.claude/plugins/agent-foundry`.
5. Runs `agent-foundry init` (writes `~/.config/agent-foundry/config.toml` + the first skill index).

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
ln -s "$PWD" ~/.claude/plugins/agent-foundry   # Claude Code plugin
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
python3 scripts/foundry-eval.py # quality gate: 32 passed, 0 failed
./scripts/validate.sh           # skill lint: 30 skills, 0 failed
```

## Uninstall

```bash
rm ~/.claude/plugins/agent-foundry   # remove the plugin symlink
rm -rf ~/.agent-foundry              # remove the repo
rm -rf ~/.config/agent-foundry       # remove config, venv, and logs
```

## Requirements

- Python 3.10+
- macOS or Linux (Windows not yet supported)
- An Anthropic or OpenAI API key (the daemon uses LiteLLM, so any supported model works)
