# Changelog

## 0.1.0 — 2026-07-20

**Public launch — Option C (plan → execute → return).**

The repo delivers a working Python package that orchestrates 30+ skills via a FastAPI daemon. The thin Claude Code plugin (registered in `claude_code_plugin.json`) exposes `/plan` and `/af` slash commands that POST to the daemon.

**What's new this release:**

- **Python package** (`agent-foundry`, installable via `pip install -e .` from the repo):
  - `init`, `index`, `cost-report`, `plan`, `execute`, `run`, `serve` (Click commands)
  - `~/.config/agent-foundry/config.toml` with `[core]` + `[planner]` sections, weights tunable without code edits
  - Pydantic data models; LiteLLM as the unified LLM client (any model)
  - Pure-Python YAML frontmatter parser (no PyYAML needed)
- **FastAPI daemon** with `/health`, `/index`, `/plan`, `/execute`, `/loop`
  - Lazy-start by the CLI (no systemd/launchd requirement)
  - In-memory index cache with TTL (default 60s, configurable)
  - Token budget guard returns `requires_confirmation` → CLI prompts `y/n` → re-sends with `force=true`. Zero tokens spent on decline.
- **Virtual `generic-reasoning` fallback skill** injected into the index by the indexer — runs when no skill matches. Has a configurable system prompt in `config.toml` (`fallback_system_prompt = "..."`).
- **SQLite execution log** at `~/.config/agent-foundry/executions.db` with `planner_score` and `was_fallback` columns for later accuracy analysis (planning for v0.2 tuning).
- **Claude Code plugin manifest** at `claude_code_plugin.json` (symlinked into `~/.claude/plugins/agent-foundry` by `install.sh`).
- **Install script** (`install.sh`) — idempotent, macOS/Linux, creates venv + symlinks + runs `init`.

**What's deferred to v0.2+:** judge agent, retry loop, knowledge graph, auto-trigger, SSE streaming, PyPI publication, system-level auto-start.

---

## 0.2.0-pre — 2026-07-20

In development per [`docs/improvement-plan.md`](docs/improvement-plan.md). Working on Option C (public launch) was v0.1. v0.2 brings the structure to support multiple harnesses, agents, and quality eval.

**New in v0.2-pre:**

- **`docs/architecture.md`** — the skill-vs-agent taxonomy. Single page that explains what each is and how to decide which to make.
- **`docs/authoring.md`** — portability rules: action verbs over tool names, ≤8 KB / ≤150 lines, exactly one `Use when...` trigger phrase, plugin-scoped agent names. The portability contract for Codex/Gemini/Hermes/OpenCode.
- **`scripts/foundry-eval.py`** — static quality evaluation that replaces `validate.sh` as the CI gate. Checks description trigger phrase, body size, tool vocabulary, anti-patterns section, verification checklist, references/ split, and agent-name uniqueness. Run via `python scripts/foundry-eval.py`.
- **`scripts/provenance-audit.py`** — per-skill provenance audit for §2.12. Detects whether a skill body retains verbatim text from a known upstream or is a clean-room rewrite. Output is a checklist; it does not delete anything. Current snapshot: 30 skills, 0 review-required (all `credit_only`).
- **`agents/af-critic/`** — the judge agent. Scores output on correctness, slop, scope. Returns JSON only.
- **`agents/af-planner/`** — the decomposer. Takes a request, returns a JSON plan naming skills/agents in order.
- **`agent_foundry/judge.py`** + `--judge` flag on `run` + `LoopRequest.judge` field + `LoopResponse.judge_score` + 4 new columns in the SQLite `executions` table.
- **`hooks/session-end.sh`** — real distillation via the daemon when reachable, falls back to a fillable placeholder.

**Not yet implemented (per the plan):**

- Adapter framework (`tools/adapters/capabilities.py`, harness emitters, Makefile) — Cut #2 work.
- Attribution purge (depends on audit sign-off)
- New discipline skills (`spec-first`, `dependency-diet`, etc.)
- Component-split marketplace install


---

## 0.1.0-pre — 2026-07-20

Initial development; superseded by 0.1.0 (Python implementation shipped).

**Public launch — Option C (plan → execute → return).**

**16 core skills + 1 optional (1 in `skills/optional/`):**

(see previous v0.1.0 entries preserved below)

---

Adapted (from MIT/Apache-2.0):
- `prompt-discipline` — the 4 rules: think before acting, minimum viable change, surgical edits, goal-driven
- `plan-before-code` — no implementation without an approved spec

Inspired (idea adopted, content rewritten):
- `context-optimization` — keep tool outputs small, sandbox large files, reference not repeat
- `anti-slop` — kill filler prose, over-commenting, defensive over-engineering, emoji headers, unnecessary abstractions
- `session-closeout` — reconcile changes, update docs, list loose ends, write handoff note
- `plan-then-act` — plan first, then act; the plan may change mid-execution
- `constraint-then-solve` — restate the problem, list constraints, then solve

Original (authored from operational experience):
- `verify-first` — triangle verification meta-discipline
- `re-verify-findings` — re-verify audits / bug claims before executing
- `measure-first` — query live data before planning
- `bottleneck-gating` — phase by measured bottleneck, not requested order
- `pushback-when-wrong` — surface discrepancies with evidence
- `read-before-build` — read source before trusting plan claims
- `show-your-work` — output a thinking-trace after complex work
- `landscape-first` — research 5-10 competitors before building
- `quality-protocol` — unified maximum-quality protocol for every non-trivial task

**Optional skill (1 in `skills/optional/`):**
- `design-language` — restraint, typography, color, spacing, motion

**Total: 17 skills shipped.**

**Optional skills (6 in `skills/optional/`):**
- `chrome-devtools-mcp-bridge`
- `persistent-memory`
- `token-compression`
- `design-language`
- `funnel-pr-guard`
- `sql-migration-trio`
- `persistent-memory` — cross-session context persistence
- `token-compression` — compress tool outputs, logs, files before they consume context

**Optional skills — original (2 in `skills/optional/`):**
- `funnel-pr-guard` — generalized from operational PR review discipline
- `sql-migration-trio` — generalized from operational migration management

**Total: 22 skills shipped.**

**Layer 1 — additional core skills (8 in `skills/core/`):**

Adapted/inspired:
- `api-design` — inspired by Stripe + GitHub + Heroku API design docs (CC-BY-4.0)
- `cron-troubleshoot` — original (synthesized from operational use)
- `e2e-test-strategy` — original
- `feedback-loop` — original
- `workflow-decompose` — original
- `automation-pick` — original
- `session-distill` — original
- `knowledge-extract` — original

**Total core: 24. Total optional: 6. Total: 30 skills shipped.**

**Layer 2 — workflow runbooks (5 in `workflows/`):**

- `workflows/ci-cd-vercel.md` — Vercel preview + production deploy with smoke tests
- `workflows/e2e-on-pr.md` — Playwright E2E on every PR
- `workflows/release-train.md` — weekly release process (tag → changelog → deploy → smoke → notes)
- `workflows/skill-update.md` — weekly scan for upstream skill updates
- `workflows/session-to-skill.md` — distill a session into a new skill draft

These are runbooks, not skills — they don't auto-trigger. They're structured guides you copy and adapt.

**Hook:**
- `session-closeout.sh` — Bash hook that prompts the closeout skill at session end

**Scripts:**
- `install.sh` — auto-detect harness and install
- `validate.sh` — lint all skills

**Catalog:**
- `decisions.md` — public verdicts on every source
- `sources.md` — license ledger for every source
- `skills.csv` — private triage ledger (gitignored)

See `ATTRIBUTIONS.md` for the full lineage.
