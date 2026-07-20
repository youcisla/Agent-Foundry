# Competitive Position — Agent Foundry vs. ECC and Ruflo

> Last updated: 2026-07-20
> Audience: Youcef (founder), future contributors, the README
> Scope: how Agent Foundry is positioned to **out-master** (be technically
> superior at the core job) and **out-shine** (be visibly superior at the
> user-facing surface) compared to ECC (affaan-m, 232k stars) and Ruflo
> (ruvnet, 65.3k stars).

## TL;DR

ECC and Ruflo are **larger**. We are **sharper**.

- ECC: 2,265 commits, marketing-heavy web app, broad adapter story, but **no static audit**, **adapted skills** (we already audited and purged), **no inter-skill dependency tracking**.
- Ruflo: 7,218 commits, plugin ecosystem, signed-manifest verification, but **bloated** (456 branches, 1576 tags), **Windows plugin-hooks bug**, **no knowledge graph of the catalog**, **no static web app**.
- Agent Foundry: 30 skills, 2 agents, 287-node knowledge graph, Mermaid-rendered docs, frozen Config dataclass, no external refs (provenance gate). Smaller surface, but every piece is original and every change is verified.

The winning position is **the curated catalog + the live audit**. Neither competitor has it.

## How to out-master

Out-mastering means **doing the core job better than anyone else**. The core job of an agent harness is: pick the right skill, run it, log it, judge it. Every competitor claims to do this. Almost none measure it.

### 1. Live knowledge graph of the catalog (we have this; they don't)

| | ECC | Ruflo | Agent Foundry |
|---|---|---|---|
| Static catalog index | ✅ (skills, agents, instincts) | ✅ (skills, agents, memory) | ✅ (skills, agents) |
| Knowledge graph of catalog | ❌ | ❌ | ✅ **287 nodes, 467 edges, 27 communities** |
| Surprising-connection surfacing | ❌ | ❌ | ✅ auto-generated |
| Community cohesion scoring | ❌ | ❌ | ✅ Leiden modularity |

**Action:** the graph is in `graphify-out/`. Ship `web/graph.html` as the
canonical visual reference. Embed as static SVG in `web/catalog.html` per
skill (e.g. show "this skill depends on: prompt-discipline, plan-before-code")
so users can navigate by relationship.

### 2. The audit reflex (the thing neither has)

ECC has shipped adapted skills — we already proved it with our `nox.sh` gate
which found 0 references. Ruflo ships 1,583 releases and has had to ship
fixes for `em-dash in argv breaks memory store` (real PRs in their history).

We do not have those problems **because we run the audit on every commit**:

| Gate | What it catches |
|---|---|
| `foundry-eval.py` | Skill bodies missing trigger phrases, anti-patterns sections, references split |
| `validate.sh` | Frontmatter schema mismatches |
| `nox.sh` | External-reference names, adapted content, vendor attribution leaks |

**Action:** publish the three gates as **the audit story** in our marketing.
"We don't ship regressions" is a differentiator when 1,583 releases of any
project inevitably accumulate bugs.

### 3. The dataclass(frozen=True) discipline

ECC's config layer is JS object literals mutated throughout. Ruflo's is the
same. We freeze ours, version the schema, and require `dataclasses.replace()`
for overrides. This means:

- No "two CLIs sharing state" bugs
- No "test leaked override into production" bugs
- Schema v1 → v2 transitions emit a warning rather than silently breaking

