# Agent Foundry – Competitive Improvement Plan (v0.3 lens)

> Planning document. Benchmarks Agent Foundry against `affaan-m/ECC` and `ruvnet/ruflo`, and specifies the external-reference purge.
> Last updated: 2026-07-20. Companion to `docs/improvement-plan.md` (v0.2 → v1.0 roadmap).

---

## 0. Snapshot — where the repo actually is

- **Local is ahead of GitHub.** Local `main` is at v0.2-pre (`agents/af-critic`, `agents/af-planner`, `scripts/foundry-eval.py`, `scripts/provenance-audit.py`, `AUTHORSHIP.md`). GitHub `main` still shows v0.1. **Push before anything else** so reviewers see the real surface.
- **The §2.12 cleanup was half-done.** The commit created `AUTHORSHIP.md` and *ran* the provenance audit — result: **30/30 skills `credit_only` (clean-room), 0 review-required** — but it never stripped the traces. External references are still live across `catalog/`, `CHANGELOG.md`, 25 skills' `provenance:` frontmatter, `docs/`, `plans/PLAN.md`, two optional skill *directory names*, and the scripts. That audit result is the green light the earlier guardrail required — the purge in §4 is now safe to execute in full.

---

## 1. The two competitors — what they are, honestly

Both are large, mature, and impressive. Neither is our template. Read them for ideas, not scope.

### `affaan-m/ECC` — "harness-native operator system"

Closest in *shape* to us (curated, harness-native, MIT + hosted Pro). Much larger: **60 agents, 232 skills, 75 command shims, 7 harnesses**, Anthropic-hackathon pedigree. Its genuinely strong ideas:

| ECC capability | The idea worth stealing |
|---|---|
| **Selective / manifest-driven install** (`install-plan.js`, `install-apply.js`, state store, profiles `minimal/core/full`, `--with capability:X`, `--without baseline:hooks`) | Install *only* what you need — the token/context doctrine applied to installation. |
| **`npx ecc consult "security reviews"`** | An advisor that maps a plain-English need → matching components + preview/install command. |
| **Lifecycle CLI** (`doctor`, `repair`, `list-installed`, `uninstall --dry-run`, `status --markdown`) | Operational maturity: self-diagnose, self-repair, portable status handoff. |
| **Hook runtime controls** (`ECC_HOOK_PROFILE=minimal\|standard\|strict`, `ECC_DISABLED_HOOKS`, `ECC_SESSION_START_MAX_CHARS`, context `off`) | Tune hook strictness/verbosity per environment without editing files. |
| **Instincts / continuous-learning-v2** (confidence scoring, `/instinct-import\|export`, `/evolve` → cluster into skills, `/prune`) | A graded, self-improving memory layer on top of session extraction. |
| **Contexts** (`dev.md` / `review.md` / `research.md` dynamic system-prompt modes) | Swap a small mode-context instead of bloating the base prompt. |
| **Verification loops / eval-harness** (checkpoint vs continuous, grader types, pass@k) | Productized eval as a first-class workflow. |
| **AgentShield** security scan (config surface: CLAUDE.md, settings, MCP, hooks, agents; 102 rules; red-team/blue-team/auditor; CI exit codes) | Static + adversarial security review of the *agent config itself*. |

### `ruvnet/ruflo` — "multi-agent orchestration nervous system"

A different universe: **100+ agents, 33 plugins, ~314 MCP tools, swarms, federation**. Mostly out of scope for us, but three small ideas are gold:

| Ruflo capability | The idea worth stealing (and only this) |
|---|---|
| **`ruflo verify`** — cryptographically prove installed bytes match a signed witness | Supply-chain integrity for a `curl \| bash` public launch. Small, high-trust. |
| **Two clearly-scoped install paths** (plugin-lite = slash commands only, no MCP; CLI = full loop) with an explicit surface-area table | Kills the #1 support problem (stacked/duplicate installs) by being blunt about what each path gives you. |
| **`STATUS.md` / benchmarks** ("is-it-ready" / "is-it-fast" docs) | Honest, current capability counts and a repro'd benchmark — trust through transparency. |

