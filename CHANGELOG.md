# Changelog

## 0.1.0 — 2026-07-20

Initial release.

**Core skills (5):**
- `prompt-discipline` — adapted from multica-ai/andrej-karpathy-skills (MIT)
- `context-optimization` — inspired by mksglu/context-mode (MIT) + headroomlabs-ai/headroom (MIT)
- `anti-slop` — inspired by Leonxlnx/taste-skill (MIT) + JuliusBrussee/caveman (MIT)
- `plan-before-code` — adapted from obra/superpowers (MIT)
- `session-closeout` — inspired by thedotmack/claude-mem (Apache-2.0), REMvisual/claude-handoff (MIT), and KKKKhazix/khazix-skills/neat-freak (MIT)

**Optional skill:**
- `design-language` — inspired by pbakaus/impeccable (MIT) + emilkowalski/skills/apple-design (MIT)

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
