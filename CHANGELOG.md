# Changelog

## 0.1.0 — 2026-07-20

Initial release.

**Core skills (16 in `skills/core/`):**

Adapted (from MIT/Apache-2.0):
- `prompt-discipline` — adapted from multica-ai/andrej-karpathy-skills (MIT)
- `plan-before-code` — adapted from obra/superpowers (MIT)

Inspired (idea adopted, content rewritten):
- `context-optimization` — inspired by mksglu/context-mode (MIT) + headroomlabs-ai/headroom (MIT)
- `anti-slop` — inspired by Leonxlnx/taste-skill (MIT) + JuliusBrussee/caveman (MIT)
- `session-closeout` — inspired by thedotmack/claude-mem (Apache-2.0), REMvisual/claude-handoff (MIT), and KKKKhazix/khazix-skills/neat-freak (MIT)
- `plan-then-act` — inspired by Glint-Research/Fable-5-traces (CC-BY-4.0 dataset)
- `constraint-then-solve` — inspired by SupraLabs/reasoning-corpus-4K-5M-v1 (CC-BY-4.0 dataset)

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
- `design-language` — inspired by pbakaus/impeccable (MIT) + emilkowalski/skills/apple-design (MIT)

**Total: 17 skills shipped.**

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
