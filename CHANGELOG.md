# Changelog

All notable changes to Agent Foundry. Everything here is original work by the Agent Foundry contributors, released under MIT.

## 0.5.0 - 2026-10-18

UI, distribution, and architecture release.

- Site refresh: all 14 harness adapters marked tested, current graph counts
  (766 nodes, 1,394 edges, 75 communities), a full 19-command surface, and
  npm / PyPI / MCP install tabs.
- New interactive architecture page (`/architecture`) generated with Archify:
  distribution channels, local runtime, skill/agent/graph data, and SQLite.
- PyPI documented everywhere: `pip install agent-foundry-runtime` and
  `uvx agent-foundry-runtime mcp`.
- Graph regenerated from the current repository; god-node and architecture
  diagrams updated to the new degrees and distribution nodes.
- Adapter status is uniform: every target passes the installer + indexer smoke
  test; Claude Code, Hermes, and OpenClaw are live-verified.

## 0.4.3 - 2026-10-18

Harness portability release.

- The installer now links each of the 35 skills as a direct child of the
  harness's documented skills root. The previous nested
  `skills/agent-foundry/core/...` layout was invisible to Claude Code and most
  other harnesses.
- Corrected roots: Codex `~/.agents/skills`, Cursor `~/.cursor/skills`, Gemini
  `~/.gemini/skills` plus a real `gemini-extension.json`, Antigravity App/IDE and
  CLI roots, Kimi `~/.kimi-code/skills`, Hermes `~/.hermes/skills`, Zed
  `~/.agents/skills`, CodeBuddy/JoyCode/Qwen/OpenClaw per-skill installs.
- The installer records managed skills in `.agent-foundry-installed.json`; it
  refreshes only its own entries, removes stale ones, and never deletes
  user-authored skills. `--copy` selects a portable copy instead of links.
- Windows uses directory junctions, so linking no longer needs admin rights.
- `agent_foundry/config.py` now defaults `skills_dir` to the dedicated
  `~/.config/agent-foundry/skills` index root, so CLI routing does not rank
  third-party harness skills.
- Claude plugin manifest declares `./skills/core` and `./skills/optional`.
- Added `docs/harness-compatibility.md` with the path matrix and dos/don'ts,
  root `AGENTS.md` as the canonical cross-tool instruction file, and
  `scripts/test-install.js` to verify every target in CI.

## 0.4.2 - 2026-10-17

Packaging release for PyPI and the MCP registry.