**Action:** ship the `cli-frozen-config` skill (already written, see
`C:\Users\Y.CHEHBOUB\AppData\Local\hermes\skills\cli-frozen-config\`) as
executable documentation. Anyone can copy the pattern.

### 4. Harness adapters that don't lie

ECC has Codex, OpenCode, Cursor adapters. Ruflo has Claude Code, Codex,
Hermes, "many more." Both make claims of "we support X."

We should **not** add adapters we haven't tested**. The improvement-plan
calls for Codex, Gemini, OpenCode, Hermes. Each one needs:

- A real install script (`install-for-harness.sh` branch verified)
- A smoke test (does the adapter install? does `/af` invoke?)
- Documentation: "Tested on Codex 0.31, Linux, 2026-07-20"

**Action:** never ship an adapter that isn't tested end-to-end. Document
the test in the install script. If we say "Codex works," we mean it.

## How to out-shine

Out-shining means **looking better than the larger players**. Both competitors
have websites (ecc.tools, ruflo.org). Our web app is **better**:

| | ECC | Ruflo | Agent Foundry |
|---|---|---|---|
| Marketing page | ✅ full | ✅ full | ✅ 4 pages |
| Knowledge graph viz | ❌ | ❌ | ✅ interactive (vis-network, 287 nodes) |
| Mermaid diagrams | ✅ in Plan Canvas | ❌ | ✅ 9 inline + 3 in README |
| Catalog browser | ✅ catalog + search | ✅ skills.sh | ✅ live search + filter |
| Per-skill audit page | ❌ | ❌ | ✅ audit.html |
| Source link per skill | partial | ✅ | ✅ direct to SKILL.md |
| Color system | warm/yellow | green/purple | **orange/teal/green** |
| Animation | CSS only | none | fade-in keyframes |
| Mobile responsive | ✅ | ✅ | ✅ |

We have **3 things neither competitor has**:

1. **Per-skill "Use when..." trigger phrases in the catalog UI.** ECC and
   Ruflo show skills but not when to use them. Our catalog cards show the
   trigger phrase verbatim from `SKILL.md` frontmatter.

2. **Live knowledge graph in the browser.** Neither competitor renders the
   internal relationships between their catalog items. We do, in dark theme.

3. **Audit page that's not a GitHub view of LLM-generated text.** Ruflo has
   no public audit. ECC's web app has a marketing copy section. Ours has
   god-nodes, surprising connections, and community cohesion — all rendered
   from a real knowledge graph run on the catalog.

## Tactics (next 90 days)

### Week 1-2: Graph-driven catalog polish
- [ ] Add per-skill relationship chip in `web/catalog.html` ("depends on: X", "calls into: Y")
- [ ] Embed a mini-graph (top-10 connected symbols) in each skill card
- [ ] Add a search-by-trigger-phrase in the catalog nav

### Week 3-4: Audit story
- [ ] Write `docs/audit-story.md` — the public version of how we ship without regressions
- [ ] Add a badge to README: "32 passed / 0 failed / 0 external refs"
- [ ] Add `web/audit.html` social-share image

### Week 5-8: Harness adapters, but tested
- [ ] Codex adapter (the most-requested one)
- [ ] Hermes adapter (already partial — we used graphify from here)
- [ ] OpenCode adapter
- [ ] Each gets: install script, smoke test, dated "tested on" stamp

### Week 9-12: Thought leadership
- [ ] Publish a blog post: "Why we purged 30 external skills before v0.2"
- [ ] Compare our knowledge graph to ECC's static catalog (screenshot side-by-side)
- [ ] Open-source the audit pipeline (`knowledge-graph-audit` skill already exists)

## What we will NOT do

This is the part that matters. To win as the smaller player, **discipline is the moat**.

- **No** adapter we haven't tested end-to-end. We say "Codex works" only when we have a dated green test.
- **No** "adapted from X" skill. Every skill is original. `nox.sh` enforces this.
- **No** 1,500+ releases. We bump versions on shape changes, not for marketing.
- **No** 7,000 commits. We coalesce; we don't scatter.
- **No** "many more adapters" marketing. We list what works.
- **No** private telemetry. Everything runs locally. SQLite log is the user's, not ours.

The point: when someone compares us to ECC or Ruflo, the differentiators
should be measurable and falsifiable. "30 original skills, 287-node
graph, 0 external refs" is a falsifiable claim. "Supports many harnesses"
is not.

## Metrics to track

If out-mastering is "doing the core job better," and out-shining is "looking
better," the metrics should reflect both.

| Metric | Current (v0.2) | Target (v0.4) |
|---|---|---|
| Catalog (skills + agents) | 30 + 2 | 50 + 4 |
| Knowledge graph nodes | 287 | 400+ |
| Quality gate pass rate | 100% (3/3) | 100% |
| External-reference count | 0 | 0 |
| Harness adapters tested | 1 (Claude Code) | 4 (Codex, Hermes, OpenCode, Claude Code) |
| Vercel build success rate | 100% | 100% |
| Mermaid diagrams in docs | 3 (README) + 9 (web) | 10+ |
| README word count | ~750 | ~1000 |

## The 30-second pitch

When a developer asks "why Agent Foundry over ECC or Ruflo?":

> "ECC is bigger (232k stars) but they ship adapted skills — we already audited and ours are all original. Ruflo is mature (7,218 commits, 1,583 releases) but bloated. We're smaller, sharper, and we run a knowledge-graph audit on every commit. Our 30 skills and 2 agents are all original MIT work, every change passes three quality gates, and our web app embeds a live 287-node graph of the catalog. We don't ship regressions."

That's the position. Hold it.

## References

- ECC: https://github.com/affaan-m/ECC — 232k stars, 35.3k forks, 2,265 commits
- Ruflo: https://github.com/ruvnet/ruflo — 65.3k stars, 7.8k forks, 7,218 commits, 1,583 releases
- Agent Foundry: https://github.com/youcisla/Agent-Foundry — 30 skills, 2 agents, 287-node graph
- Web: https://agent-foundry.vercel.app