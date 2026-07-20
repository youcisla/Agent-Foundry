# Agent-Foundry

**One install. A curated, maintained set of agent skills distilled from the best of the ecosystem — harness-agnostic, token-efficient, attributed.**

This is a single repo that gives any agent harness (Claude Code, Codex, Cursor, Gemini CLI, Hermes, OpenCode, …) the distilled know-how of the top 100+ agent-skill repos — without installing 100+ repos.

Every skill is **MIT** (this repo) and **attributed** to its source under its own license. See `ATTRIBUTIONS.md` for the full lineage.

## Why

The community has 2,000+ skills and 50+ MCPs across dozens of repos. Installing them all is impossible. Picking a subset is guesswork. **This repo curates the best of them into a single, maintained, opinionated set** that you can install once and trust.

## What's in v0.1.0

24 **core** skills (always-on for every project, in `skills/core/`):
- `prompt-discipline` — think before acting, minimum viable change, surgical edits
- `context-optimization` — small outputs, sandbox large files, reference not repeat
- `anti-slop` — kill generic AI patterns before they ship
- `plan-before-code` — spec → approval → code; no implementation without a plan
- `plan-then-act` — plan in one sentence before every tool call; write-then-verify; batch independent calls
- `constraint-then-solve` — restate → list unknowns → catalog constraints → solve → self-verify
- `quality-protocol` — unified maximum-quality protocol for every non-trivial task
- `verify-first` — triangle verification meta-discipline; every claim is a hypothesis
- `re-verify-findings` — re-verify audits / bug claims before executing
- `measure-first` — query live data before planning
- `bottleneck-gating` — phase by measured bottleneck, not requested order
- `pushback-when-wrong` — surface discrepancies with evidence
- `read-before-build` — read source before trusting plan claims
- `show-your-work` — output a thinking-trace after complex work
- `landscape-first` — research 5-10 competitors before building
- `session-closeout` — reconcile, document, hand off cleanly
- `api-design` — REST/GraphQL resource modeling, error contracts, pagination, idempotency, versioning
- `cron-troubleshoot` — 7-failure-mode diagnostic checklist for cron jobs
- `e2e-test-strategy` — test pyramid, seeding, auth, flake mitigation
- `feedback-loop` — instrument → measure → review weekly → adjust
- `workflow-decompose` — universal DAG model for any orchestrator
- `automation-pick` — decide whether to automate before automating
- `session-distill` — auto-summarize what was learned at session end
- `knowledge-extract` — read sessions, identify patterns, draft new skills

6 **optional** skill bundles (in `skills/optional/`):
- `design-language` — Apple-grade UI polish
- `chrome-devtools-mcp-bridge` — Google's official browser automation via DevTools Protocol
- `claude-mem-persistent-memory` — cross-session persistent memory
- `headroom-token-compression` — token compression proxy + MCP server
- `funnel-pr-guard` — front-door PR review discipline
- `sql-migration-trio` — migration management with up/down/schema sync

**Total: 30 skills.**

5 **workflow runbooks** (in `workflows/` — not skills, structured guides you copy):
- `ci-cd-vercel.md` — Vercel preview + production deploy with smoke tests
- `e2e-on-pr.md` — Playwright E2E on every PR
- `release-train.md` — weekly release process
- `skill-update.md` — weekly upstream skill scan
- `session-to-skill.md` — session → skill extraction pipeline

One hook (`session-closeout.sh`) that prompts the closeout at end of session.

## Install

```bash
# Auto-detect your harness (Claude Code, Codex, Cursor, Hermes, …)
./scripts/install.sh

# Or pin a specific harness
./scripts/install.sh --harness=claude-code
./scripts/install.sh --harness=codex
./scripts/install.sh --harness=hermes

# Show what install would do without writing
./scripts/install.sh --dry-run
```

See `INSTALL.md` for per-harness details.

## Validate

```bash
./scripts/validate.sh
```

Lints every skill's frontmatter, line count, description length, and provenance field.

## License

This repo: MIT. See `LICENSE`.
Adapted skills: each retains its source license. See `ATTRIBUTIONS.md`.

## Curation

Every source is triaged in `catalog/skills.csv` (private) with a public verdict in `catalog/decisions.md`. New sources go through the same gate: license check → category → port/inspire/skip → skill + attribution + changelog.

See `docs/philosophy.md` for the full curation criteria and contribution flow.
