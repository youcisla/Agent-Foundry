# Agent Foundry

<div align="center">
<br>

**A curated runtime orchestrator for AI coding assistants.**

Plan → execute → verify. Skills, agents, a local daemon, and a growing catalog — all MIT, all your data stays local.

</div>

## Quick start

```bash
curl -fsSL https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/install.sh | bash
export ANTHROPIC_API_KEY=sk-...
```

```bash
/af "build a react component"   # plan + execute in Claude Code
/plan "audit this API"          # see which skills match
```

Or without Claude Code:

```bash
agent-foundry plan "kill generic AI slop"
agent-foundry run  "refactor the API design"
```

## What it is

Agent Foundry is three things:

| Layer | What | File |
|---|---|---|
| **Skills** | Disciplines the model applies to its own work — how to *think*, not what to *know*. | `skills/core/<name>/SKILL.md` |
| **Agents** | Roles the orchestrator can dispatch — critic, planner, verifier. | `agents/af-*/AGENT.md` |
| **Orchestrator** | Local daemon that ranks, dispatches, executes, and logs every run. | `agent_foundry/` (Python) |

## The catalog

30 skills, 2 agents. All original work under MIT. Each skill:

- **≤150 lines / ≤8 KB** — Codex cap, no exceptions
- **Exactly one trigger phrase** — `Use when...` so the model knows when to fire
- **Anti-patterns + Verification checklist** — teach what *not* to do, then confirm it was done
- **Action verbs, not tool names** — `examine` not `Read`, `create` not `Write`

### Core skills (24)

| Skill | Trigger | Lines |
|---|---|---|
| `anti-slop` | Kill generic AI patterns before they ship | 36 |
| `api-design` | Design or review a new API endpoint | 57 |
| `automation-pick` | Decide whether to automate a task | 50 |
| `bottleneck-gating` | Phase a project by measured bottleneck | 46 |
| `constraint-then-solve` | Restate, catalog constraints, then solve | 46 |
| `context-optimization` | Keep tool outputs small, reference not repeat | 47 |
| `cron-troubleshoot` | Debug a missing or wrong cron job | 68 |
| `e2e-test-strategy` | Plan an E2E test pyramid | 69 |
| `feedback-loop` | After shipping, instrument → measure → iterate | 61 |
| `knowledge-extract` | Turn a session into a skill draft | 68 |
| `landscape-first` | Research competitors before building | 46 |
| `measure-first` | Measure before optimizing | 45 |
| `plan-before-code` | Spec before implementation | 46 |
| `plan-then-act` | Plan first, then act | 46 |
| `prompt-discipline` | Think, simplify, edit surgical, stay goal-driven | 52 |
| `pushback-when-wrong` | Push back against incorrect briefs | 47 |
| `quality-protocol` | Maximum-quality gate before declaring done | 60 |
| `read-before-build` | Read source files before writing code | 49 |
| `re-verify-findings` | Re-verify every claimed audit finding | 45 |
| `session-closeout` | Reconcile, update, hand off at session end | 67 |
| `session-distill` | Extract patterns from every session | 67 |
| `show-your-work` | Output a thinking trace after complex tasks | 44 |
| `verify-first` | Verify claims before committing to action | 47 |
| `workflow-decompose` | Decompose tasks into DAG steps | 62 |

### Optional skills (6)

| Skill | Trigger |
|---|---|
| `persistent-memory` | Persist context across sessions |
| `token-compression` | Compress tool outputs before they consume context |
| `chrome-devtools-mcp-bridge` | Drive Chrome DevTools from an agent |
| `design-language` | Apply Apple-grade UI polish |
| `funnel-pr-guard` | Guard conversion-critical paths from breaking |
| `sql-migration-trio` | Three-file migration pattern (up/down/schema) |

### Agents (2)

| Agent | Model | Job |
|---|---|---|
| `af-critic` | opus | Score output on correctness, slop, scope |
| `af-planner` | opus | Decompose a request into a skill/agent plan |

## Commands

| Command | What it does |
|---|---|
| `agent-foundry plan "..."` | Rank skills for a prompt |
| `agent-foundry run "..."` | Plan + execute the top-ranked skill |
| `agent-foundry execute <id> "..."` | Run a specific skill |
| `agent-foundry doctor` | Health-check config, index, daemon, API key |
| `agent-foundry status` | Routing accuracy, fallback rate, average cost |
| `agent-foundry consult "..."` | Recommend skills for a need |
| `agent-foundry cost-report` | Token and time estimates per skill |
| `agent-foundry index` | Rebuild the skill index |
| `agent-foundry serve` | Start the daemon (lazy-started on first command) |

## Architecture

```
/af <prompt>          /plan <prompt>
    │                      │
    ▼                      ▼
┌──────────────────────────────────┐
│       Agent Foundry daemon       │
│  FastAPI  · planner  · judge    │
│  executor  · budget guard       │
│  SQLite log  · indexer          │
└──────────────────┬───────────────┘
                   │
                   ▼
┌──────────────────────────────────┐
│  Skill catalog  +  Agent catalog │
│  references/  ·  scripts/  ·    │
│  hooks/  ·  executions.db       │
└──────────────────────────────────┘
```

The daemon is lazy-started by the CLI (no systemd/launchd requirement). Everything runs locally. Your data stays in `~/.config/agent-foundry/executions.db`.

## Install profiles

```bash
AF_PROFILE=minimal ./install.sh    # Skills only (no daemon)
AF_PROFILE=core    ./install.sh    # Skills + daemon (default)
AF_PROFILE=full    ./install.sh    # Skills + daemon + hooks
```

## Requirements

- Python 3.10+
- Claude Code, Codex, Gemini, Hermes, or OpenCode (any harness that accepts slash commands)
- An Anthropic or OpenAI API key

## Quality gates

Every commit runs:

```bash
# 32 assets pass static quality checks
python scripts/foundry-eval.py

# All skills have correct frontmatter
./scripts/validate.sh

# No external-reference names in tracked files
bash scripts/nox.sh
```

Current: **32 passed, 0 failed** | **30 skills, 0 failed** | **0 external references**

## License

MIT. All skills, agents, and authored artifacts are original work by the Agent Foundry Contributors.

## Related

- [ECC](https://github.com/affaan-m/ECC) — The agent harness optimization system that inspired this project's approach to skill curation and selective install
- [AGENTS.md](https://agents.md/) — The open cross-harness context-file convention
- [wshobson/agents](https://github.com/wshobson/agents) — Reference marketplace for multi-harness agent deployment

## Status

Public v0.1 — active development. [docs/launch-plan.md](docs/launch-plan.md) for the original spec, [docs/improvement-plan.md](docs/improvement-plan.md) for the roadmap.
