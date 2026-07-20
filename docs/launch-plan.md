# Agent Foundry – Public Launch Plan (Option C)

> Spec-only document. No executable code. Use as input to the implementation harness.
> Last updated: 2026-07-20. Scope: v0.1 public launch.
>
> **Revision note (2026-07-20):** This revision applies three critical fixes before Cuts 2 and 3 proceed: (1) the token budget guard now performs an interactive `y/n` confirmation with a `--force` bypass instead of a hard abort; (2) a `generic-reasoning` fallback skill is defined and made always-available for no-match prompts; (3) the 80% planner-accuracy gate is replaced with log-based measurement, and scoring weights are moved to `config.toml`. SHA-256 index hashing is also replaced with a simpler mechanism. Changed sections are marked `[UPDATED]`.

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
- A token budget guard that estimates cost before execution and, when over budget, returns a `requires_confirmation` response so the CLI can prompt the user for a `y/n` confirmation (bypassable with `--force`).
- A built-in `generic-reasoning` fallback skill that always runs when no trigger patterns match.
- SQLite logging of every execution (skill, prompt, output, tokens, duration, success, error), including the planner scores used, so accuracy can be measured from real usage.
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
- Automated planner-accuracy tuning driven by logged usage data (v0.1 collects the data; v0.2 acts on it).

## 3. Implementation Steps for the Harness

### Step 1: Define the Data Models (Pydantic)

- `SkillManifest`: id, name, description, trigger_patterns (list of regex), estimated_token_cost (input/output), estimated_time_seconds, version, author, tags.
- `SkillIndex`: version, generated_at, skills list, skill_paths dict (id → file path).
- `PlanRequest`, `PlanResult`, `ExecuteRequest`, `ExecuteResponse`, `LoopRequest`, `LoopResponse`.
- **[UPDATED]** `LoopResponse` and `ExecuteResponse` gain two optional fields to support the confirmation flow: `requires_confirmation: bool` (default `false`) and `estimated_cost: TokenEstimate | None`. When `requires_confirmation` is `true`, no execution has occurred yet and `output` is empty.
- **[UPDATED]** `LoopRequest` and `ExecuteRequest` gain a `force: bool` field (default `false`) that, when set, skips the budget confirmation and executes directly.

### Step 2: Build the Indexer

- Scan `skills/*/SKILL.md` recursively.
- Use `python-frontmatter` to parse YAML frontmatter.
- Validate each manifest against the Pydantic schema.
- Write a single `index.json` with all skills and their file paths.
- **[UPDATED] Change detection — keep it simple for 30 skills.** Do **not** compute a SHA-256 hash of each `SKILL.md`. For a corpus of ~30 skills the hashing is over-engineering. Instead, do one of the following (in order of preference):
  1. Record the file `mtime` (modification timestamp) and size for each skill in `index.json`, and re-index a skill only if either changed; or
  2. Simply re-index on demand — the full scan of 30 files takes milliseconds — and cache the parsed index in memory in the daemon with a short TTL (default 60 s, configurable via `index_cache_ttl_seconds`).
  The default implementation is the in-memory cache with a TTL plus an explicit `POST /index` / `agent-foundry index` to force a rebuild. This keeps the indexer trivial and avoids any hashing dependency.
- **[UPDATED] Register the virtual fallback skill.** The `generic-reasoning` skill (see Step 6) is a **virtual skill**: it has no `SKILL.md` file on disk. The indexer must inject it into `index.json` as a synthetic manifest so it appears in the skill list and cost report. Its manifest fields are fixed:
  - `id`: `generic-reasoning`
  - `name`: `Generic Reasoning`
  - `description`: `Fallback skill for prompts that match no specific skill.`
  - `trigger_patterns`: `[]` (empty — it is never matched by patterns; it is selected only when nothing else scores > 0)
  - `estimated_token_cost`: a conservative default (e.g. input 500, output 1500)
  - `tags`: `["fallback", "builtin"]`
  Its system prompt is held in code/config, not a file (see Step 6).

### Step 3: Configuration Management

- Config file at `~/.config/agent-foundry/config.toml`.
- Fields: `skills_dir`, `index_path`, `default_llm`, `token_budget`, `daemon_port`, `harness_type`.
- **[UPDATED]** Add an `index_cache_ttl_seconds` field (default `60`) used by the daemon's in-memory index cache (Step 2).
- **[UPDATED] Configurable planner scoring weights.** Add a `[planner]` section so the scoring formula can be tuned post-launch without code changes:
  ```toml
  [planner]
  pattern_match_weight = 0.3     # score added per matched trigger pattern
  name_in_prompt_boost = 0.2     # score added if skill name/description appears in the prompt
  cost_penalty_divisor = 5000.0  # larger = weaker cost penalty
  max_results = 5                # default number of ranked skills returned by /plan
  ```
  The planner (Step 4) must read these values from config and fall back to the documented defaults if the section is absent.
