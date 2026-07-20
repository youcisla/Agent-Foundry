---
name: bottleneck-gating
description: Phase plans by measured bottleneck, not by requested order. Each phase
  has a gate condition (metric must move before proceeding). Never monetize or beautify
  a loop that doesn't complete.
version: 0.1.0
license: MIT
provenance:
  inspired: true
author: Youcisla
---

# Bottleneck Gating

The right sequence is: measure → fix the bottleneck → gate → fix the next bottleneck.

## Auto-trigger

Activates on any planning, roadmap, or execution task.

## When to Use

- Creating any multi-phase plan
- Asked to redesign before the core loop works
- Asked to bill before users get value
- Prioritizing a backlog
- Deciding what to build next

## Procedure

### 1 — Find the bottleneck

Ask: what is the single number that caps everything else?
- 86% of cases die at step 1 → funnel is the bottleneck
- 3 users ever saw the core value → don't optimize that page yet
- 0 customers → don't build billing features

### 2 — Phase by what unlocks the next thing

Structure phases as:
```
Phase 0: Stop the bleeding (trust leaks, data, safety)
Phase 1: Fix the bottleneck (activate, convert, retain)
Phase 2: Monetize the working loop (only if Phase 1 succeeds)
Phase 3: Polish the experience (only if Phase 2 works)
Phase 4: Consolidate (only if later phases ship)
```

### 3 — Define gates between phases

Every phase transition has a measurable condition:

```
Gate to Phase 2: case_created → reflection_submitted ≥ 50% for 2 consecutive weeks
If gate fails: investigate why, fix the cause, re-measure. Do not proceed.
```

Gates protect against building on a broken foundation. If the gate isn't met, the next phase won't help.

### 4 — State the gate in the plan

Every multi-phase plan must explicitly state:
- The bottleneck being fixed in each phase
- The metric that proves the gate is met
- The trigger for moving to the next phase

## Anti-pattern

Building billing features when no users complete the core flow. Building redesign when retention is the actual problem. Optimizing for power users when activation is the bottleneck.

## Composes With

- `measure-first` — provides the bottleneck measurement
- `verify-first` — confirms the gate metric actually moved
