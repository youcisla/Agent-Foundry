# Agent Foundry – Public Launch Plan (Option C)

> Spec-only document. No executable code. Use as input to the implementation harness.
> Last updated: 2026-07-20. Scope: v0.1 public launch.

---

## 1. Project Context

Agent Foundry is a skill orchestrator for Claude Code. The current state is a curated folder of 30+ `SKILL.md` files with frontmatter metadata (name, description, trigger patterns, cost estimates). The goal is to turn this knowledge base into a working plugin that:

- Runs as a local daemon (HTTP API).
- Integrates with Claude Code via a thin plugin that registers `/plan` and `/af` commands.
- Allows a user to ask for a plan (ranked skill recommendations) or execute a full "plan + run the best skill" loop.
- Is installed with a one-line `curl | bash` script.

## 2. Scope for v0.1 (Option C)

We are shipping a working orchestrator that does **plan → execute the top-ranked skill → return the result**. No judge, no retry loop, no graph, no auto-trigger, no SSE streaming, no PyPI publication, no system-level auto-start.

**What v0.1 includes:**

- A Python package with CLI commands: `init`, `index`, `cost-report`, `plan` (CLI), `execute` (CLI), `serve` (daemon), `run` (CLI loop).
- A FastAPI daemon with endpoints: `/health`, `/index`, `/plan`, `/execute`, `/loop` (simplified).
- A Claude Code plugin manifest that defines `/plan` and `/af` commands calling the daemon.
- A lazy-start mechanism: the daemon is started on the first command if not already running.
- A token budget guard that estimates cost before execution and asks for confirmation if over budget.
- SQLite logging of every execution (skill, prompt, output, tokens, duration, success, error).
- `install.sh` script that clones the repo, sets up a venv, symlinks the plugin, runs `init` and `index`.

**What is deferred to v0.2+:**

- Judge agent (evaluates output quality).
- Retry loop (re-plan on failure).
- Knowledge graph store.
- Obsidian integration.
- Auto-trigger via PreToolUse hook.
- SSE/WebSocket streaming.
- PyPI publication.
- Launchd/systemd auto-start.

## 3. Implementation Steps for the Harness

### Step 1: Define the Data Models (Pydantic)

- `SkillManifest`: id, name, description, trigger_patterns (list of regex), estimated_token_cost (input/output), estimated_time_seconds, version, author, tags.
- `SkillIndex`: version, generated_at, skills list, skill_paths dict (id → file path).
- `PlanRequest`, `PlanResult`, `ExecuteRequest`, `ExecuteResponse`, `LoopRequest`, `LoopResponse`.

### Step 2: Build the Indexer

- Scan `skills/*/SKILL.md` recursively.
- Use `python-frontmatter` to parse YAML frontmatter.
- Validate each manifest against the Pydantic schema.
- Write a single `index.json` with all skills and their file paths.
- Include a SHA-256 hash of each SKILL.md to detect changes on subsequent runs.

### Step 3: Configuration Management

- Config file at `~/.config/agent-foundry/config.toml`.
- Fields: skills_dir, index_path, default_llm, token_budget, daemon_port, harness_type.
- Provide a default config that points to `~/.claude/plugins/agent-foundry/skills`.
- `init` command creates the config and runs the indexer.

### Step 4: Planner (Recommendation Engine)

- Load `index.json`.
- For a given prompt, iterate over all skills.
- For each skill, test every `trigger_patterns` regex against the prompt. Each match adds a base score (e.g., 0.3).
- Boost score if the skill's name or description appears in the prompt (e.g., +0.2).
- Compute total estimated token cost = input + output.
- Apply cost penalty: `score *= 1.0 / (1.0 + total_cost / 5000.0)` — this favours cheaper skills when relevance is equal.
- Sort by final score descending, return top N (default 5) as `PlanResult` objects containing skill metadata, score, matched patterns, and cost estimates.

### Step 5: Executor

- Accept `skill_id` and a user prompt.
- Retrieve the skill's file path from `index.json`.
- Read the full `SKILL.md` content (including frontmatter and body).
- Build an LLM message: system = the entire SKILL.md content, user = the prompt.
- Call the configured LLM via `litellm.completion` (supports `claude-3-7-sonnet`, `gpt-4o`, etc.).
- Extract the response, token usage, and duration.
- Return `ExecuteResponse` with output, tokens_used, duration_seconds, success boolean, and optional error.

### Step 6: Simplified Loop Endpoint (`/loop`)