- Provide a default config that points to `~/.claude/plugins/agent-foundry/skills`.
- `init` command creates the config (including the `[planner]` section with defaults) and runs the indexer.

### Step 4: Planner (Recommendation Engine) [UPDATED]

- Load the index (from the in-memory cache; rebuild if stale per Step 2).
- Read scoring weights from the `[planner]` config section (Step 3); use documented defaults if missing.
- For a given prompt, iterate over all skills (the virtual `generic-reasoning` skill is **excluded** from pattern scoring — it is handled as the explicit fallback in Step 6, never via pattern matches).
- For each skill, test every `trigger_patterns` regex against the prompt. Each match adds `pattern_match_weight` (default 0.3).
- Boost score by `name_in_prompt_boost` (default 0.2) if the skill's name or description appears in the prompt.
- Compute total estimated token cost = input + output.
- Apply cost penalty: `score *= 1.0 / (1.0 + total_cost / cost_penalty_divisor)` (default divisor 5000.0) — this favours cheaper skills when relevance is equal.
- Sort by final score descending, return top N (`max_results`, default 5) as `PlanResult` objects containing skill metadata, score, matched patterns, and cost estimates.
- **Note on tuning:** the weights above are deliberately configurable rather than gated by a fixed accuracy target. We measure planner accuracy from logged real usage (see Section 5) and tune these weights in v0.2 based on that data, not against a hard threshold.

### Step 5: Executor

- Accept `skill_id` and a user prompt.
- **[UPDATED]** If `skill_id` is `generic-reasoning`, use the built-in system prompt from Step 6 instead of reading a file (the skill has no `SKILL.md`).
- Otherwise, retrieve the skill's file path from the index and read the full `SKILL.md` content (including frontmatter and body).
- Build an LLM message: system = the SKILL.md content (or the fallback system prompt), user = the prompt.
- Call the configured LLM via `litellm.completion` (supports `claude-3-7-sonnet`, `gpt-4o`, etc.).
- Extract the response, token usage, and duration.
- Return `ExecuteResponse` with output, tokens_used, duration_seconds, success boolean, and optional error.

### Step 6: Simplified Loop Endpoint (`/loop`) [UPDATED]

- Accept a prompt (and optional `force` flag — see Step 7 / Step 12).
- Call the planner to get the top-ranked skill (limit = 1).
- **Fallback behaviour — explicit `generic-reasoning` skill.** If no skill scores above zero (no trigger patterns match), select the built-in **`generic-reasoning`** skill instead of returning an error. This skill is always available. Its system prompt is:

  > `You are a helpful assistant. The user's prompt didn't match any specific skill. Respond thoughtfully and thoroughly.`

  The `generic-reasoning` skill is a virtual (fileless) skill registered by the indexer (Step 2); its system prompt lives in code (a module constant) with an optional override in `config.toml`. When the fallback is used, the returned plan lists a single item with `skill_id = "generic-reasoning"` so the user can see the fallback was chosen.
- Run the token budget guard (Step 12). If the estimate exceeds budget and `force` is not set, return a `LoopResponse` with `requires_confirmation = true` and `estimated_cost` populated, and do **not** execute yet.
- Otherwise call the executor with the selected skill and the prompt.
- Return a `LoopResponse` containing the plan (list of one item), the execution result, and total tokens and time.

### Step 7: Daemon (FastAPI) [UPDATED]

- Endpoints:
  - `GET /health` — returns `{"status": "ok"}`.
  - `POST /index` — triggers a re-index (returns number of skills indexed).
  - `POST /plan` — accepts `PlanRequest`, returns list of `PlanResult`.
  - `POST /execute` — accepts `ExecuteRequest`, returns `ExecuteResponse`.
  - `POST /loop` — accepts `LoopRequest`, returns `LoopResponse`.
