---
name: knowledge-extract
description: "Read a session, conversation, or document and identify reusable patterns. Draft a new skill (or update an existing one). Use when you notice a recurring behavior you want to formalize."
version: 0.1.0
license: MIT
provenance:
  author: Youcisla
  source: operational methodology
  inspired: true
---

# Knowledge Extract

Turn observed behavior into a reusable skill draft.

## The Pipeline

```
Observe → Capture → Distill → Validate → Adopt
```

| Step | Output | Where |
|------|--------|-------|
| Observe | Raw pattern noted in session | `plans/sessions/` |
| Capture | One-paragraph description | `plans/skills/drafts/` |
| Distill | Full SKILL.md draft | `skills/core/draft-<name>/SKILL.md` |
| Validate | Passes validate.sh, trigger fires | same |
| Adopt | Moved to `skills/core/<name>/` | final |

## Step 1 — Observe

Patterns emerge from repetition. Watch for:

- "I always do X before Y"
- "Every time Z happens, I check W first"
- "When the user says A, they usually mean B"
- The same correction applied to two different problems

If you've seen it 3 times, write it down. Not before.

## Step 2 — Capture

One paragraph. No skill yet.

```
plans/skills/drafts/YYYY-MM-DD-<name>.md

## Pattern
[One sentence: what you noticed]

## Why it matters
[Why this is worth formalizing]

## Examples
- [date] [context where it applied]
```

If the capture is still interesting a week later, move to Step 3.

## Step 3 — Distill

Write the full SKILL.md draft. Template:

```markdown
---
name: <verb-or-short-name>
description: "<trigger phrase>. Use when <specific situation>. Inspired by <source>."
version: 0.1.0
license: MIT
provenance:
  source: <where the pattern came from>
  inspired: true
---

# <Name>

<One sentence: what this skill does>

## When to Use
- <Situation 1>
- <Situation 2>

## Procedure

### 1 — <Step>
<Concrete action, not abstract guidance>

### 2 — <Step>
...

## Anti-patterns
- <What NOT to do>

## Verification Checklist
- [ ] <Confirmable outcome>
```

## Step 4 — Validate

```bash
./scripts/validate.sh
```

Test the trigger:

```
Ask the agent: "What skills do you know?"
Look for: <name> in the list with the right description
```

If the trigger doesn't fire, rewrite the description.

## Step 5 — Adopt

Once validated, move from `skills/core/draft-<name>/` to `skills/core/<name>/`. Add to CHANGELOG and catalog/decisions.md.

## What Makes a Good Skill

| ✅ Good | ❌ Bad |
|---------|-------|
| Trigger phrase in description | Vague "useful for X" |
| Concrete procedure steps | Abstract principles |
| Anti-patterns section | Just "best practices" |
| Verification checklist | No success criteria |
| ≤150 lines | 500-line reference doc |

## Update vs Create New

Before creating, search:

```bash
grep -ri "<pattern keyword>" skills/
```

If similar exists:
- Edit it (don't create a near-duplicate)
- Add the new trigger phrase
- Add an anti-pattern if you've fallen into one

## Anti-patterns

- Extracting from one observation (over-fit)
- "Let me skill this up" before 3 data points
- Writing skills you don't actually use
- Skipping validation (broken triggers = invisible skills)
- Naming after tools instead of behaviors (`git-foo` not `commit-then-verify`)
