# Philosophy

Agent Foundry is a curated, original set of agent-skill *disciplines* — small, reusable rules that teach a model **how to think**, wrapped in a local orchestrator that plans, dispatches, and measures. This document is the "why."

## The token-budget doctrine

We apply the same rules to ourselves that our skills preach:

- **Every skill is small** (≤150 lines, ≤8 KB). Long reference material goes in `references/`, never in the main body.
- **No force-loading.** Skills activate via their own `description` frontmatter trigger. Hooks never inject skill bodies into every session.
- **No duplication.** One idea → one skill. If two skills overlap, merge them.
- **No slop.** No emoji headers, no filler prose, no "in this implementation we..." sentences.

A skills repo about token efficiency that bloats context is self-refuting.

## Original authorship

Every skill, agent, hook, and script here is original work by the Agent Foundry contributors, released under MIT. Each skill carries a single `author` field in its frontmatter; the repo-level statement lives in `AUTHORSHIP.md`. We do not vendor, fork, or republish other projects — we author disciplines from operational experience and hold ourselves to the curation criteria below.

## The curation criteria

A discipline earns a place in the catalog only if:

1. **It captures a non-obvious idea** — not just "use best practices."
2. **The idea is reusable** — fits in one skill body, not project-specific.
3. **We can verify it works** — we use it ourselves before shipping it.
4. **It survives the token budget** — it stays small, or it doesn't ship.

If a candidate fails any of these, it doesn't ship. The rationale for what made the cut lives in `catalog/decisions.md` (internal design notes).

## The intake flow

New idea → draft → verify → ship.

1. Draft the skill from a real, repeated pattern (often via `session-distill` → `knowledge-extract`).
2. Write it small: one `Use when …` trigger, ≤150 lines, action verbs not tool names.
3. Run `scripts/foundry-eval.py` (the quality gate) and `scripts/validate.sh` — must pass.
4. Add a `CHANGELOG.md` entry; bump the version.
5. Self-test: install into a scratch harness and confirm the trigger fires.

## Original-work statement and good-faith review

Everything in this repository is authored by the Agent Foundry contributors. If you believe any material here is genuinely derived from your work, open an issue titled `AUTHORS REVIEW`; we will review in good faith and, where warranted, revise or remove it promptly.

## Why MIT

- We want unrestricted commercial use (teams, companies).
- Skills are short; explicit permission to share removes any ambiguity.
- Authorship is attested per skill via the `author` field — no separate ledger to drift out of date.

## Why one small repo

Our edge is not size. It is:

- **Single install** — one script installs the full set.
- **Curation** — we ship a small, high-signal catalog rather than everything.
- **A measured runtime** — the daemon logs every dispatch, so routing accuracy is a number we track, not a guess.
- **Token-budget awareness** — every skill is small; the repo is small.

We are not trying to be the biggest. We are trying to be the most respectful of your context window.