- PyPI distribution is `agent-foundry-runtime` (the name `agent-foundry` is blocked by PyPI's similarity rule). Adds an `agent-foundry-runtime` console-script alias so `uvx agent-foundry-runtime mcp` works.
- MCP `serverInfo.version` and the FastAPI version now derive from `agent_foundry.__version__`; `sync-version.py` keeps it aligned.
- `server.json` updated for `agent-foundry-runtime`; registry listing `io.github.youcisla/agent-foundry@0.4.2`.

## 0.4.0 - 2026-10-17

The evidence and distribution release. Fixes a catalog bug that silently dropped four skills and a planner bug that broke `plan()` outright, adds an MCP server, learned routing weights, reliable execution, paired evaluation, and a session-start bootstrap.

**Added**

- `agent-foundry mcp`: MCP stdio server exposing `plan`, `execute`, `list_skills`, and `get_skill`. No new dependencies.
- `agent-foundry resume <session_id> "<prompt>"` and `agent-foundry session <id>`: multi-turn loop sessions, persisted in SQLite; daemon routes `POST /loop/resume` and `GET /loop/{id}`.
- `agent-foundry browse`: terminal catalog browser with `--search` and `--read`.
- `agent-foundry eval`: paired evaluation (same task with and without a skill) with a deterministic verifier and skill-lift reporting.
- SessionStart bootstrap hook (`hooks/hooks.json`, `hooks/session-start.sh`) injecting a ~733-token skill index, opt-out via `AGENT_FOUNDRY_NO_BOOTSTRAP=1`.
- Codex and Cursor plugin manifests alongside the Claude Code manifest.
- `mcpName` in `package.json` and `server.json` for official MCP registry publication; `scripts/publish-mcp.sh` validates versions and publishes.
- CI workflow: version drift check, generated-artifact check, unit tests.
- `scripts/sync-version.py`, `scripts/gen-site-data.py`, `scripts/gen-skill-index.py`.

**Changed**

- Planner: keyword-overlap fallback when triggers miss, learned skill weights from judge scores, two-hop graph boost, cached graph adjacency, optional semantic fallback (`[semantic]` extra), optional LLM rerank of the top candidates (`planner.rerank_enabled`).
- Graph path input is restricted to JSON files inside the repo or working directory.
- Executor: timeout, max-token cap, retries, cost reporting, full output stored in the log DB (display truncation only), skill integrity verification via SHA-256.
- Loop uses the shared completion path instead of duplicating LiteLLM logic.
- Version is now 0.4.0 across every manifest; `sync-version.py --check` enforces it.

**Fixed**

- Inline YAML lists (`tags: [a, b]`) were parsed as strings, silently dropping four optional skills from the index. The catalog now indexes all 35.
- `PlanRequest` lacked `graph_path`, so `plan()` and the `/plan` endpoint raised `AttributeError`.
- Trigger derivation produced malformed regexes containing quote characters and literal `\s`, so most prompts matched nothing.
- `agent-foundry status` referenced a nonexistent `cfg.log_path`.
- Hosted site no longer opens an SSE connection to `127.0.0.1:8765` (the production console `ERR_CONNECTION_REFUSED`).
- Site counts (skills, agents, CLI commands, endpoints, graph nodes/edges/communities) now match generated data; testimonials with no source were removed.
- Accessibility: contrast tokens raised to WCAG AA, `<main>` landmark added, inline links underlined.
- Graph page header statistics now populate instead of showing placeholders; initial view fits hub nodes so labels are readable.


## 0.3.2 - 2026-07-21

Maintenance release after the npm packaging cycle.

**Changed**

- Moved the npm-publish skills under `docs/` so they stay private and are not shipped to the npm tarball.
- Reconciled version strings across `pyproject.toml`, `package.json`, and the README badge (all now read 0.3.2).
- Humanizer pass on docs and manifests: removed em-dash usage and other AI-writing patterns from README, INSTALL, CHANGELOG, and `pyproject.toml`.

## 0.3.1 - 2026-07-21

Patch release for the npm install path.

**Fixed**

- Install tabs on the web app threw `ReferenceError: counts is not defined` (a scope bug in the adapter-strip renderer). The stat counters and adapter strip are now fully driven by the live `AFStore` feed.
- Hero stats and adapter strip no longer carry stale hardcoded values.

## 0.3.0 - 2026-07-20

The routing and packaging release. Adds O(1) prompt routing, a third agent, a published npm package, and cross-platform install.

**Added**

- **`engram-routing`** skill: Engram-style conditional memory. N-gram keyed lookup table gives O(1) prompt matching instead of a linear scan over the skill index. Backed by SQLite, so hot prompts plan and execute in microseconds once the pattern is recognized. Adopted from the DeepSeek Engram pattern.
- **`af-orchestrator`** agent: dispatches subtasks to specialized agents and skills, then merges the results. Joins `af-planner` and `af-critic` as the third agent role.
- **npm package** `@youcisla/agent-foundry`. Published with a cross-platform `scripts/install.js` Node entry point (Node 18+, zero runtime dependencies). Thin `.sh` / `.bat` / `.ps1` wrappers delegate to it.
- **Cross-platform install**: Windows support via `install.ps1` and `install.bat`, both routing through `install.js`. Symlink, then hard-link, then recursive copy fallback chain (the ECC pattern).
- **13 harness adapters** in `install.js`: Claude Code, Codex, Hermes (tested end-to-end), plus Cursor, Gemini CLI, OpenCode, Antigravity, Codebuddy, JoyCode, Qwen, Kimi, OpenClaw, Zed (beta or coming-soon). Each has a `--harness=NAME` install path and a `--list` discovery command.
- GitHub Action for npm publish automation on tag push.

**Changed**

- Renamed the npm package to `@youcisla/agent-foundry` after an npm name conflict on the unscoped handle.
- `.npmignore` and `package.json` `files[]` now exclude `__pycache__` and `.pyc` from the tarball.
- Vercel `installCommand` skips npm install (this repo has no npm runtime dependencies).

**Fixed**

- Claude Code venv activation error on Windows caused by PowerShell execution policy.

---

## 0.2.0 - 2026-07-20

Structure to support agents, quality evaluation, and multiple harnesses. Tracked in `docs/launch-plan.md`.

**Added**

- **`agents/`**: the agent layer (roles the orchestrator can dispatch), distinct from skills (disciplines the model applies):
  - `af-planner` decomposes a request into an ordered plan naming skills/agents. Returns JSON.
  - `af-critic` is the judge. Scores a completed output on correctness, slop, and scope. Returns JSON.
- **`agent_foundry/judge.py`** plus the `--judge` flag on `run`, `LoopRequest.judge` / `LoopResponse.judge_score`, and judge columns in the SQLite `executions` table.
- **`scripts/foundry-eval.py`**: the static quality gate (trigger phrase, body size, tool-vocabulary/action-verb check, anti-patterns section, verification checklist, `references/` split, agent-name uniqueness). Replaces `validate.sh` as the CI gate.
- **`docs/architecture.md`**: the skill-vs-agent taxonomy.
- **`docs/authoring.md`**: portability rules (action verbs over tool names, 8 KB / 150 lines max, exactly one `Use when...` trigger, plugin-scoped agent names).
- **`hooks/session-end.sh`**: real distillation via the daemon when reachable, fillable placeholder otherwise.
- **`.gitattributes`**: enforces LF line endings so shell scripts run under `curl | bash` on macOS/Linux.

**Changed**

- Every skill now carries a single `author: Agent Foundry Contributors` field. Original-authorship attestation lives in `AUTHORSHIP.md`; the skill manifest schema requires `author`.
- Normalized all shell/Python line endings to LF (shell scripts were silently broken on Linux).
- Author strings unified across the catalog.

**Also added this cycle**

- Lifecycle CLI: `agent-foundry doctor` (health-check config/index/daemon/API key), `status` (routing accuracy, fallback rate, average cost), `consult` (recommend skills for a need).
- Selective install profiles: `AF_PROFILE=minimal|core|full ./install.sh`.

**Not yet implemented (planned)**

- Multi-harness adapter framework (Codex, Gemini, OpenCode, ...). Shipped in 0.3.0.

---

## 0.1.0 - 2026-07-20

Public launch (Option C: plan, execute, return).

A working Python package that orchestrates 30 skills via a FastAPI daemon. A thin Claude Code plugin (`claude_code_plugin.json`) exposes `/plan` and `/af` slash commands that POST to the daemon.

**Package** (`agent-foundry`, `pip install -e .`):

- CLI: `init`, `index`, `cost-report`, `plan`, `execute`, `run`, `serve` (Click).
- `~/.config/agent-foundry/config.toml` with `[core]` and `[planner]` sections. Scoring weights are tunable without code edits.
- Pydantic data models. LiteLLM as the unified client (any model). Pure-Python YAML frontmatter parser (no PyYAML dependency).

**Daemon**: `/health`, `/index`, `/plan`, `/execute`, `/loop`:

- Lazy-started by the CLI (no systemd, no launchd).
- In-memory index cache with configurable TTL (default 60s).
- Token-budget guard returns `requires_confirmation`, the CLI prompts `y/n`, then re-sends with `force=true`. Zero tokens spent on a decline.
- Virtual `generic-reasoning` fallback skill runs when nothing matches (configurable system prompt).

**Logging**: SQLite at `~/.config/agent-foundry/executions.db` with `planner_score` and `was_fallback` columns for accuracy analysis.

**Skill catalog: 30 skills (all original disciplines).**

24 core (`skills/core/`): `prompt-discipline`, `context-optimization`, `anti-slop`, `plan-before-code`, `plan-then-act`, `constraint-then-solve`, `quality-protocol`, `verify-first`, `re-verify-findings`, `measure-first`, `bottleneck-gating`, `pushback-when-wrong`, `read-before-build`, `show-your-work`, `landscape-first`, `session-closeout`, `session-distill`, `knowledge-extract`, `api-design`, `cron-troubleshoot`, `e2e-test-strategy`, `feedback-loop`, `workflow-decompose`, `automation-pick`.

6 optional (`skills/optional/`): `design-language`, `chrome-devtools-mcp-bridge`, `persistent-memory`, `token-compression`, `funnel-pr-guard`, `sql-migration-trio`.

**Workflow runbooks (4 in `workflows/`)**: copy-and-adapt guides, not auto-triggering skills: `ci-cd-vercel`, `e2e-on-pr`, `release-train`, `session-to-skill`.

**Hooks / scripts**: `session-closeout.sh`, `session-end.sh`; `install.sh`, `validate.sh`.
