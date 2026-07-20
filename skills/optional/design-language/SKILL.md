---
name: design-language
description: Apply Apple-grade UI polish principles — restraint, coherence, intention,
  hierarchy through scale, negative space, motion that means. Use when generating
  UI, design systems, components, or marketing surfaces.
version: 0.1.0
license: MIT
provenance:
  inspired: true
author: Agent Foundry Contributors
---

# Design Language

A skill for when you generate UI. Six principles. Apply on every visual output.

## The 6 principles

### 1. Restraint over decoration

If a visual element has no function, remove it. A border with no purpose is a wall. A shadow on every card is noise.

### 2. Coherence over variety

One type scale. One spacing scale. One motion language. A page with 4 fonts is chaos. A page with 1 font and 4 weights is a system.

### 3. Intention over default

Every default (system font, #3b82f6 blue, 16px base) is a missed opportunity. Pick a reason. "Why this color?" should have a one-sentence answer.

### 4. Hierarchy through scale

The primary action is bigger and higher-contrast than the secondary. Not "primary has a gradient, secondary doesn't." Size and weight carry the hierarchy.

### 5. Negative space is content

24px padding isn't empty — it's a visual breath that makes the adjacent content readable. Plan the empty.

### 6. Motion means something

Transitions answer "why did this change?" — not "look at me." A modal slides because it appeared in the user's mental model as elevated content. Linear motion is the AI tell. Use cubic-bezier.

## The test

Show the design to someone for 3 seconds. Ask "what does this do?"

- Specific answer (e.g., "manage my repos") → good
- "It's a dashboard" / "It's a platform" → generic AI
- "I don't know" → restart with intent

## Concrete defaults

- **Type:** 1 display + 1 body. Scale 1.125 or 1.25, 4-5 steps.
- **Spacing:** 4px base, 4-7 steps. Never arbitrary 13px.
- **Color:** 1-2 accent hues max. Backgrounds and grays fill the rest.
- **Motion:** <300ms. Cubic-bezier curves. Respect `prefers-reduced-motion`.
- **Accessibility:** WCAG AA contrast minimum (4.5:1 text, 3:1 UI). Visible focus rings. Keyboard navigation.

## When to skip

- Internal tools where polish doesn't matter
- Backend / CLI work (not visual)
- The user wants a 1:1 clone of an existing design (replicate, don't redesign)


## Anti-patterns

- Skipping verification when the change "feels small"
- Reasoning by analogy without a real example
- Acting on a claim you have not verified this session
- Choosing speed over accuracy when accuracy is what the task requires


## Verification Checklist

- [ ] The claim or action has been verified against a live source
- [ ] The output matches the request's scope (no scope creep)
- [ ] Slop markers are absent (filler, hedging, emoji headers)
