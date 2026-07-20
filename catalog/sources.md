# Source License Ledger

Every source we evaluated. Read [philosophy.md](docs/philosophy.md) for the licensing gate rules.

| Source | License | Status in v0.1.0 | What we used |
|---|---|---|---|
| multica-ai/andrej-karpathy-skills | MIT | **adapted** | `prompt-discipline` (4 rules) |
| mksglu/context-mode | MIT | **inspired** | `context-optimization` (sandbox pattern) |
| headroomlabs-ai/headroom | MIT | **inspired** | `context-optimization` (compression proxy) |
| Leonxlnx/taste-skill | MIT | **inspired** | `anti-slop` (anti-pattern catalog) |
| JuliusBrussee/caveman | MIT | **inspired** | `anti-slop` (token compression) |
| obra/superpowers | MIT | **adapted** | `plan-before-code` (brainstorming + spec) |
| thedotmack/claude-mem | Apache-2.0 | **inspired** | `session-closeout` (transcript reconciliation) |
| REMvisual/claude-handoff | MIT | **inspired** | `session-closeout` (handoff notes) |
| KKKKhazix/khazix-skills | MIT | **inspired** | `session-closeout` (6-surface contract) |
| pbakaus/impeccable | MIT | **inspired** | `design-language` (principles) |
| emilkowalski/skills/apple-design | MIT | **inspired** | `design-language` (restraint) |

## v0.1.0 — adapted / inspired sources only

The full source list (120+ links) lives in the project's private triage ledger at `catalog/skills.csv` (gitignored). Public verdicts in `decisions.md`.

## How to add a new source

1. Add row to `catalog/skills.csv` with URL, name, category, license
2. Check license — only MIT / Apache-2.0 / BSD may be adapted; everything else is "inspired by" (rewrite from scratch, attribute as inspiration)
3. Decide verdict: `port` / `inspire` / `skip` / `later`
4. Non-`skip` verdicts get one line in `decisions.md`
5. If porting/inspiring: write skill, add to `ATTRIBUTIONS.md`, add CHANGELOG entry, version bump

See `docs/philosophy.md` for the full intake flow.
