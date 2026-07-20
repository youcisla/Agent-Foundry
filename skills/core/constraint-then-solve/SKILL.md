---
name: constraint-then-solve
description: Before solving, restate the problem, list unknowns, and catalog every
  constraint. Verify the solution against every constraint at the end. Use on any
  non-trivial reasoning task. Use on any non-trivial reasoning task before jumping
  to a solution.
version: 0.1.0
license: MIT
author: Agent Foundry Contributors
---

# Constraint Then Solve

Every high-quality reasoning trace follows: restate the problem → acknowledge unknowns → catalog constraints → solve → verify against constraints.

## The Protocol

### Step 1: Problem Restatement

Restate what you're being asked in your own words.

```
The user wants [goal]. I know [context]. I don't know [gaps]. I'll infer [assumptions].
```

### Step 2: Missing Context Acknowledgment

"I don't have X, but we can infer Y based on Z." State what you DON'T know before proceeding.

### Step 3: Constraint Catalog

List every constraint explicitly. Numbered. Before any solution generation:

```
Given [context].
Constraints:
1. [A]
2. [B]
3. [C]
Therefore the solution must satisfy: [derived requirements]
```

### Step 4: Output Structure Planning

After reasoning, state what will be produced and how it's organized before writing it.

### Step 5: Self-Verification

After conclusion, verify against every constraint from Step 3. ✓ or ✗ per constraint.

## Structural Format

The reasoning should use:
1. **First-person plural:** "We need to..."
2. **Direct statements about unknowns:** "I don't have the snippet, but..."
3. **Inline correction:** "The answer X doesn't satisfy Y because [reason]. The correct is Z."
4. **No filler:** Every sentence advances reasoning. No meta-commentary about the reasoning process itself.

## When to Use

- Complex code generation with ambiguous specs
- Tasks requiring systematic constraint analysis
- Any work where incorrect assumptions would be costly
- Debugging — use constraint cataloging before any fix attempt

## Verification

After applying: confirm the constraint catalog is numbered, every constraint is verified in the final solution, and unknowns are stated before being inferred.


## Anti-patterns

- Skipping verification when the change "feels small"
- Reasoning by analogy without a real example
- Acting on a claim you have not verified this session
- Choosing speed over accuracy when accuracy is what the task requires


## Verification Checklist

- [ ] The claim or action has been verified against a live source
- [ ] The output matches the request's scope (no scope creep)
- [ ] Slop markers are absent (filler, hedging, emoji headers)
