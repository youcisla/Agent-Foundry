---
name: landscape-first
description: 'Before building anything in a competitive space, research 5-10 competitors:
  pricing, UX patterns, positioning, weaknesses. Extract what to steal, adapt, or
  avoid. Every project should do this before the first feature commit.'
version: 0.1.0
license: MIT
provenance:
  inspired: true
author: Youcisla
---

# Landscape First

Never build in a vacuum. Research what competitors do, how they price it, and where they're weak.

## Auto-trigger

Activates on "competitor", "market", "landscape", "research", "build feature", "launch", "redesign", "pricing", "positioning".

## When to Use

- Before building a new product or feature
- When asked to design pricing or positioning
- Before a redesign (what patterns work in the space?)
- When evaluating product-market fit
- Quarterly: re-pull the battlecard (markets move fast)

## Procedure

### 1 — Identify 5-10 relevant competitors

Search broadly:
- "pairs with: our category"
- "competitors to: our product"
- "alternatives to: use case"
- "category + app", "category + pricing"

Include: market leaders, fast-growing challengers, adjacent players.

### 2 — Research each competitor (browser)

For each, capture in a table:

| Player | What it is | Model & price | UX strength | Weakness |
|--------|------------|---------------|-------------|----------|
| Name | 1-line summary | Pricing + subscriptions | What they do better | What they miss |

Use browser tools to navigate their pages, check pricing, signup flow.

### 3 — Extract 3 patterns to steal

Not everything is worth copying. Identify the 3 proven UX patterns that consistently show up — these are validated by the market.

### 4 — Extract 3 gaps to fill

What do users complain about? What features are missing? What pricing tiers don't exist?

### 5 — Document the battlecard

Save the table + extracted patterns as `competitive/<date>-landscape.md`. Reference it in every planning session.

## Anti-pattern

Building in a vacuum because "we know our users." You know YOUR users. The landscape shows you who's winning them away.

## Composes With

- `measure-first` — supplements with usage data of your own product
- `pushback-when-wrong` — surfaces "users want X because competitor Y has it"
- `bottleneck-gating` — landscape gaps feed the bottleneck analysis