- Accept a prompt.
- Call the planner to get the top-ranked skill (limit = 1).
- If no skill is found, return an error (or a fallback message).
- Call the executor with that skill and the prompt.
- Return a `LoopResponse` containing the plan (list of one item) and the execution result, plus total tokens and time.

### Step 7: Daemon (FastAPI)

- Endpoints:
  - `GET /health` — returns `{"status": "ok"}`.
  - `POST /index` — triggers a re-index (returns number of skills indexed).
  - `POST /plan` — accepts `PlanRequest`, returns list of `PlanResult`.
  - `POST /execute` — accepts `ExecuteRequest`, returns `ExecuteResponse`.
  - `POST /loop` — accepts `LoopRequest`, returns `LoopResponse`.
- Token budget guard: before execution, estimate total cost. If it exceeds `token_budget` from config, return a 400 with a message like "Estimated cost exceeds your budget. Increase budget or choose a cheaper skill." (In v0.1 we do not implement an interactive confirmation; we just abort with a clear error.)
- Logging: after each `/execute` or `/loop`, write a record to a SQLite database (or a JSONL file) with: timestamp, skill_id, prompt, output, tokens_used, duration, success, error.

### Step 8: CLI Commands (Click)

- `agent-foundry init` — create config, run index.
- `agent-foundry index` — rebuild index from scratch.
- `agent-foundry cost-report` — print table of all skills with input/output tokens and time.
- `agent-foundry plan "prompt" [--max N]` — call the planner (either directly or via daemon) and print ranked skills.
- `agent-foundry execute skill_id "prompt" [--model]` — call executor and print output.
- `agent-foundry run "prompt" [--model] [--budget]` — call the `/loop` endpoint (or local logic) and print plan + execution result.
- `agent-foundry serve [--port]` — start the daemon (foreground).

### Step 9: Daemon Lazy-Start

- When a user runs `/plan` or `/af` in Claude Code, the plugin invokes `agent-foundry plan` or `agent-foundry run`.
- These CLI commands should first check if the daemon is alive (e.g., via `curl http://127.0.0.1:8765/health`).
- If not, they start the daemon in the background using `agent-foundry serve --port 8765 &` and wait a short moment.
- The daemon's PID should be stored in `~/.config/agent-foundry/daemon.pid` to avoid duplicate processes.

### Step 10: Claude Code Plugin

- Manifest file: `claude_code_plugin.json` (placed inside the repo root, symlinked to `~/.claude/plugins/agent-foundry`).
- Commands:
  - `/plan "args"` → runs `agent-foundry plan "$ARGS"`.
  - `/af "args"` → runs `agent-foundry run "$ARGS"`.
- The plugin does not contain any logic; it just passes the prompt to the CLI.

### Step 11: Installer Script (`install.sh`)

- Steps:
  1. Detect OS (macOS/Linux — others not supported yet).
  2. Ensure Python 3.10+ is installed.
  3. Clone or pull the repo into `~/.agent-foundry`.
  4. Create a virtual environment and run `pip install -e .` (editable install).
  5. Run `agent-foundry init --force` to create config and index.
  6. Symlink the repo into `~/.claude/plugins/agent-foundry` (create parent if needed).
  7. Make `scripts/daemon.sh` (if any) executable — but we rely on the CLI to start the daemon.
- The script should be idempotent (can be re-run to update the tool).

### Step 12: Token Budget Guard Details

- Read `token_budget` from config (default 100,000).
- For a given skill and prompt, estimate total tokens = `estimated_token_cost.input + len(prompt) // 4 + estimated_token_cost.output` (rough estimate).
- If total > budget, the `/loop` endpoint returns a 400 error with a message including the estimate and suggesting to increase budget or use a cheaper skill.
- The CLI `run` command should also check this and print the error.

### Step 13: Logging Implementation

- Use SQLite with a single table `executions`:
  - `id` INTEGER PRIMARY KEY
  - `timestamp` DATETIME
  - `skill_id` TEXT
  - `prompt` TEXT
  - `output` TEXT (may be truncated or stored as text)
  - `tokens_used` INTEGER
  - `duration_seconds` REAL
  - `success` INTEGER (0/1)
  - `error` TEXT
- The log file is stored at `~/.config/agent-foundry/executions.db`.

## 4. Non-Goals for v0.1 (Explicitly Excluded)

- No judge agent: no evaluation of output quality.
- No retry loop: if execution fails or produces bad output, the loop does not re-plan.
- No graph store: no dependency tracking or recommendation based on past executions.
- No Obsidian integration: the orchestrator does not read/write Obsidian notes.
- No auto-trigger: users must explicitly type `/af` or `/plan`.
- No SSE/WebSocket: the response is a single JSON payload.
- No PyPI: installation is via git clone.
- No systemd/launchd: daemon is lazy-started by the CLI on first use.