**Everything else in Ruflo — swarms, federation, HNSW vector memory, SONA neural learning, GOAP planner, 12 background workers, multi-provider routing at scale — is explicitly out of scope for us** (§5 anti-goals). It's a company; we're a curated toolkit.

---

## 2. Doctrine check — borrow vs refuse

Run every idea through the token-budget doctrine (`docs/philosophy.md`): small skills, no force-loading, no duplication, no context bloat. Our edge stays **curation + a measured runtime + restraint** — the opposite of catalog sprawl.

| Borrow (doctrine-compatible) | Refuse (betrays the doctrine) |
|---|---|
| Selective install + profiles | 232 skills / 100 agents catalog race |
| `consult` advisor (reuses our planner/daemon) | Swarms, federation, consensus topologies |
| Lifecycle CLI (`doctor`/`status`/`repair`) | HNSW/AgentDB vector memory subsystem |
| Hook runtime controls | SONA neural learning, ReasoningBank |
| Instincts as a graded upgrade to our existing flywheel | GOAP A\* planner, 12 background workers |
| Contexts (mode injection) | Hosted Pro / GitHub App / billing |
| Deepen `foundry-eval` into verification loops | Web UI / dashboard GUI |
| `af verify` signed-manifest integrity | Multi-provider routing "at scale" |
| Config-surface security scan (`af scan`, static) | Rust control-plane rewrite (their `ecc2/`) |
| Two-path install clarity + `STATUS.md` | Rules layer (our disciplines already cover it) |

---

## 3. Borrow-and-better — prioritized, sized, doctrine-checked

Each is deliberately smaller and cleaner than the reference's version. Priority: **P0** (next cut), **P1** (v0.3), **P2** (v1.0).

**P0 — Selective install + profiles (beats ECC by being simpler).** Add `minimal` / `core` / `full` profiles and `--with`/`--without` to `install.sh` + a manifest the indexer already half-implies. We have the index; ECC bolted a whole `install-plan.js` state store on top. We can do it with the index + a tiny profile map. *Why now:* our single monolithic install is the weakest UX gap versus both refs.

**P0 — `af consult "<need>"` advisor.** This is `af plan` pointed at *components* instead of prompts. The planner already scores skills against text; extend it to return "install these / enable this MCP." Near-zero new code, uniquely ours because we have a runtime ECC has to fake with a static script.

**P0 — Lifecycle CLI: `af doctor`, `af status`, `af repair`.** `doctor` = health-check config + index + daemon + API key. `status --markdown` = portable snapshot from `executions.db` (routing accuracy, fallback rate, judge pass rate). `repair` = re-index + rewrite config defaults. We already log everything; this is surfacing it.

**P1 — Instincts as a graded flywheel upgrade.** We already have `session-distill` → `auto-extract` → draft skill. Add ECC's missing middle: a confidence score per extracted pattern (seeded from `executions.db` success signals), and `af evolve` to cluster high-confidence instincts into a skill draft — which then runs through `foundry-eval` before human review. Fuses their instinct idea with our measurement edge.

**P1 — Hook runtime controls.** `AF_HOOK_PROFILE=minimal|standard|strict`, `AF_DISABLED_HOOKS`, `AF_SESSION_CONTEXT=off`. Direct doctrine fit (the "low-context path"). Cheap.

**P1 — `af verify` (from Ruflo).** Ship a signed manifest of file hashes; `af verify` proves the installed tree matches. Real trust lever for `curl | bash`. Small.

**P1 — Deepen `foundry-eval` into verification loops.** We have the static layer. Add the LLM-judge layer (reuse `af-critic`) and checkpoint-vs-continuous modes with pass@k reporting. This is the wshobson `plugin-eval` / ECC `eval-harness` analog — but fused with our real logs.

