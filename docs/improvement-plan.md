# Agent Foundry – Improvement Roadmap (v0.2 → v1.0)

> Planning document. Successor to `docs/launch-plan.md` (v0.1 is shipped and tested).
> Last updated: 2026-07-20. Scope: everything after the v0.1 public launch.
> Reference studied: [`wshobson/agents`](https://github.com/wshobson/agents) (94 plugins, 203 agents, 175 skills, 5 harnesses).

---

## 0. The thesis: don't out-breadth them, out-*think* them

`wshobson/agents` is a mature **static marketplace**: one Markdown source-of-truth, adapters that emit harness-native artifacts for five CLIs, an offline three-layer eval framework, and a big catalog. It is very good. We will not win by shipping 203 agents and 175 skills — that is a treadmill we would lose.

Agent Foundry already has three things `wshobson/agents` does **not**:

1. **A runtime orchestrator.** We plan → score → dispatch → **log** every execution. Their install is static; the model does all the routing. Our daemon is a real differentiator — lean into it.
2. **Closed-loop measurement.** We log `planner_score` and `was_fallback` per run. We can measure real routing accuracy from usage and tune from data — not vibes. Their eval is offline-only.
3. **A curation doctrine.** ≤150-line skills, a licensing gate, attribution discipline, and a "we say no to 90% of sources" intake. This is a brand, and it is the *opposite* of catalog sprawl.

**External validation of the doctrine:** 2026 research on agent instruction files found that *human-written* `AGENTS.md` files raise task-success ~4% and cut agent-generated bugs 35–55%, while *LLM-generated* instruction files *decrease* success and raise inference cost 20%+ ([source](https://www.morphllm.com/agents-md-guide)). Curation beats generation. That is our entire premise.

So the strategic bet for v0.2 → v1.0 is: **become the smart, self-improving, measured, multi-harness orchestrator — with a small curated catalog — rather than the biggest catalog.** Borrow their structural rigor (adapter framework, eval harness, agents, progressive disclosure). Keep our runtime, our measurement, and our restraint.

What we adopt from them, what we don't:

| Adopt | Skip / adapt |
|---|---|
| Multi-harness adapter framework (`tools/adapters/` + capability matrix) | Their catalog size — we stay curated |
| An eval framework (static → LLM-judge → Monte-Carlo) | Their purely-offline stance — we fuse eval with our real logs |
| An `agents/` layer of domain experts | 203 of them — we ship a tight, high-leverage set |
| Progressive disclosure (`SKILL.md` nav + `references/`) | Nothing to skip — pure win |
| "Talk about actions, not tools"; 8 KB Codex cap; unique agent names | Their `make`/Python monorepo weight if it out-scales our needs |

---

## 1. Where we stand today (honest audit)

**Shipped and solid**

- Python orchestrator: `indexer`, `planner`, `executor`, `loop`, `daemon`, `logging_db`, `config`, `cli`, `models`.
- 30 core + 6 optional `SKILL.md` files — meta-cognitive *disciplines* (anti-slop, plan-before-code, verify-first, context-optimization, …), not domain experts.
- Interactive budget guard, `generic-reasoning` fallback, SQLite logging with `planner_score` / `was_fallback`.
- Curation apparatus: `catalog/` ledger, `schemas/skill-manifest.schema.json`, `ATTRIBUTIONS.md`, `scripts/validate.sh`, licensing gate in `docs/philosophy.md`.
- Auto-learning flywheel: `hooks/session-end.sh` → `plans/sessions/*` → `scripts/auto-extract.sh` → draft skill; weekly `scripts/skill-update.sh` upstream scan.

**Gaps (ranked by leverage)**

1. **No `agents/` layer.** We have disciplines but no domain *actors*. This is the single biggest structural gap versus the reference.
2. **"Harness-agnostic" is a claim, not a build.** `docs/philosophy.md` and `docs/auto-learning.md` name Codex / Hermes / Gemini / OpenCode, but there is no adapter that emits harness-native artifacts. Everything is Claude-Code-shaped.
3. **No quality eval.** We validate *structure* (`validate.sh`) but never *quality*. No LLM-judge, no reliability sampling, no drift/dead-link "garden" check.
4. **Trigger patterns are brittle.** v0.1 does exact-regex matching over the description's "Use when…" clause; no fuzzy match. The fallback masks misses instead of surfacing them.
5. **Workflows are prose, not runnable.** `workflows/*.md` describe pipelines; nothing executes or validates them.
6. **MCP story is thin.** One optional bridge skill (`chrome-devtools-mcp-bridge`). No recommended MCP bundle, no MCP-aware routing.
7. **Docs are scattered.** `philosophy.md`, `auto-learning.md`, `launch-plan.md` are good, but there is no capability matrix, no authoring guide, no docs index.
8. **Orchestrator is single-pass.** No judge, no retry, no eval feedback into scoring weights (all deferred in v0.1, correctly — now it's time).

---

## 2. Area-by-area improvement plan

Each area lists **what to change**, **why**, and a **concrete first deliverable**. Priority tags: **P0** (v0.2 must-have), **P1** (v0.3), **P2** (v1.0 / opportunistic).

### 2.1 Skills — sharpen and extend the catalog

**Update existing (P0).** Migrate every skill to **progressive disclosure** so it survives the Codex 8 KB cap and other harnesses cleanly:

```
skills/core/<name>/
├── SKILL.md          # navigation + quick-start + decision tree (≤150 lines / ≤8 KB)
└── references/       # deep material, loaded on demand
    ├── details.md
    └── examples/
```

- Audit all 36 skills against `SKILL_OVER_CODEX_CAP` (any body > 8 KB with no `references/` → split).
- Rewrite bodies to **"talk about actions, not tools"** — no `Read`/`Grep`/`TodoWrite`/`Task` vocabulary in skill bodies, so they port to Codex/OpenCode/Gemini without degradation.
- Enforce one recognized trigger phrase per description (`Use when …`, `Use PROACTIVELY when …`) — this becomes a lint (see 2.9).

**New skills — grow *coverage of disciplines*, not domains (P1).** Stay true to the "non-obvious, reusable idea" criterion. Candidate additions, each ≤150 lines:

- `spec-first` — write the acceptance test / interface before the implementation.
- `error-budget-triage` — decide fix-now vs defer using severity × likelihood.
- `dependency-diet` — resist adding a dependency; inline or vendor the 20 lines.
- `reversible-first` — prefer the change you can undo; gate irreversible ones.
- `context-handoff` — structured state transfer between agents/sessions (pairs with the daemon).
- `mcp-scoping` — choose the *minimal* MCP/tool allowlist for a task (ties to 2.5).

Keep the intake discipline, adjusted for the authorship model in §2.12: each new skill goes through `catalog/skills.csv` (internal triage) → license gate → `decisions.md` → **own-authorship attestation** → `CHANGELOG` → `validate.sh`. (The `ATTRIBUTIONS.md` step is retired once §2.12 lands.)

**First deliverable:** a `references/` split PR for the three largest skills + a `docs/authoring.md` (see 2.10) that codifies the ≤8 KB / action-verb / trigger-phrase rules.

### 2.2 Agents — the missing layer (P0, the flagship v0.2 feature)

Introduce an `agents/` tree. Draw the **skill vs agent line explicitly** (put it in `docs/architecture.md`):

- **Skill** = a *discipline* the model applies to its own work (how to think). Stateless, always the caller.
- **Agent** = a *role* the orchestrator can dispatch or the model can delegate to (who acts). Has a model tier, an optional tool allowlist, and may own a workflow.

Ship a **tight, curated set** (~8–12 agents, not 200). Suggested first cohort, plugin-scoped names to avoid collisions (`agent-foundry-<role>`):

| Agent | Model tier | Job |
|---|---|---|
| `af-planner` | opus | Decompose a request into a skill/agent plan (formalizes today's `/plan`). |
| `af-critic` | opus | The **judge** — score an output on correctness, slop, scope. Feeds 2.8. |
| `af-verifier` | sonnet | Re-run claims/tests; the `re-verify-findings` skill as an actor. |
| `af-refactorer` | sonnet | Behavior-preserving code changes with a diff summary. |
| `af-test-author` | sonnet | Author tests from a spec (`e2e-test-strategy` as an actor). |
| `af-doc-writer` | haiku | Docs/READMEs under the anti-slop discipline. |
| `af-researcher` | sonnet | Web/repo fan-out research, returns cited findings. |
| `af-security-reviewer` | opus | Read-only security pass. (Never `fable` — cyber classifiers fall back anyway.) |

Rules borrowed from the reference's authoring guide, baked in from day one:

- **Globally unique, plugin-scoped names** (`agent-foundry-critic`, not `critic`) — CI check for collisions.
- **Avoid built-in Codex names** (`default`, `worker`, `explorer`).
- **Model as alias** (`opus`/`sonnet`/`haiku`/`inherit`) so adapters can map per harness.
- **Tool allowlist via `tools:`** where the harness honors it; degrade gracefully elsewhere.

**First deliverable:** `af-critic` + `af-planner` (they unlock the v0.2 loop, §2.8), with the skill/agent taxonomy documented.

### 2.3 Commands — a real `commands/` surface (P1)

Today only `/plan` and `/af` exist, hard-wired in `claude_code_plugin.json`. Add a `commands/` directory of thin slash-commands that the adapter framework can transpile (Codex → skills, Gemini → TOML, Copilot → prompt files):

- `/af-plan`, `/af-run` (rename the current two for namespacing).
- `/af-index`, `/af-cost` (surface indexer + cost-report in-harness).
- `/af-eval <skill|agent>` (run the quality eval, §2.9).
- `/af-distill` (invoke the session→skill flow on demand, §2.7).

Keep each command a thin forwarder to the CLI or daemon — no logic in the command file (preserves harness portability).

### 2.4 Hooks — make them portable and useful (P1)

We have `session-end.sh` and `session-closeout.sh`. Improvements:

- **Emit real distilled artifacts,** not transcript placeholders — call the daemon's executor with the `session-distill` skill so the artifact is filled, not a stub.
- **Add a `PostRun` log-flush hook** so the daemon's SQLite log survives crash/exit.
- **Document degradation honestly:** hooks are first-class only on Claude Code and OpenCode. In the capability matrix (§2.6) mark hooks as unsupported on Codex/Gemini/Cursor and provide the cron/CI fallback (already partly done in `auto-learning.md`).
- **Optional `PreToolUse` auto-trigger** remains a *non-goal until v1.0* — it violates the "no force-loading" doctrine unless it only *suggests* a skill rather than injecting a body.

### 2.5 MCPs — from one bridge to a curated bundle (P1)

- Publish a **recommended MCP bundle** (`docs/mcp-bundle.md`) — a small, vetted set (filesystem, git, fetch/web, and the existing chrome-devtools bridge) with per-harness wiring, mirroring how each harness (Codex, zcode, Gemini, OpenCode) speaks MCP.
- Add the `mcp-scoping` skill (§2.1) so the model requests the **minimal** MCP/tool set per task — the token-budget doctrine applied to tools.
- **MCP-aware routing (P2):** let a skill's manifest declare `requires_mcp: [...]`; the planner down-ranks skills whose MCPs aren't connected and tells the user what to enable. This is a genuinely novel edge the static reference can't match, because we have a runtime.

### 2.6 Multi-harness — the adapter framework (P0 for Codex/Gemini; P1 for the rest)

This is where the user's ask (Codex, Hermes, zcode, Kimi Code, …) lands. Do it the way the reference proved works, and lean on the emerging standard: **`AGENTS.md` + MCP are now open conventions** (donated to the Linux Foundation's Agentic AI Foundation in Dec 2025), read by 28–30+ tools ([agents.md](https://agents.md/), [source](https://www.morphllm.com/agents-md-guide)). Build to the standard, adapt at the edges.

**Architecture:**

```
tools/adapters/
├── capabilities.py     # the capability matrix (source of truth; docs generated from it)
├── codex.py            # committed lean registry + gitignored transformed tree
├── gemini.py
├── opencode.py
├── cursor.py
├── copilot.py
├── hermes.py           # AGENTS.md-family; verify config at build time
├── zcode.py            # AGENTS.md + MCP; GLM/Kimi/DeepSeek/OpenRouter backends
└── kimi.py             # Moonshot; AGENTS.md-family
Makefile                # make generate HARNESS=x | generate-all | validate | garden
```

**Principles (all proven by the reference):**

- **One Markdown source-of-truth** (`skills/`, `agents/`, `commands/`). Adapters transform; authors write once.
- **Commit lean registries, gitignore transformed trees.** Only small JSON/TOML manifests pointing at source are checked in; the big generated trees regenerate on demand. CI fails on registry drift.
- **Canonical context file = `AGENTS.md`,** with `CLAUDE.md` as a symlink/import. Keep it ≤150 lines / ~500 tokens (a table of contents, not an encyclopedia).
- **Mechanical degradation:** tool allowlists → permission blocks or dropped; model aliases mapped per harness; skills > 8 KB split into `references/`; slash commands → skills/TOML/prompt files.

**Harness rollout order and honesty about each:**

| Harness | Confidence | Notes |
|---|---|---|
| Codex CLI | High | AGENTS.md-native, 8 KB skill cap, commands→skills, no tool vocab. Proven pattern. **First target.** |
| Gemini CLI | High | Native skills/subagents (2026 spec), TOML commands, `GEMINI.md`. Second target. |
| OpenCode | High | `permission:` block from `tools:`, hooks via TS plugins. |
| Cursor | Med | Reuses `.claude/`; coarser tool model. |
| Copilot | Med | Markdown agents + SKILL.md; serves Claude models natively. |
| **zcode** (Z.AI/GLM-5.2) | Med | Confirmed: reads `AGENTS.md`, speaks MCP, backends incl. GLM / Kimi / DeepSeek / OpenRouter ([review](https://www.bitdoze.com/zcode-ai-review/)). Good AGENTS.md-family target. |
| **Kimi Code** (Moonshot) | Med-Low | AGENTS.md-family; reachable directly and via zcode's Moonshot backend. **Verify exact config format with a spike before building the adapter.** |
| **Hermes** | Low | Local agent gateway; `config.yaml` hooks already sketched in `auto-learning.md`. **Verify current config surface before committing an adapter.** |

**Discipline (borrowed from our own curation criterion #4 — "we verify it ourselves"):** every new harness gets a **one-day verification spike** — install the real CLI, generate artifacts, confirm it loads them — *before* the adapter is declared supported. No adapter ships against a guessed config format. Track each harness's verified config surface in `capabilities.py` with a "last verified" date, exactly as the reference does.

**First deliverable:** `capabilities.py` + `codex.py` + `Makefile` (`make generate HARNESS=codex`), verified against the real Codex CLI, plus `docs/harnesses.md` generated from the matrix.

### 2.7 Automations / auto-learning — close the flywheel (P1)

The session→skill pipeline exists but produces stubs. Upgrade it:

- **Real distillation:** the session-end hook calls the executor with `session-distill`, so `plans/sessions/*` are filled, not placeholders.
- **Auto-eval the draft:** `auto-extract.sh` output runs through the quality eval (§2.9) and only surfaces drafts that clear a static+judge bar — junk never reaches human review.
- **Upstream scan → PR:** extend `skill-update.sh` to open a draft PR (via CI) summarizing the upstream diff, not just a digest to read.
- **Ship the GitHub Actions** that `auto-learning.md` documents (weekly scan, validate-on-PR) as real `.github/workflows/*.yml`, not just examples.

### 2.8 Orchestrator / runtime — v0.2 loop (P0)

The v0.1 plan deferred these; now they're the point. Add them **behind flags**, keeping single-pass as default:

- **Judge (`af-critic`):** after `/loop` executes, optionally score the output (correctness / slop / scope). Store the score in the `executions` table next to `planner_score`.
- **Retry-on-low-score:** if judge score < threshold and `--retry` is set, re-plan with the failure as context (max 1 retry in v0.2 — bounded, no runaway loops).
- **Data-driven weight tuning:** the promise from `launch-plan.md` §9 — read the accumulated `executions.db`, compute real routing accuracy, and *suggest* new `[planner]` weights (`af tune --dry-run`). Human applies; we never auto-mutate config.
- **Fuzzy trigger matching:** replace exact-regex-only with an optional embedding or token-overlap fallback so near-misses route correctly instead of dropping to `generic-reasoning`. Log every fallback as a routing miss to feed tuning.

### 2.9 Quality evaluation — `foundry-eval` (P0 for static, P1 for judge/MC)

Adopt the reference's three-layer model, but **fuse it with our real logs** (the edge they can't match):

1. **Static (<2 s, free):** frontmatter shape, trigger-phrase presence, ≤8 KB / `references/` split, action-verb linting, agent-name collisions, dead links. This replaces/extends `validate.sh`.
2. **LLM judge (~30 s):** semantic quality of a skill/agent across correctness, clarity, scope, portability. Reuse `af-critic`.
3. **Monte-Carlo / real-log reliability:** instead of *only* simulating 50–100 runs, compute reliability from **actual `executions.db` history** where available, and simulate only for unused skills. Closed-loop eval, not offline-only.

Expose as `af eval <path> --depth quick|full` and a `make garden` drift/dead-link/cap check. Gate PRs on the static layer in CI.

**First deliverable:** the static layer (`af eval --depth quick`) wired into CI, replacing `validate.sh`.

### 2.10 Documentation — an indexed, generated doc set (P1)

Restructure `docs/` into a navigable set, most generated from source so it can't drift:

- `docs/index.md` — the map (read-in-this-order).
- `docs/architecture.md` — skill-vs-agent taxonomy, the orchestrator, design principles.
- `docs/harnesses.md` — capability matrix, **generated from `capabilities.py`**.
- `docs/authoring.md` — the portable-content style guide (≤8 KB, action verbs, trigger phrases, unique names, model aliases).
- `docs/agents.md`, `docs/skills.md` — catalogs, generated from frontmatter.
- `docs/mcp-bundle.md`, `docs/foundry-eval.md`.
- Keep `philosophy.md`, `auto-learning.md`, `launch-plan.md`, `improvement-plan.md` (this file).
- **`AGENTS.md` at repo root** (canonical context file; `CLAUDE.md` symlinks to it) — ≤150 lines.

### 2.11 Packaging & distribution (P2)

- Keep `curl | bash` as the primary path; keep PyPI deferred until the surface stabilizes (still correct).
- Add a **Claude Code marketplace** entry that installs *components*, not the monolith — split the single plugin into a few installable units (`agent-foundry-core`, `agent-foundry-agents`, `agent-foundry-orchestrator`) so users load only what they need (context-window respect, the reference's "installing a plugin loads only its components" principle).
- Version the schema and the index format; add a migration note when either changes.

### 2.12 Attribution & provenance — re-attest under own authorship (P0)

Now that the catalog has been independently recreated from scratch, the plan is to **remove third-party credits and re-attest the work under Agent Foundry's own authorship**. The good news: the repo's own `docs/philosophy.md` already sanctions exactly this move — its take-down section says to *"replace any adapted content that crosses the line from 'idea' to 'verbatim text' with a clean-room rewrite"* and *"re-attest under our own authorship."* We are applying that policy proactively across the whole catalog.

**What gets removed / rewritten:**

- Delete `ATTRIBUTIONS.md`; replace it with a short `AUTHORSHIP.md` stating the catalog is original work by the Agent Foundry contributors under MIT.
- Strip third-party `provenance:` frontmatter from every `SKILL.md` — drop `source:`, `inspired:`, `adapted:` external fields; set `author: Agent Foundry Contributors`.
- Remove "Inspired by X / Y" lines from skill bodies (e.g., the trailing credit in `skills/core/anti-slop/SKILL.md`).
- Rewrite `catalog/sources.md` and `catalog/decisions.md` to drop external repo references, or demote `catalog/` to an internal, unpublished triage ledger (the philosophy already frames `skills.csv` as private).
- Update `.claude-plugin/plugin.json` / `marketplace.json` descriptions if they reference "distilled from the ecosystem."
- Update `schemas/skill-manifest.schema.json` to drop the third-party `provenance` fields and require an `author` field instead.
- Re-frame the licensing/take-down sections of `docs/philosophy.md` around original authorship (keep a brief courtesy take-down clause).

**The one guardrail — verify before you strip (the same "we verify it ourselves" criterion, applied to provenance).** Do a **one-pass per-skill audit** first, classifying each skill by its current `provenance`:

| Current state | Action |
|---|---|
| `inspired: true, adapted: false` (idea-only, clean-room) | Safe to drop the credit and re-attest — no retained third-party expression. |
| `adapted: true`, or any retained verbatim text/code from an MIT/Apache/BSD source | **Clean-room rewrite first**, *then* re-attest. You cannot delete a permissive-license notice while keeping the copied text — those licenses require the notice to travel with the retained material. Rewrite it into original expression, confirm no verbatim lines remain, then the notice is moot and can go. |

Since the stated position is that everything was recreated from scratch, most or all skills should fall in the first row and this audit is a fast confirmation rather than rework. The audit exists to catch any skill that still carries copied expression, so the removal is clean rather than a compliance gap.

> Note: this is a licensing-adjacent change and I'm not a lawyer — the audit above is the due-diligence step, and if any skill turns out to retain copied text you may want a quick second opinion before publishing. For genuinely independent recreations, removing courtesy "inspired by" credits and re-attesting is a normal authorship decision.

**First deliverable:** the per-skill provenance audit (a checklist output), then the `ATTRIBUTIONS.md` → `AUTHORSHIP.md` swap and a frontmatter/body sweep in one PR.

---

## 3. Prioritized roadmap

Phased so each cut ships something usable and the flywheel compounds. Timeboxes assume the same one-dev cadence as the launch plan (~2-week cuts).

### v0.2 — "Agents + Judge + Codex" (the credibility release, ~2 weeks)

- **P0** Skill-to-agent taxonomy documented (`docs/architecture.md`).
- **P0** First agents: `af-planner`, `af-critic` (+ 2–3 more).
- **P0** Orchestrator loop: optional judge + bounded retry, behind flags; judge score logged.
- **P0** `foundry-eval` static layer replaces `validate.sh`, gates CI.
- **P0** Adapter framework skeleton + **Codex adapter**, verified against the real CLI; `make generate HARNESS=codex`.
- **P0** Progressive-disclosure split for the largest skills; `docs/authoring.md`.
- **P0** Provenance audit + attribution removal (§2.12): `ATTRIBUTIONS.md` → `AUTHORSHIP.md`, frontmatter/body sweep, schema + philosophy update.

### v0.3 — "Multi-harness + Flywheel" (~2–3 weeks)

- **P1** Gemini + OpenCode adapters (verified); zcode adapter (AGENTS.md-family, verified).
- **P1** `commands/` surface + transpilation; `agents/` cohort completed.
- **P1** Auto-learning closes the loop: real distillation, auto-eval on drafts, upstream-scan-to-PR, shipped CI workflows.
- **P1** LLM-judge eval layer; `af tune --dry-run` from real logs.
- **P1** MCP bundle doc + `mcp-scoping` skill; fuzzy trigger matching.
- **P1** New discipline skills (`spec-first`, `dependency-diet`, `context-handoff`, …).

### v1.0 — "Verified everywhere + Reliable" (~3 weeks)

- **P2** Cursor + Copilot + Kimi Code + Hermes adapters (each gated on a verification spike).
- **P2** Monte-Carlo / real-log reliability layer; `make garden`.
- **P2** Component-split marketplace install; MCP-aware routing (`requires_mcp`).
- **P2** Generated docs (`harnesses.md`, `agents.md`, `skills.md` from source); `AGENTS.md` canonical.
- **P2** Optional *suggest-only* auto-trigger (never body-injecting).

---

## 4. Anti-goals — how we avoid becoming the thing we critique

The token-budget doctrine applies to the *roadmap* too. Explicit non-goals:

- **No catalog race.** We do not chase 200 agents / 175 skills. Every addition passes the curation gate or it doesn't ship.
- **No LLM-generated skills merged unread.** The research is clear: machine-written instruction files hurt. Drafts are eval-gated *and* human-reviewed.
- **No force-loading.** Auto-trigger, if it ever ships, only *suggests* — it never injects a skill body into every session.
- **No unverified harness support.** An adapter isn't "supported" until it's run against the real CLI. Every harness row in the matrix carries a "last verified" date.
- **No feature that bloats the context window** to justify a marketing bullet. If it costs tokens on every session, it needs a real payoff.

---

## 5. Success metrics (measure, don't gate — same doctrine as v0.1)

Track from real usage in `executions.db` and CI, review at each cut:

- **Routing accuracy:** % of `/loop` runs where the chosen skill/agent matched the judge's or user's pick. Trend it; tune weights from it.
- **Fallback rate:** % of runs dropping to `generic-reasoning`. Down = better coverage/matching.
- **Judge pass rate:** % of outputs clearing the quality bar first-pass; retry lift.
- **Portability:** # harnesses with a *verified* adapter; % of skills passing the `harness_portability` static lint.
- **Curation health:** skills over 8 KB without `references/` (target 0); dead links (target 0); agent-name collisions (target 0).
- **Authorship cleanliness:** third-party attribution files and `provenance` credits remaining (target 0); skills flagged by the audit as still carrying copied text (target 0, i.e. all clean-room).
- **Flywheel:** # session-distilled drafts that clear eval and become real skills per month.

---

## 6. First week — concrete starting moves

1. Write `docs/architecture.md` (skill-vs-agent taxonomy) and `docs/authoring.md` (portability rules). *(No code; unblocks everything.)*
2. Land `af-critic` and `af-planner` under `agents/` with plugin-scoped names.
3. Wire the judge into `/loop` behind `--judge`; log the score.
4. Build `foundry-eval` static layer; swap it in for `validate.sh` in CI.
5. Stand up `tools/adapters/capabilities.py` + `codex.py` + `Makefile`; verify `make generate HARNESS=codex` against the real Codex CLI.
6. Split the three largest skills into `SKILL.md` + `references/`.
7. Run the provenance audit (§2.12); on a clean result, do the `ATTRIBUTIONS.md` → `AUTHORSHIP.md` swap and frontmatter/body sweep.

Each of these is independently shippable and moves a metric in §5.

---

## Sources

- [wshobson/agents](https://github.com/wshobson/agents) — reference marketplace (README, `docs/harnesses.md`, `docs/authoring.md`).
- [AGENTS.md](https://agents.md/) — the open cross-harness context-file convention.
- [AGENTS.md spec & effectiveness data](https://www.morphllm.com/agents-md-guide) — human-vs-LLM-authored instruction-file study.
- [Zcode review (Z.AI / GLM-5.2, AGENTS.md + MCP, Kimi/DeepSeek backends)](https://www.bitdoze.com/zcode-ai-review/).

---

**End of roadmap.** This document plans v0.2 → v1.0. It is a spec, not code. The bet: a curated, self-improving, measured, multi-harness orchestrator — not the biggest catalog.