- **[UPDATED] Token budget guard — confirmation, not just abort.** Before executing, estimate total cost (Step 12). If the estimate exceeds `token_budget` **and** the request's `force` flag is `false`, the daemon does **not** abort with a 400. Instead it returns a normal `200` response with:
  ```json
  {
    "requires_confirmation": true,
    "estimated_cost": { "input": 1234, "output": 1500, "total": 2734 },
    "plan": [ { "skill_id": "...", "score": 0.9, ... } ],
    "output": "",
    "tokens_used": 0,
    "duration_seconds": 0,
    "success": false
  }
  ```
  The CLI then prompts the user with a `y/n` confirmation (Step 8). On `y`, the CLI re-sends the identical request with `force = true`, which tells the daemon to skip the guard and execute. On `n`, the CLI aborts locally with a clear message and nothing is executed. This confirmation round-trip is a plain HTTP exchange and **is in scope for v0.1**. A `--force` CLI flag lets power users skip the prompt entirely (it sets `force = true` on the first request).
- Logging: after each `/execute` or `/loop` that actually executes, write a record to SQLite (see Step 13). Records that only returned `requires_confirmation` (no execution) are not logged as executions.

### Step 8: CLI Commands (Click) [UPDATED]

- `agent-foundry init` — create config, run index.
- `agent-foundry index` — rebuild index from scratch.
- `agent-foundry cost-report` — print table of all skills with input/output tokens and time (includes the virtual `generic-reasoning` skill).
- `agent-foundry plan "prompt" [--max N]` — call the planner (either directly or via daemon) and print ranked skills.
- `agent-foundry execute skill_id "prompt" [--model] [--force]` — call executor and print output.
- **[UPDATED]** `agent-foundry run "prompt" [--model] [--budget] [--force]` — call the `/loop` endpoint and print plan + execution result. **Confirmation flow:** if the daemon responds with `requires_confirmation = true`, the CLI prints the estimated cost and the chosen skill, then prompts:
  ```
  Estimated cost: 2,734 tokens (budget: 1,000). Proceed? [y/N]
  ```
  On `y` it re-sends the same request with `force = true` and prints the result; on `n` (or empty/EOF) it prints `Aborted — no tokens spent.` and exits. `--force` skips the prompt and sends `force = true` on the first request. When stdin is not a TTY (e.g. piped/CI), the CLI treats the absence of `--force` as a decline and aborts rather than hanging.
- `agent-foundry serve [--port]` — start the daemon (foreground).

### Step 9: Daemon Lazy-Start

- When a user runs `/plan` or `/af` in Claude Code, the plugin invokes `agent-foundry plan` or `agent-foundry run`.
- These CLI commands should first check if the daemon is alive (e.g., via `curl http://127.0.0.1:8765/health`).
- If not, they start the daemon in the background using `agent-foundry serve --port 8765 &` and wait a short moment.
- The daemon's PID should be stored in `~/.config/agent-foundry/daemon.pid` to avoid duplicate processes.
- **[UPDATED] Note on the confirmation flow:** because the confirmation is a second HTTP request from the same short-lived CLI process, the lazy-started daemon must remain alive between the two requests (it does — it is a persistent background process). The CLI holds the `y/n` prompt in the foreground while the daemon idles.

### Step 10: Claude Code Plugin

- Manifest file: `claude_code_plugin.json` (placed inside the repo root, symlinked to `~/.claude/plugins/agent-foundry`).
- Commands:
  - `/plan "args"` → runs `agent-foundry plan "$ARGS"`.
  - `/af "args"` → runs `agent-foundry run "$ARGS"`.
- The plugin does not contain any logic; it just passes the prompt to the CLI. The `y/n` confirmation surfaces through the CLI's normal stdout/stdin, which Claude Code relays to the user.

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

### Step 12: Token Budget Guard Details [UPDATED]

- Read `token_budget` from config (default 100,000).
- For a given skill and prompt, estimate total tokens = `estimated_token_cost.input + len(prompt) // 4 + estimated_token_cost.output` (rough estimate; 4 chars ≈ 1 token).
- **[UPDATED] Behaviour when over budget — confirm, then optionally proceed:**
  1. If `total <= budget`, execute normally.
  2. If `total > budget` and `force = false`, return `requires_confirmation = true` with the `estimated_cost` breakdown (input / output / total) and the selected plan, and do **not** execute. (See Step 7 for the exact response shape.)
  3. If `total > budget` and `force = true`, skip the guard and execute (the user has already confirmed, or passed `--force`).
- The CLI `run` and `execute` commands implement the user-facing side of this: they detect `requires_confirmation`, print the estimate, prompt `y/n`, and on `y` re-send with `force = true`. `--force` bypasses the prompt.
- The guard is a lightweight, deterministic check on the estimate — no LLM call is made until the user has confirmed (or budget is sufficient), so a declined confirmation spends **zero** tokens.

