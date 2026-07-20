---
name: knowledge-extract
description: Read a session, conversation, or document and identify reusable patterns.
  Draft a new skill (or update an existing one). Use when you notice a recurring behavior
  you want to formalize.
version: 0.1.0
license: MIT
author: Agent Foundry Contributors
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

create the full SKILL.md draft. Template:

```markdown
---
name: <verb-or-short-name>
description: "<trigger phrase>. Use when <specific situation>."
version: 0.1.0
license: MIT
author: Agent Foundry Contributors
---

# <Name>

<One sentence: what this skill does>

## Anti-patterns

- Skipping verification when the change 'feels small'
- Reasoning by analogy without a real example
