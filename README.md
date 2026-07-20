# Agent-Foundry

**One install. A curated, maintained set of agent skills distilled from the best of the ecosystem — harness-agnostic, token-efficient, attributed.**

This is a single repo that gives any agent harness (Claude Code, Codex, Cursor, Gemini CLI, Hermes, OpenCode, …) the distilled know-how of the top 100+ agent-skill repos — without installing 100+ repos.

Every skill is **MIT** (this repo) and **attributed** to its source under its own license. See `ATTRIBUTIONS.md` for the full lineage.

## Why

The community has 2,000+ skills and 50+ MCPs across dozens of repos. Installing them all is impossible. Picking a subset is guesswork. **This repo curates the best of them into a single, maintained, opinionated set** that you can install once and trust.

## What's in v0.1.0

Five **core** skills (always-on for every project):
- `prompt-discipline` — think before acting, minimum viable change, surgical edits
- `context-optimization` — small outputs, sandbox large files, reference not repeat
- `anti-slop` — kill generic AI patterns before they ship
- `plan-before-code` — spec → approval → code; no implementation without a plan
- `session-closeout` — reconcile, document, hand off cleanly

One **optional** skill bundle:
- `design-language` (under `skills/optional/`) — Apple-grade UI polish

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