### Step 13: Logging Implementation [UPDATED]

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
  - **[UPDATED]** `planner_score` REAL — the final score of the chosen skill (NULL for direct `execute` calls). Enables measuring planner accuracy from real usage (Section 5).
  - **[UPDATED]** `was_fallback` INTEGER (0/1) — `1` when the `generic-reasoning` fallback was selected, so no-match frequency can be tracked.
- The log file is stored at `~/.config/agent-foundry/executions.db`.

## 4. Non-Goals for v0.1 (Explicitly Excluded) [UPDATED]

- No judge agent: no evaluation of output quality.
- No retry loop: if execution fails or produces bad output, the loop does not re-plan.
- No graph store: no dependency tracking or recommendation based on past executions.
- No Obsidian integration: the orchestrator does not read/write Obsidian notes.
- No auto-trigger: users must explicitly type `/af` or `/plan`.
- No SSE/WebSocket: the response is a single JSON payload (the budget confirmation is a second, separate JSON request/response — not a stream).
- No PyPI: installation is via git clone.
- No systemd/launchd: daemon is lazy-started by the CLI on first use.
- No automated accuracy tuning: v0.1 **measures** planner accuracy from logs but does not auto-adjust weights; tuning is a manual/v0.2 activity.

**In scope (clarification):** The `generic-reasoning` fallback skill **is** part of v0.1 (shipped in Cut 3). It is intentionally minimal — a single generic system prompt — and is not a "judge" or a retry mechanism. It exists only so that a prompt matching no specific skill still produces a useful response rather than a dead end.

## 5. Testing and Validation Criteria [UPDATED]

- **Installation test**: run `install.sh` on a fresh macOS VM and a fresh Ubuntu VM — both succeed without manual intervention.
- **Indexer test**: `agent-foundry index` correctly parses all existing `SKILL.md` files and generates the index without errors, **and** the virtual `generic-reasoning` skill appears in the index and cost report.
- **Cost report test**: `agent-foundry cost-report` prints a table with all skills (including `generic-reasoning`) and their cost estimates.
- **[UPDATED] Planner accuracy — measure, don't gate.** Run `agent-foundry plan` on a set of ~20 representative prompts (mix of coding, writing, analysis) and record whether the top-ranked skill is what a human considers most relevant. **Do not gate the release on a fixed threshold (the previous "80%" rule is removed).** Instead:
  - Confirm that scores are logged (`planner_score`, `was_fallback` in the `executions` table) so accuracy can be computed from **real usage** once the tool is in users' hands.
  - Confirm the scoring weights are read from `config.toml` and that changing `pattern_match_weight`, `name_in_prompt_boost`, or `cost_penalty_divisor` changes rankings without a code change.
  - Use the collected accuracy data to tune the planner in **v0.2**. v0.1 ships with sensible default weights; it does not block launch on hitting a target number.
- **Fallback test [UPDATED]**: run `agent-foundry run "asdfghjkl nonsense prompt that matches nothing"` — confirm the `generic-reasoning` skill is selected, the response is produced, and the log record has `was_fallback = 1`.
- **Executor test**: `agent-foundry execute anti-slop "Write a clean README"` returns a useful output and logs the execution.
- **Loop test**: `agent-foundry run "Write a test for a sorting function"` — it picks a skill, executes, and returns output. Check that total tokens and time are reported.
- **[UPDATED] Token guard confirmation test**: temporarily lower `token_budget` to 1,000, then run a task that exceeds it. Verify the full flow end-to-end:
  1. The daemon returns `requires_confirmation = true` with a populated `estimated_cost` and **no** execution/log record.
  2. The CLI prints the estimate and prompts `y/n`.
  3. Answering `n` prints `Aborted — no tokens spent.` and no execution is logged.
  4. Answering `y` (or passing `--force`) re-sends with `force = true`, executes, returns output, and logs the execution.
  5. In a non-TTY context (piped input) without `--force`, the CLI declines and aborts rather than hanging.
- **Claude Code integration test**: after symlinking, open Claude Code, type `/plan "build a react component"` — see a ranked list. Type `/af "build a react component"` — see the execution output (and, if over budget, the confirmation prompt).

## 6. Milestone Schedule [UPDATED]

- **Cut 1 (already shipped)**: models, indexer, config, CLI init/index/cost-report, install script skeleton. See commit `dbc3a8a`.
- **Cut 2 (3-4 days)**: planner logic with configurable weights from `config.toml`, daemon with `/plan` endpoint, CLI `plan` command, Claude Code `/plan` integration, accuracy **measurement** wiring (log scores). Includes the simple mtime/TTL change-detection for the indexer (no SHA-256).
- **Cut 3 (3-4 days)**: executor logic, `/execute` endpoint, `/loop` endpoint, CLI `execute` and `run` commands, Claude Code `/af` integration, token budget guard **with the confirmation round-trip and `--force` flag**, the `generic-reasoning` fallback skill, SQLite logging (including `planner_score` and `was_fallback`), lazy-start mechanism, end-to-end testing.