## 5. Testing and Validation Criteria

- **Installation test**: run `install.sh` on a fresh macOS VM and a fresh Ubuntu VM — both succeed without manual intervention.
- **Indexer test**: `agent-foundry index` correctly parses all existing `SKILL.md` files and generates `index.json` without errors.
- **Cost report test**: `agent-foundry cost-report` prints a table with all skills and their cost estimates.
- **Planner accuracy test**: manually run `agent-foundry plan` on 20 prompts (mix of coding, writing, analysis). Ensure the top-ranked skill is the one a human would consider most relevant. If accuracy < 80%, adjust the regex patterns or scoring weights.
- **Executor test**: `agent-foundry execute anti-slop "Write a clean README"` returns a useful output and logs the execution.
- **Loop test**: `agent-foundry run "Write a test for a sorting function"` — it picks a skill, executes, and returns output. Check that total tokens and time are reported.
- **Token guard test**: temporarily lower budget to 1,000 tokens, run a task that should exceed it — the loop aborts with a clear error message.
- **Claude Code integration test**: after symlinking, open Claude Code, type `/plan "build a react component"` — see a ranked list. Type `/af "build a react component"` — see the execution output.

## 6. Milestone Schedule

- **Cut 1 (already shipped)**: models, indexer, config, CLI init/index/cost-report, install script skeleton. See commit `dbc3a8a`.
- **Cut 2 (3-4 days)**: planner logic, daemon with `/plan` endpoint, CLI `plan` command, Claude Code `/plan` integration, accuracy testing.
- **Cut 3 (3-4 days)**: executor logic, `/execute` endpoint, `/loop` endpoint, CLI `execute` and `run` commands, Claude Code `/af` integration, token budget guard, SQLite logging, lazy-start mechanism, end-to-end testing.

Total: ~10 days from this point.

## 7. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Trigger regex patterns are too narrow | Use a broad set of patterns and allow wildcard matches; score boost compensates for partial matches. |
| LLM API key missing | The daemon should catch `litellm.exceptions.AuthenticationError` and return a user-friendly error: "Set your ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable." |
| Daemon port conflict | Allow `--port` override; if the port is already in use, the lazy-start script should detect it and reuse the existing daemon. |
| Token budget estimation inaccurate | Use a simple estimation (4 chars = 1 token) and allow users to override via config. In v0.2 we can refine based on actual logs. |
| Installation fails on Windows | v0.1 supports only macOS and Linux; a Windows version can be added later if demand exists. |

## 8. Final Deliverables

After implementing the above, the repository should contain:

- A working Python package with all CLI commands.
- A running daemon that persists across sessions (via lazy-start).
- A Claude Code plugin that works out of the box after `install.sh`.
- Full logging of all executions.
- A clean error-handling layer that does not expose stack traces to the user.
- A `README.md` with a quick-start section:

```markdown
## Quick Start

1. Run the installer:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/install.sh | bash
   ```

2. Set your API key:

   ```bash
   export ANTHROPIC_API_KEY=sk-...
   ```

3. Start using it in Claude Code:
   - `/plan "write a react component"` — see which skills match.
   - `/af "write a react component"` — let the orchestrator plan and execute the best skill.

Run `agent-foundry --help` for more CLI commands.
```

## 9. Next Steps

Once this plan is implemented and tested, the next iteration (v0.2) will add:

- A judge agent that scores output quality.
- A retry loop that re-plans and re-executes when score is low.
- A feedback mechanism to adjust scoring weights based on past successes.

But that is **not** part of this plan. The current plan is scoped to deliver a working orchestrator that performs a single pass of plan-execute-return.

## 10. Implementation Guidelines (Recap)

- Python 3.10+ with type hints.
- Pydantic for all data models (schema validation).
- Click for the CLI.
- FastAPI for the daemon.
- LiteLLM as the unified LLM client.
- Skill index as a single JSON file.
- User-level config: `~/.config/agent-foundry/`.
- Logs: `~/.config/agent-foundry/executions.db` (SQLite).
- Daemon is stateless (except for the log) — reads index per request or caches in-memory.
- Installer must be idempotent (re-runnable to update).
- Claude Code plugin is a simple JSON manifest; no logic in the plugin itself.

---

**End of plan.** This document is the complete specification for v0.1. No code is included — only architecture, components, and implementation steps.
