# Agent-Foundry

A skill orchestrator for Claude Code. Install once, get a curated set of 30+ skills dispatched against your prompts via a local daemon.

**This file documents v0.1** — the public launch baseline (Option C). For the design rationale, see [`docs/launch-plan.md`](docs/launch-plan.md).

## What this is

- A **Python package** (`agent-foundry`) that indexes your `SKILL.md` files and exposes:
  - `init`, `index`, `cost-report` — setup / maintenance
  - `plan "prompt"` — get a ranked list of relevant skills
  - `execute <skill_id> "prompt"` — run a specific skill
  - `run "prompt"` — plan + execute the top-ranked skill (with budget guard)
  - `serve` — run the daemon
- A **FastAPI daemon** with `/health`, `/index`, `/plan`, `/execute`, `/loop`
- A **thin Claude Code plugin** (`/plan`, `/af`) that forwards to the daemon
- A **fallback skill** (`generic-reasoning`) that runs when no skill matches your prompt
- An **interactive budget guard** — you'll be asked `y/n` before any run that exceeds your configured token budget (`--force` to skip)
- **SQLite logging** of every execution, including `planner_score` and `was_fallback` for later accuracy analysis

## v0.1 scope

**In scope:**
- Plan → execute → return (single pass)
- Configurable planner scoring weights (`config.toml`)
- Token budget confirmation flow
- Generic-reasoning fallback for unmatched prompts
- SQLite logging (`executions` table)

**Deferred to v0.2+:**
- Judge agent (output quality scoring)
- Retry loop (re-plan on failure)
- Knowledge graph store
- Auto-trigger via hooks
- PyPI publication
- SSE/WebSocket streaming
- systemd/launchd auto-start

## Quick start

### 1. Install

```bash
# Clone and install in editable mode
git clone https://github.com/youcisla/Agent-Foundry.git ~/.agent-foundry
cd ~/.agent-foundry
pip install -e .

# Or via the install script (Linux / macOS only)
curl -fsSL https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/install.sh | bash
```

The installer:
- Creates a venv at `~/.config/agent-foundry/venv`
- Runs `agent-foundry init` (writes `~/.config/agent-foundry/config.toml` + first index)
- Symlinks the repo to `~/.claude/plugins/agent-foundry`

### 2. Set your API key

```bash
export ANTHROPIC_API_KEY=sk-...
```

The daemon uses `litellm` and supports any model — Claude, GPT, etc.

### 3. Use the Claude Code plugin

In Claude Code:
```
/plan "write a react component"        # see which skills match
/af   "write a react component"        # plan + execute top skill
```

If the run would exceed your budget, you'll be asked `y/n` first. Pass `--force` (or use a setup that disables the prompt) to skip.

### 4. Or use the CLI directly

```bash
agent-foundry --help
agent-foundry plan "audit this code"
agent-foundry execute anti-slop "revise this README"
agent-foundry run  "refactor the API design"
agent-foundry serve --port 8765        # foreground; CLI commands start it lazily on first call
```

## Configuration

Config file: `~/.config/agent-foundry/config.toml`

```toml
[core]
skills_dir = "~/.claude/plugins/agent-foundry/skills"
index_path = "~/.config/agent-foundry/skills-index.json"
default_llm = "claude-3-7-sonnet-20250219"
token_budget = 100000
daemon_port = 8765
index_cache_ttl_seconds = 60
harness_type = "claude-code"

[planner]
pattern_match_weight = 0.3
name_in_prompt_boost = 0.2
cost_penalty_divisor = 5000.0
max_results = 5
```

Edit any field and re-run `agent-foundry init --force` to apply. The planner weights are tunable from `config.toml` without code changes.

## File layout

```
agent-foundry/                 # Python package
  __init__.py
  __main__.py                  # python -m agent_foundry
  cli.py                       # Click commands
  config.py                    # Config dataclasses + TOML load/save
  indexer.py                   # Walk skills/ + build SkillIndex
  models.py                    # Pydantic data models
  planner.py                   # Score + rank skills
  executor.py                  # LiteLLM call wrapper
  loop.py                      # plan → budget guard → execute
  daemon.py                    # FastAPI app
  logging_db.py                # SQLite exec logger
pyproject.toml                # Install via `pip install -e .`
install.sh                    # curl | bash installer
claude_code_plugin.json       # /plan + /af commands
docs/launch-plan.md           # v0.1 design spec
```

## Behavior notes

- **Lazy daemon start**: when you run `agent-foundry plan`, `execute`, or `run`, the CLI checks `/health`. If absent, it spawns `agent-foundry serve --detach` in the background and waits for it. The daemon stays alive between calls.
- **In-memory index cache**: the daemon caches `skills-index.json` for `index_cache_ttl_seconds` (default 60). Call `POST /index` to force a rebuild.
- **Trigger patterns**: extracted from each skill's `description` field's "Use when ..." clause. Patterns are exact regexes; **v0.1 does not fuzzy-match**. If a prompt doesn't trigger any pattern, the `generic-reasoning` fallback runs instead.
- **Budget guard**: the daemon returns `requires_confirmation=true` (instead of executing) when estimated cost exceeds `token_budget`. The CLI prompts `y/n` (skipped in non-TTY without `--force`). On `y`, the CLI re-sends with `force=true`. Zero tokens spent on a declined confirmation.

## Validation results

End-to-end checks performed during v0.1 development:

| Test | Result |
|------|--------|
| `init` writes config and indexes 30 skills + 1 fallback | ✅ |
| `cost-report` lists all skills with cost estimates | ✅ |
| `plan "kill generic AI slop in this essay"` → `anti-slop` | ✅ |
| `plan "xyz nonsense"` → empty (no match, fallback will run on `/loop`) | ✅ |
| `run --budget 50` over-budget → returns `requires_confirmation`, no execution | ✅ |
| `run` non-TTY input + over-budget → "declining without --force" | ✅ |
| Daemon `/health`, `/plan`, `/index`, `/loop` all return 200 | ✅ |
| Skill content indexed (31 entries with trigger patterns, location, costs) | ✅ |
| Logs written to `~/.config/agent-foundry/executions.db` | ✅ |
| Budget refusal does NOT log a real execution | ✅ |
| Fallback selection sets `was_fallback=1` in the log | ✅ |

## What's next

After using v0.1 for a week:

- Tune planner scoring weights (`config.toml`) based on observed success
- Review `~/.config/agent-foundry/executions.db` for accuracy signals
- File issues for v0.2 features (judge, retry loop, graph store)

## License

MIT. See `LICENSE`.