Total: ~10 days from this point. The confirmation flow and fallback skill are small, well-scoped additions (a couple of extra response fields, one CLI prompt, one virtual skill) and fit comfortably within the Cut 3 budget.

## 7. Risks and Mitigations [UPDATED]

| Risk | Mitigation |
|------|------------|
| Trigger regex patterns are too narrow | Use a broad set of patterns and allow wildcard matches; score boost compensates for partial matches. The `generic-reasoning` fallback guarantees a response even when nothing matches. |
| Planner picks the wrong skill | **We measure, not gate.** Planner scores and fallback usage are logged (`planner_score`, `was_fallback`) so real-world accuracy can be computed and the configurable weights tuned in v0.2. No launch-blocking accuracy threshold. |
| Scoring weights hard to tune | Weights (`pattern_match_weight`, `name_in_prompt_boost`, `cost_penalty_divisor`, `max_results`) live in the `[planner]` section of `config.toml` and can be changed without code edits or a redeploy. |
| LLM API key missing | The daemon should catch `litellm.exceptions.AuthenticationError` and return a user-friendly error: "Set your ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable." |
| Daemon port conflict | Allow `--port` override; if the port is already in use, the lazy-start script should detect it and reuse the existing daemon. |
| Token budget estimation inaccurate | Use a simple estimation (4 chars = 1 token). Rather than silently aborting, the guard **asks the user to confirm** over-budget runs (with the estimate shown) and offers `--force`; users can also raise `token_budget` in config. v0.2 can refine estimates from actual logs. |
| Prompt matches no skill (dead end) | The always-available `generic-reasoning` fallback skill runs a generic-assistant system prompt so the user still gets a thoughtful answer instead of an error. |
| Installation fails on Windows | v0.1 supports only macOS and Linux; a Windows version can be added later if demand exists. |

## 8. Final Deliverables [UPDATED]

After implementing the above, the repository should contain:

- A working Python package with all CLI commands.
- A running daemon that persists across sessions (via lazy-start).
- A Claude Code plugin that works out of the box after `install.sh`.
- An interactive token-budget confirmation flow (`requires_confirmation` → `y/n` prompt → `force` re-request) with a `--force` bypass.
- An always-available `generic-reasoning` fallback skill for unmatched prompts.
- Full logging of all executions, including planner scores and fallback usage for later accuracy analysis.
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
     If a task exceeds your token budget, you'll be asked to confirm before anything runs
     (add `--force` to skip the prompt). If nothing matches, a general-purpose fallback answers.

Run `agent-foundry --help` for more CLI commands.
```

## 9. Next Steps [UPDATED]

Once this plan is implemented and tested, the next iteration (v0.2) will add:

- A judge agent that scores output quality.
- A retry loop that re-plans and re-executes when score is low.
- A feedback mechanism to adjust scoring weights based on past successes — **driven by the planner accuracy data collected in v0.1** (the logged `planner_score` / `was_fallback` history).

But that is **not** part of this plan. The current plan is scoped to deliver a working orchestrator that performs a single pass of plan-execute-return, with an interactive budget confirmation and a generic fallback.

## 10. Implementation Guidelines (Recap) [UPDATED]

- Python 3.10+ with type hints.
- Pydantic for all data models (schema validation).
- Click for the CLI (including the `y/n` confirmation prompt and `--force` flag).
- FastAPI for the daemon.
- LiteLLM as the unified LLM client.
- Skill index as a single JSON file; change detection via mtime/size or an in-memory TTL cache — **no SHA-256 hashing**.
- Planner scoring weights are read from the `[planner]` section of `config.toml`.
- User-level config: `~/.config/agent-foundry/`.
- Logs: `~/.config/agent-foundry/executions.db` (SQLite), including `planner_score` and `was_fallback`.
- Daemon is stateless (except for the log) — reads index per request or caches in-memory with a TTL. It must stay alive between the two requests of a budget confirmation.
- The `generic-reasoning` fallback is a virtual (fileless) skill injected by the indexer; its system prompt lives in code with an optional `config.toml` override.
- Installer must be idempotent (re-runnable to update).
- Claude Code plugin is a simple JSON manifest; no logic in the plugin itself.

---

**End of plan.** This document is the complete specification for v0.1. No code is included — only architecture, components, and implementation steps.
