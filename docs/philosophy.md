# Philosophy

This repo exists because the agent-skill ecosystem is fragmented. 2,000+ skills, 50+ MCPs, dozens of harnesses — all in different corners, with no shared curation. **Agent-Foundry is the curation layer.** We forge/refine skills from many sources into a single maintained set.

## The token-budget doctrine

We apply the same rules to ourselves that we preach:

- **Every skill is small** (≤150 lines). Long reference material goes in `references/`, never in the main body.
- **No force-loading.** Skills activate via their own `description` frontmatter trigger. Hooks never inject skill bodies into every session.
- **No duplication.** One source → one skill. If two skills overlap, merge.
- **No slop.** No emoji headers, no filler prose, no "in this implementation we..." sentences.

A skills repo about token efficiency that bloats context is self-refuting.

## The licensing gate

Before porting anything from a source repo, check its license:

| Source license | Action |
|---|---|
| MIT / Apache-2.0 / BSD | **Adapt.** Reuse the content, attribute the idea. |
| GPL / AGPL | **Do NOT copy text or code** into this MIT repo. Learn the *idea*, rewrite from scratch, attribute as "inspired by". |
| No license file | **Treat as all-rights-reserved.** Idea only, full rewrite, attribute as "inspired by". |
| Proprietary | **Skip.** Don't even use the idea without permission. |

We track every source's license in `catalog/sources.md`. The private triage ledger at `catalog/skills.csv` records the verdict for each.

## The curation criteria

A source gets ported only if:

1. **License is OK** (per the gate above).
2. **It captures a non-obvious idea** — not just "use best practices."
3. **The idea is reusable** — fits in one skill body, not project-specific.
4. **We can verify it** — we read the source ourselves, not just the README.

If a source fails any of these, it goes to `later` or `skip` in the CSV. Public verdict in `decisions.md`.

## The intake flow

New source → triage → skill (or not) → version bump.

1. Add row to `catalog/skills.csv` with URL, name, category, license.
2. License check (see gate above).
3. Verdict: `port` / `inspire` / `skip` / `later`.
4. Non-`skip` verdicts get one line in `catalog/decisions.md`.
5. If ported/inspired: write skill, add to CHANGELOG, version bump.
6. Run `./scripts/validate.sh` — must pass.
7. Self-test: install in a scratch dir, confirm a harness picks it up.

## Take-down

If you maintain a source whose methodology appears here and you believe the content should not be distributed, open an issue titled `AUTHORS REVIEW`.

We respect take-down requests. If any skill or agent contains material you believe is derived, we will review and, where applicable, remove or replace it in a timely manner.

We respect attribution and take-down. We will not fight you on this.

## Why MIT

This repo's license is MIT because:

- Skills are short — copyright is weak, but we want explicit permission to share.
- We want commercial use (teams, companies) to be unrestricted.
- Attribution is required years removed — we no longer maintain a separate ATTRIBUTIONS.md. Every skill has a single `author` field in its frontmatter.

## Why one repo, not 10

The community has 100+ skill repos. We are one more. Our edge:

- **Single install** — `git clone` + one script = full set.
- **Curation** — we say no to 90% of sources. Most repos say yes to everything.
- **Harness-agnostic** — works on Claude Code, Codex, Cursor, Hermes, Gemini CLI, OpenCode. Same skills.
- **Token-budget aware** — every skill is small. The repo is small.

We are not trying to be the biggest. We are trying to be the most respectful of your context window.
