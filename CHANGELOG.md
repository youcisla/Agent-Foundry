# Changelog

All notable changes to Agent Foundry. Everything here is original work by the Agent Foundry contributors, released under MIT.

## 0.2.0-pre — 2026-07-20 (in development)

Structure to support agents, quality evaluation, and multiple harnesses. Tracked in `docs/launch-plan.md`.

**Added**

- **`agents/`** — the agent layer (roles the orchestrator can dispatch), distinct from skills (disciplines the model applies):
  - `af-planner` — decomposes a request into an ordered plan naming skills/agents. Returns JSON.
  - `af-critic` — the judge. Scores a completed output on correctness, slop, and scope. Returns JSON.
- **`agent_foundry/judge.py`** + `--judge` flag on `run` + `LoopRequest.judge` / `LoopResponse.judge_score` + judge columns in the SQLite `executions` table.
- **`scripts/foundry-eval.py`** — static quality gate (trigger phrase, body size, tool-vocabulary/action-verb check, anti-patterns section, verification checklist, `references/` split, agent-name uniqueness). Replaces `validate.sh` as the CI gate.
- **`docs/architecture.md`** — the skill-vs-agent taxonomy.
- **`docs/authoring.md`** — portability rules: action verbs over tool names, ≤8 KB / ≤150 lines, exactly one `Use when…` trigger, plugin-scoped agent names.
- **`hooks/session-end.sh`** — real distillation via the daemon when reachable; fillable placeholder otherwise.
- **`.gitattributes`** — enforces LF line endings so shell scripts run under `curl | bash` on macOS/Linux.

**Changed**

- Every skill now carries a single `author: Agent Foundry Contributors` field. Original-authorship attestation lives in `AUTHORSHIP.md`; the skill manifest schema requires `author`.
- Normalized all shell/Python line endings to LF (shell scripts were silently broken on Linux).
- Author strings unified across the catalog.

**Also added this cycle**

- Lifecycle CLI: `agent-foundry doctor` (health-check config/index/daemon/API key), `status` (routing accuracy, fallback rate, average cost), `consult` (recommend skills for a need).
- Selective install profiles: `AF_PROFILE=minimal|core|full ./install.sh`.

**Not yet implemented (planned)**

- Multi-harness adapter framework (Codex, Gemini, OpenCode, …).
- New discipline skills (`spec-first`, `dependency-diet`, …).

---

## 0.1.0 — 2026-07-20

**Public launch — Option C (plan → execute → return).**

A working Python package that orchestrates 30 skills via a FastAPI daemon. A thin Claude Code plugin (`claude_code_plugin.json`) exposes `/plan` and `/af` slash commands that POST to the daemon.

**Package** (`agent-foundry`, `pip install -e .`):

- CLI: `init`, `index`, `cost-report`, `plan`, `execute`, `run`, `serve` (Click).
- `~/.config/agent-foundry/config.toml` with `[core]` + `[planner]` sections; scoring weights tunable without code edits.
- Pydantic data models; LiteLLM as the unified client (any model). Pure-Python YAML frontmatter parser (no PyYAML dependency).

**Daemon** — `/health`, `/index`, `/plan`, `/execute`, `/loop`:

- Lazy-started by the CLI (no systemd/launchd).
- In-memory index cache with configurable TTL (default 60s).
- Token-budget guard returns `requires_confirmation` → CLI prompts `y/n` → re-sends with `force=true`. Zero tokens spent on a decline.
- Virtual `generic-reasoning` fallback skill runs when nothing matches (configurable system prompt).

**Logging** — SQLite at `~/.config/agent-foundry/executions.db` with `planner_score` and `was_fallback` columns for accuracy analysis.

**Skill catalog — 30 skills (all original disciplines).**

24 core (`skills/core/`): `prompt-discipline`, `context-optimization`, `anti-slop`, `plan-before-code`, `plan-then-act`, `constraint-then-solve`, `quality-protocol`, `verify-first`, `re-verify-findings`, `measure-first`, `bottleneck-gating`, `pushback-when-wrong`, `read-before-build`, `show-your-work`, `landscape-first`, `session-closeout`, `session-distill`, `knowledge-extract`, `api-design`, `cron-troubleshoot`, `e2e-test-strategy`, `feedback-loop`, `workflow-decompose`, `automation-pick`.

6 optional (`skills/optional/`): `design-language`, `chrome-devtools-mcp-bridge`, `persistent-memory`, `token-compression`, `funnel-pr-guard`, `sql-migration-trio`.

**Workflow runbooks (4 in `workflows/`)** — copy-and-adapt guides, not auto-triggering skills: `ci-cd-vercel`, `e2e-on-pr`, `release-train`, `session-to-skill`.

**Hooks / scripts** — `session-closeout.sh`, `session-end.sh`; `install.sh`, `validate.sh`.
