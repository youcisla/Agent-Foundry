# ATTRIBUTIONS

Every skill in this repo is either:
- **Adapted** (from MIT/Apache-2.0/BSD source, with attribution), or
- **Inspired** (idea adopted, content rewritten from scratch, with attribution), or
- **Original** (authored by Youcisla from operational experience; no upstream source).

The licensing gate is in `docs/philosophy.md`. The full source ledger is in `catalog/sources.md`. The private triage ledger is in `catalog/skills.csv` (gitignored).

## v0.1.0 — adapted sources

| Source | License | Used for | License link |
|---|---|---|---|
| multica-ai/andrej-karpathy-skills | MIT | `prompt-discipline` | https://github.com/multica-ai/andrej-karpathy-skills/blob/main/CLAUDE.md |
| obra/superpowers | MIT | `plan-before-code` | https://github.com/obra/superpowers |

## v0.1.0 — inspired sources (ideas only, content rewritten)

| Source | License | Idea used for |
|---|---|---|
| mksglu/context-mode | MIT | sandbox tool outputs to files |
| headroomlabs-ai/headroom | MIT | compress before LLM |
| Leonxlnx/taste-skill | MIT | anti-pattern categories |
| JuliusBrussee/caveman | MIT | token compression patterns |
| thedotmack/claude-mem | Apache-2.0 | transcript reconciliation |
| REMvisual/claude-handoff | MIT | handoff note format |
| KKKKhazix/khazix-skills | MIT | 6-surface closeout contract |
| pbakaus/impeccable | MIT | design principles |
| emilkowalski/skills/apple-design | MIT | restraint philosophy |

## v0.1.0 — original skills (authored by Youcisla)

These skills were synthesized from operational use across multiple projects, not adapted from a single source. They are released under this repo's MIT license with no upstream attribution required.

| Skill | Provenance |
|---|---|
| `verify-first` | Triangle verification methodology, distilled from repeated audit work |
| `re-verify-findings` | Pattern of re-checking stale audit claims before executing |
| `measure-first` | Live-data-first planning discipline |
| `bottleneck-gating` | Phase-gating by measured bottleneck, not requested order |
| `pushback-when-wrong` | Discrepancy surfacing discipline with evidence |
| `read-before-build` | Read-source-before-trusting-plan discipline |
| `show-your-work` | Thinking-trace format for complex outputs |
| `landscape-first` | Competitive research protocol before building |

## v0.1.0 — optional skills — adapted sources

| Source | License | Used for |
|---|---|---|
| ChromeDevTools/chrome-devtools-mcp | Apache-2.0 | `chrome-devtools-mcp-bridge` |
| thedotmack/claude-mem | Apache-2.0 | `claude-mem-persistent-memory` |
| headroomlabs-ai/headroom | MIT | `headroom-token-compression` |

## v0.1.0 — optional skills — original (authored by Youcisla)

| Skill | Provenance |
|---|---|
| `funnel-pr-guard` | Generalized from Sentio project's front-door PR review discipline |
| `sql-migration-trio` | Generalized from Sentio project's migration-trio pattern |

## v0.1.0 — inspired-by dataset patterns (ideas only, content rewritten)

| Source | License | Idea used for |
|---|---|---|
| Glint-Research/Fable-5-traces | CC-BY-4.0 (dataset) | plan-first + write-verify loop + batching (`plan-then-act`) |
| SupraLabs/reasoning-corpus-4K-5M-v1 | CC-BY-4.0 (dataset) | problem restatement + constraint catalog + self-verify (`constraint-then-solve`, `quality-protocol`) |

The datasets contain agent traces / thought traces — they are not source code. We extracted structural patterns (e.g., "every Bash call has a description field", "constraints are cataloged before solving") and rewrote the protocols in our own voice. No verbatim text was copied.

## Take-down

If you maintain any of the above and want your source removed from our `inspired` category, open an issue on this repo with "ATTRIBUTIONS REMOVAL" in the title. We will:
1. Remove the inspired credit
2. Replace any adapted content that crosses the line from "idea" to "verbatim text"
3. Re-attest under our own authorship

The v0.1.0 release is intentionally narrow — 12 sources cited, 150-line cap per skill, all adaptations reviewed against the originals before merge.