**P2 — `af scan` (config-surface security, static).** A lean AgentShield analog: scan our own `plugin.json`, hooks, MCP config, and skill frontmatter for injection/secret/permission red flags. Static only; CI exit code. No red-team agent theatre.

**P2 — Contexts (mode injection).** `contexts/dev.md|review.md|research.md` — small mode prompts swapped in on demand. Only if a real need shows up; otherwise skip (our disciplines already carry most of this).

**P2 — Two-path install clarity + `STATUS.md`.** Document plugin-lite vs full-CLI surface areas in one blunt table (Ruflo's best doc move), and add a `STATUS.md` with honest current capability counts.

---

## 4. External-reference purge — concrete execution (audit-cleared)

The provenance audit already cleared all 30 skills as `credit_only` / clean-room, so removing courtesy credits and re-attesting is a normal authorship decision. This is the exact file-by-file plan. It touches **11 tracked files + 25 skill frontmatters + 2 skill directory renames + generated artifacts**.

### 4a. Skill frontmatter (25 files)

- Strip the `provenance:` block from every `skills/**/SKILL.md`. Replace with `author: Agent Foundry Contributors`.
- Update `schemas/skill-manifest.schema.json`: remove the `provenance` object; add required `author` (string).
- Update `scripts/validate.sh`: stop requiring `provenance`; require `author` instead.
- Update `scripts/indexer.py` (drop `provenance` field from the index record) and `scripts/auto-extract.sh` (drop the `provenance:` template block).

### 4b. Rename the two externally-named skills

- `skills/optional/claude-mem-persistent-memory/` → `skills/optional/persistent-memory/`
- `skills/optional/headroom-token-compression/` → `skills/optional/token-compression/`
- Rewrite each `SKILL.md` body and `name:` to drop the external project name. Update `skills/index.json`, `CHANGELOG.md`, and any cross-references.

### 4c. Catalog

- `catalog/sources.md`, `catalog/skills.csv`, `catalog/decisions.md`: remove all external-repo rows/URLs. Two options — **(a)** delete the external-tracking columns and keep these as an *internal design-rationale* log written in our own terms ("the plan→spec→approve gate," not "obra/superpowers"), or **(b)** delete `sources.md` + `skills.csv` entirely and fold any surviving rationale into `decisions.md`. Recommend (a) for the rationale value, (b) for `skills.csv` (it's purely an external triage ledger).
- `catalog/state.json`: it's the upstream-scan hash map keyed by external URLs — delete it (see 4e).

### 4d. Docs

- `docs/philosophy.md`: rewrite the licensing gate + take-down + "Why MIT" sections around **original authorship**. Drop the `ATTRIBUTIONS.md` and "inspired by" model; keep a one-line courtesy take-down clause.
- `docs/auto-learning.md`: the upstream-scan examples name `obra/superpowers` and `pbakaus/impeccable` — remove or replace with generic placeholders; see 4e for the mechanism itself.
- `docs/architecture.md` (line ~109): drop the `provenance` frontmatter mention; say `author`.
- `docs/authoring.md` (line ~33): remove `provenance: []` from the example frontmatter.
- `CHANGELOG.md`: rewrite every "inspired by X (MIT)" / "adapted from Y" line to describe the skill **by what it does**, no external names. (This is forward-facing working-file history; see the caveat below re: git history.)
- `INSTALL.md`: scrub the one external reference.
- `plans/PLAN.md`: the original planning doc is saturated with external sources — archive it out of the repo or scrub it fully. Recommend deleting it (superseded by `docs/launch-plan.md` + this file).

### 4e. Retire (or repurpose) the upstream-scan pillar

The "weekly upstream scan" (`scripts/skill-update.sh`, `workflows/skill-update.md`, `catalog/state.json`) exists **only to track external source repos**. With external references gone, it has no subject.

- **Recommended:** retire it. Remove `skill-update.sh`, `workflows/skill-update.md`, `catalog/state.json`, and the `skill-update` wiring from `docs/auto-learning.md`. The auto-learning flywheel keeps its two internal pillars (session-distill → extract → evolve); it loses the external-ingest pillar, which is exactly the intent.

### 4f. Manifests

- `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json`: rewrite descriptions that say "distilled from the best of the ecosystem" → original-authorship phrasing ("a curated, original set of agent-skill disciplines").

### 4g. Verify + lock it shut

- Regenerate `skills/index.json` (drops provenance).
- Add a CI lint — `NO_EXTERNAL_REFS` — a grep gate over tracked files for the external names/URLs; fail the build if any reappear. This makes the purge permanent, not a one-time sweep.
- Re-run `scripts/provenance-audit.py` → expect 0 provenance blocks remaining.

### The one honest caveat

Scrubbing **working files** is straightforward and complete. **Git history is not** — every past commit still contains the old `provenance` blocks and `ATTRIBUTIONS.md`. If "remove any trace" must include history, that's a separate `git filter-repo` rewrite of a public repo, which invalidates existing clones/forks and PRs. My recommendation: scrub working files now (this plan), and only rewrite history if you have a specific reason — the working tree is what users install and read. For genuinely independent, audit-cleared recreations, forward-facing removal is the normal and sufficient step.

---

## 5. Roadmap slot, metrics, anti-goals

**Sequencing.** This slots as **v0.3** after the v0.2 items in `docs/improvement-plan.md` land. Order within v0.3: (1) push local → GitHub; (2) run the §4 purge + `NO_EXTERNAL_REFS` lint; (3) P0 borrows (selective install, `consult`, lifecycle CLI); (4) P1 borrows.

**New success metrics** (add to `improvement-plan.md` §5):
- External references in tracked files: **target 0** (enforced by `NO_EXTERNAL_REFS`).
- Skills carrying `provenance:`: **target 0**; skills with `author:`: **100%**.
- Install footprint: median files installed under `minimal` profile vs `full` (prove selective install works).
- `af doctor` green-rate on fresh macOS/Ubuntu installs.

**Anti-goals (explicit — these are what make us *not* ECC/Ruflo):** no swarms, no federation, no vector-memory subsystem, no neural/SONA learning, no GOAP planner, no background-worker fleet, no hosted Pro/billing, no web UI, no Rust rewrite, no catalog race. If an idea needs a subsystem to justify a bullet, it's out.

---

## 6. First moves this session (on your go)

1. **Push** local v0.2-pre to GitHub `main`.
2. **Execute §4 purge** — it's audit-cleared; I can do the frontmatter sweep, renames, catalog/doc/CHANGELOG scrub, upstream-scan retirement, and add the `NO_EXTERNAL_REFS` lint in one reviewable pass.
3. Stub the **P0 borrows** (`install` profiles, `af consult`, `af doctor/status`) as the v0.3 opener.

Each is independently shippable. The purge (2) is the one you asked for and the one that's now unblocked by the audit.

---

## Sources

- [`affaan-m/ECC`](https://github.com/affaan-m/ecc) — README (install profiles, `consult`, lifecycle CLI, hook controls, instincts, AgentShield, verification loops).
- [`ruvnet/ruflo`](https://github.com/ruvnet/ruflo) — README (`ruflo verify`, two install paths, STATUS/benchmarks; swarms/federation/memory noted as out-of-scope for us).
- Internal: `scripts/provenance-audit.py` output (30/30 `credit_only`), `docs/philosophy.md` (token-budget doctrine), `docs/improvement-plan.md` (v0.2 → v1.0 roadmap).

---

**End of competitive plan.** The bet is unchanged: a curated, measured, restrained orchestrator. Borrow the operator-maturity ideas (selective install, advisor, lifecycle, graded learning, verification, integrity). Refuse the subsystems. Remove every external trace and stand on our own authorship.
