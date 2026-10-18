<!-- mcp-name: io.github.youcisla/agent-foundry -->
<div align="center">

# Agent Foundry

**Skill and agent runtime for AI coding assistants.**

Plan → execute → verify. Skills, agents, a local daemon.
MIT, local, no cloud. 35 original skills, no third-party skill content.

<br>

[![MIT License](https://img.shields.io/badge/License-MIT-f5a623.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.5.0-4ade80.svg)](CHANGELOG.md)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-6496ff.svg)](https://www.python.org)
[![npm](https://img.shields.io/badge/npm-%40youcisla%2Fagent--foundry-6496ff.svg)](https://www.npmjs.com/package/@youcisla/agent-foundry)
[![Skills](https://img.shields.io/badge/skills-35-f5a623.svg)](#catalog)
[![Agents](https://img.shields.io/badge/agents-3-4ade80.svg)](#catalog)
[![Gates](https://img.shields.io/badge/quality%20gates-3%20green-4ade80.svg)](#quality-gates)
[![External refs](https://img.shields.io/badge/external%20refs-0-4ade80.svg)](https://github.com/youcisla/Agent-Foundry/blob/main/scripts/nox.sh)
[![Web](https://img.shields.io/badge/live%20demo-youcisla--agents.vercel.app-f5a623)](https://youcisla-agents.vercel.app)

<br>

[**Quick start**](#quick-start) · [**Catalog**](#catalog) · [**Architecture**](#architecture) · [**Commands**](#commands) · [**Web app**](https://youcisla-agents.vercel.app)

</div>

---

## Why Agent Foundry

> Models hallucinate. They over-comment. They reach for `npm install` when
> you asked for a one-line fix. Agent Foundry steers the model back to the
> actual work.

Three layers:

| Layer | What | Lives in |
|---|---|---|
| **🧠 Skills** | Disciplines the model applies (how to think, not what to know) | `skills/core/<name>/SKILL.md` |
| **🤖 Agents** | Roles the orchestrator can dispatch (critic, planner, orchestrator) | `agents/af-*/AGENT.md` |
| **⚙️ Orchestrator** | Local daemon that ranks, dispatches, executes, logs, judges | `agent_foundry/` (Python) |

Each layer is portable. A skill body is a plain markdown file with a trigger
phrase. An agent is a role definition. The orchestrator is a Python package
you can `pip install` or run from source.

---

## Quick start

### 1. Install

macOS / Linux / Git Bash:

```bash
curl -fsSL https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/install.sh | bash
```

Windows (PowerShell):

```powershell
irm https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/scripts/install.ps1 | iex
```

Or from npm (cross-platform, Node 18+):

```bash
npm install -g @youcisla/agent-foundry
agent-foundry            # auto-detect harness and install
```

Or from PyPI (Python 3.10+, includes the MCP runtime):

```bash
pip install agent-foundry-runtime
agent-foundry doctor
uvx agent-foundry-runtime mcp   # MCP stdio server, no install needed
```

Registry name: `io.github.youcisla/agent-foundry`.

Every harness gets each skill as a direct child of its real discovery root.
See [docs/harness-compatibility.md](docs/harness-compatibility.md) for the
path matrix and the dos/don'ts.

Then set an API key:

```bash
export ANTHROPIC_API_KEY=sk-...   # or OPENAI_API_KEY
```

### 2. Use it

In Claude Code (or any harness that accepts slash commands):

```bash
/af "build a react component"      # plan + execute
/plan "audit this API"             # see which skills match
```

Without a harness:

```bash
agent-foundry plan  "kill generic AI slop"
agent-foundry run   "refactor the API design"
agent-foundry doctor
```

### 3. Or browse first

→ **[youcisla-agents.vercel.app](https://youcisla-agents.vercel.app)** has the
full catalog, an interactive knowledge graph, and one-click install.

### 4. Or connect over MCP

```bash
agent-foundry mcp   # stdio MCP server: plan, execute, list_skills, get_skill
```

Or run the published package directly:

```bash
uvx agent-foundry-runtime mcp
```

Registered name: `io.github.youcisla/agent-foundry`.

### 5. Measure a skill instead of trusting it

```bash
agent-foundry eval --tasks tasks.json
```

Each task runs twice, with and without the skill, and reports the pass-rate
lift. Task format: `{"id", "prompt", "skill", "verify"}` where `verify` is a
shell command that receives the output on stdin. The layout matches
SkillsBench v1.1 (`benchflow/skillsbench`), so published benchmarks can be
reused.

---

## Architecture

```text
Your prompt  (/af build a react component)
   └─▶ Agent Foundry daemon
         └─▶ planner · rank_skills
               └─▶ executor · LiteLLM  ⇄  LLM provider (Claude, OpenAI, …)
                     └─▶ SQLite · executions.db
                           └─▶ Response to user
```

Published through three channels: npm (`@youcisla/agent-foundry`), PyPI
(`agent-foundry-runtime`), and the official MCP registry
(`io.github.youcisla/agent-foundry`).

> Interactive versions of every diagram live on the site:
> **[/architecture](https://youcisla-agents.vercel.app/architecture)**,
> **[/graph](https://youcisla-agents.vercel.app/graph)** (knowledge graph +
> orchestration), and **[/audit](https://youcisla-agents.vercel.app/audit)**.

### What's in the box

```text
skills/         35 disciplines (25 core + 10 optional)    ─┐ feed
agents/         af-planner · af-critic · af-orchestrator  │ the
                                                          ▼ indexer
agent_foundry/  config.py ─▶ daemon.py (FastAPI) ─▶ mcp_server.py (stdio MCP)
                indexer.py ─▶ planner.py ─▶ loop.py  ⇄  executor.py
                loop.py ─▶ judge.py (af-critic) ─▶ logging_db.py
scripts/        install.js ─▶ 14 harness skill roots + CLI index
```

The daemon is lazy-started by the CLI, so there is no systemd/launchd requirement.
Everything runs locally. Your data stays in `~/.config/agent-foundry/executions.db`.

### The loop, end to end

```text
 1.  user      → run_loop   : /af "kill generic AI slop"
 2.  run_loop  → planner    : rank_skills(prompt, index)
 3.  planner   → run_loop   : top match (e.g. anti-slop, 0.24)
 4.  run_loop  → run_loop   : budget guard
 5.  run_loop  → executor   : build_messages(prompt, body)
 6.  executor  → LiteLLM    : POST /v1/messages
 7.  LiteLLM   → executor   : response text
 8.  executor  → run_loop   : response + cost
 9.  (judge=true) run_loop → af-critic : score → {corr, slop, scope, verdict}
10.  run_loop  → SQLite     : log_execution(...)
11.  run_loop  → user       : LoopResponse {output, plan, judge_score?}
```

---

## Catalog

**35 skills, 3 agents.** All original work under MIT. Each skill:

- 📏 **≤150 lines / ≤8 KB** (Codex cap, no exceptions)
- 🎯 **Exactly one trigger phrase** (`Use when...` so the model knows when to fire)
- 🚫 **Anti-patterns + Verification checklist** (teach what *not* to do, then confirm it was done)
- ⚡ **Action verbs, not tool names** (`examine` not `Read`, `create` not `Write`)

### Core skills (25)

| Skill | Trigger |
|---|---|
| [`anti-slop`](skills/core/anti-slop/SKILL.md) | Kill generic AI patterns before they ship |
| [`api-design`](skills/core/api-design/SKILL.md) | Use when creating a new API endpoint or reviewing API consistency |
| [`automation-pick`](skills/core/automation-pick/SKILL.md) | Decide whether to automate a task before automating |
| [`bottleneck-gating`](skills/core/bottleneck-gating/SKILL.md) | Phase a project by measured bottleneck, not intuition |
| [`constraint-then-solve`](skills/core/constraint-then-solve/SKILL.md) | Restate the problem, catalog constraints, then solve |
| [`context-optimization`](skills/core/context-optimization/SKILL.md) | Use on any task with >2K-token outputs, big files, or repeated reads |
| [`cron-troubleshoot`](skills/core/cron-troubleshoot/SKILL.md) | Debug a missing or wrong cron job |
| [`e2e-test-strategy`](skills/core/e2e-test-strategy/SKILL.md) | Use when designing test coverage for a web app or API |
| [`engram-routing`](skills/core/engram-routing/SKILL.md) | Route prompts via O(1) N-gram lookup when trigger patterns should match fast |
| [`feedback-loop`](skills/core/feedback-loop/SKILL.md) | After shipping, instrument → measure → iterate |
| [`knowledge-extract`](skills/core/knowledge-extract/SKILL.md) | Turn a session into a skill draft |
| [`landscape-first`](skills/core/landscape-first/SKILL.md) | Research the space before building |
| [`measure-first`](skills/core/measure-first/SKILL.md) | Use when about to optimize, refactor, or claim a system is slow |
| [`plan-before-code`](skills/core/plan-before-code/SKILL.md) | Use before writing any non-trivial code change |
| [`plan-then-act`](skills/core/plan-then-act/SKILL.md) | Use when a task has multiple steps and the order matters |
| [`prompt-discipline`](skills/core/prompt-discipline/SKILL.md) | Use on every non-trivial task: think, simplify, edit surgical, stay goal-driven |
| [`pushback-when-wrong`](skills/core/pushback-when-wrong/SKILL.md) | Use when reviewing an assertion that smells off |
| [`quality-protocol`](skills/core/quality-protocol/SKILL.md) | Use before declaring a task complete |
| [`re-verify-findings`](skills/core/re-verify-findings/SKILL.md) | Use after any prior verification claimed a finding |
| [`read-before-build`](skills/core/read-before-build/SKILL.md) | Read source files before writing code |
| [`session-closeout`](skills/core/session-closeout/SKILL.md) | Apply at the end of any multi-step project |
| [`session-distill`](skills/core/session-distill/SKILL.md) | Extract patterns from every session |
| [`show-your-work`](skills/core/show-your-work/SKILL.md) | Output a thinking trace after complex tasks |
| [`verify-first`](skills/core/verify-first/SKILL.md) | Apply before committing to any claim |
| [`workflow-decompose`](skills/core/workflow-decompose/SKILL.md) | Use when designing or debugging an automation |

### Optional skills (10)

| Skill | Trigger |
|---|---|
| [`persistent-memory`](skills/optional/persistent-memory/SKILL.md) | Use when persisting context across sessions or threading memory across agents |
| [`token-compression`](skills/optional/token-compression/SKILL.md) | Compress tool outputs before they consume context |
| [`chrome-devtools-mcp-bridge`](skills/optional/chrome-devtools-mcp-bridge/SKILL.md) | Drive Chrome DevTools from an agent |
| [`design-language`](skills/optional/design-language/SKILL.md) | Apply Apple-grade UI polish |
| [`funnel-pr-guard`](skills/optional/funnel-pr-guard/SKILL.md) | Guard conversion-critical paths from breaking |
| [`sql-migration-trio`](skills/optional/sql-migration-trio/SKILL.md) | Three-file migration pattern (up/down/schema) |
| [`agent-memory-vault`](skills/optional/agent-memory-vault/SKILL.md) | Shared structured memory that survives agent sessions |
| [`agent-team-standards`](skills/optional/agent-team-standards/SKILL.md) | Per-project locked agent skill set with version pins |
| [`autonomous-briefing`](skills/optional/autonomous-briefing/SKILL.md) | Run a fully autonomous morning briefing |
| [`book-to-skill`](skills/optional/book-to-skill/SKILL.md) | Convert book chapters or long articles into a runnable skill |

### Agents (3)

| Agent | Model | Job |
|---|---|---|
| [`af-critic`](agents/af-critic/AGENT.md) | `opus` | Score output on correctness, slop, scope. Returns JSON. |
| [`af-planner`](agents/af-planner/AGENT.md) | `opus` | Decompose a request into a skill/agent plan. Returns JSON. |
| [`af-orchestrator`](agents/af-orchestrator/AGENT.md) | `opus` | Dispatch subtasks to specialized agents and skills, then merge results. |

---

## Commands

| Command | What it does |
|---|---|
| `agent-foundry init [--force]` | Write config and the first skill index |
| `agent-foundry index` | Rebuild the skill index from disk |
| `agent-foundry plan "<prompt>"` | Rank skills for a prompt |
| `agent-foundry run "<prompt>"` | Plan + execute the top-ranked skill |
| `agent-foundry resume <session_id> "<prompt>"` | Continue a loop session with a follow-up |
| `agent-foundry session <session_id>` | Inspect a stored loop session |
| `agent-foundry execute <skill_id> "<prompt>"` | Run a specific skill |
| `agent-foundry doctor` | Health-check: config, index, daemon, API key |
| `agent-foundry status` | Routing accuracy, fallback rate, average cost |
| `agent-foundry consult "<need>"` | Recommend skills for a need |
| `agent-foundry cost-report` | Token and time estimates per skill |
| `agent-foundry feedback <id> <score>` | Attach a human score to an execution |
| `agent-foundry learn` | Learn trigger weights from judged executions |
| `agent-foundry instincts` | List proposed trigger instincts |
| `agent-foundry instinct-approve <id>` | Approve an instinct and persist it |
| `agent-foundry browse` | Browse/search the catalog, or `--read <id>` |
| `agent-foundry mcp` | Start the MCP stdio server (plan/execute/list_skills/get_skill) |
| `agent-foundry eval --tasks <file>` | Paired skill eval: with vs without, reports lift |
| `agent-foundry serve` | Start the daemon (lazy-started on first command) |

Every command also has an HTTP endpoint on the daemon for programmatic use:
`/health`, `/site-data`, `/events`, `/index`, `/plan`, `/engram`, `/execute`,
`/loop`, `/loop/resume`, `/loop/{id}`, `/stats`, `/feedback`, `/learn`,
`/instincts`, and `/instincts/{id}/approve`.

---

## Install profiles

The shell installer takes a profile:

```bash
AF_PROFILE=minimal ./install.sh    # Skills only (no daemon)
AF_PROFILE=core    ./install.sh    # Skills + daemon (default)
AF_PROFILE=full    ./install.sh    # Skills + daemon + hooks
```

Run from source (any OS):

```bash
git clone https://github.com/youcisla/Agent-Foundry.git ~/.agent-foundry
cd ~/.agent-foundry && pip install -e .
```

See [INSTALL.md](INSTALL.md) for the full matrix of harnesses, profiles, and platforms.

---

## Requirements

- **Python 3.10+** (for the daemon) or **Node 18+** (for the cross-platform installer)
- macOS, Linux, or Windows
- A supported harness: Claude Code, Codex, Cursor, Gemini/Antigravity, OpenCode, Hermes, Zed, or any of the 14 adapters
- An API key (Anthropic, OpenAI, or any provider LiteLLM supports)
- ~50 MB disk for the catalog and generated index

---

## Quality gates

Every commit runs three gates. **All green right now.**

```bash
# 34 assets pass static quality checks (trigger phrase, body size, anti-patterns)
python scripts/foundry-eval.py

# All skills have correct frontmatter (name, description, version, author)
./scripts/validate.sh

# No external-reference names in tracked files (provenance gate)
bash scripts/nox.sh
```

**Current:**

| Gate | Result |
|---|---|
| `foundry-eval.py` | **34 passed, 0 failed** ✅ |
| `validate.sh` | **35 skills, 0 failed** ✅ |
| `nox.sh` | **0 external references** ✅ |

The `nox.sh` gate is the strongest guarantee: it scans every tracked file for
project-handle names so that the catalog stays original work.

---

## Web app

Browse the catalog, the knowledge graph, and the audit at
**[youcisla-agents.vercel.app](https://youcisla-agents.vercel.app)**:

| Page | What |
|---|---|
| [Catalog](https://youcisla-agents.vercel.app/catalog) | All 35 skills + 3 agents with live search |
| [Graph](https://youcisla-agents.vercel.app/graph) | Interactive React Flow knowledge graph (766 nodes, 1,394 edges, 75 communities) |
| [Audit](https://youcisla-agents.vercel.app/audit) | God nodes, surprising connections, interactive React Flow diagrams |

The site regenerates from live repo state on every commit via
`scripts/gen-site-data.py` → Vercel build → deploy.

---

## Roadmap

| Status | Item |
|---|---|
| ✅ v0.1 | Python package + FastAPI daemon + Claude Code plugin |
| ✅ v0.2 | Foundational audit, frozen Config, multi-page web app, knowledge graph, interactive React Flow diagrams |
| ✅ v0.3 | npm package, Engram O(1) routing, af-orchestrator agent, harness adapters |
| ✅ v0.4 | PyPI + MCP registry, loop sessions, deterministic site data, per-skill adapter installs |
| 📋 next | `af verify` signed-manifest integrity |

See [docs/launch-plan.md](docs/launch-plan.md) for the full design spec.

---

## License

**MIT.** All skills, agents, and authored artifacts are original work by
the Agent Foundry Contributors. See [AUTHORSHIP.md](AUTHORSHIP.md) for
the attribution policy.

---

<div align="center">

Built by [Youcisla](https://github.com/youcisla) ·
[Contribute](CONTRIBUTING.md) ·
[Report an issue](https://github.com/youcisla/Agent-Foundry/issues)

</div>