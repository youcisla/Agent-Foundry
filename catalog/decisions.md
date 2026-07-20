# Curation Decisions

Every non-`skip` source in v0.1.0, with a one-line public verdict. The full triage ledger (with `skip` and `later` rows) is in `catalog/skills.csv` — private.

## v0.1.0 — ported or inspired into a skill

### Adapted (source content reused under compatible license)

- **multica-ai/andrej-karpathy-skills** (MIT) → `prompt-discipline` — the 4 rules (think, simplify, surgical, goal-driven) are the clearest non-trivial guidance we found. Adapted, not copied, to fit one skill body.
- **obra/superpowers** (MIT) → `plan-before-code` — the "brainstorm → spec → approve → implement" gate is the single most valuable workflow in the ecosystem. Adapted the gate; rewrote the format as a 4-step skill body.

### Inspired (idea adopted, content rewritten from scratch)

- **mksglu/context-mode** (MIT) + **headroomlabs-ai/headroom** (MIT) → `context-optimization` — both are compression systems; we adopt the idea (small outputs, sandbox to files, reference not repeat) but rewrite as one coherent skill rather than port either implementation.
- **Leonxlnx/taste-skill** (MIT) + **JuliusBrussee/caveman** (MIT) → `anti-slop` — both have anti-pattern lists; we synthesize the top categories (filler prose, over-commenting, defensive over-engineering, unnecessary abstractions, emoji headers).
- **thedotmack/claude-mem** (Apache-2.0) + **REMvisual/claude-handoff** (MIT) + **KKKKhazix/khazix-skills/neat-freak** (MIT) → `session-closeout` — all three have closeout/handoff patterns; we adopt the 6-surface reconciliation contract (code, runtime, docs, rules, memory, workspace) and rewrite the handoff format.
- **pbakaus/impeccable** (MIT) + **emilkowalski/skills/apple-design** (MIT) → `design-language` — both articulate restraint / coherence / intention; we synthesize into a 6-principle skill for opt-in use.

## What we explicitly did NOT port

- **anthropics/claude-code** (proprietary) — the harness itself, not a skill source. Tracked for reference only.
- **anomalyco/opencode**, **claude-code-best/claude-code**, **ultraworkers/claw-code**, **1jehuang/jcode** — alternative harnesses / clones. Out of scope for a skills repo.
- **Trading repos** (HKUDS/AI-Trader, TradingAgents, TradingView-API, tradingview-mcp, etc.) — out of v0.1 scope. Tagged `bundle:trading` for v0.3.
- **HuggingFace datasets** — training data, not skill sources. Tagged `later`.

## Why this is fair

Everything adapted is under MIT or Apache-2.0. The full lineage is in `ATTRIBUTIONS.md`. We don't republish whole source repos — we extract the *idea* (one or two key concepts) and rewrite it in our own words, under our own license, with attribution back to the source.

If a source author objects, the verdict flips to `skip` and the skill is removed in the next release. See `docs/philosophy.md` for the take-down flow.
