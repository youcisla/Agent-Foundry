---
name: session-distill
description: "At session end, auto-summarize what was learned into a structured artifact. Captures decisions made, files changed, open questions, and patterns. Use when wrapping up a work session — by hand or triggered by a hook."
version: 0.1.0
license: MIT
provenance:
  author: Youcisla
  source: operational methodology
  inspired: true
---

# Session Distill

Convert a working session into a structured artifact that lives beyond the session.

## When to Use

- End of a work session
- Before context-compaction might happen
- Handing work off to another agent or person
- After a long debug session
- Weekly: distill the week's sessions into one doc

## Output Format

Save to `plans/sessions/YYYY-MM-DD-<short-name>.md`:

```markdown
# Session: YYYY-MM-DD — <short name>

## What we did
- [Concrete change 1]
- [Concrete change 2]

## Decisions made
- **Decision 1**: [what we chose] because [evidence/reasoning]
- **Decision 2**: ...

## Files changed
- `path/to/file` — [one-line description]
- `path/to/other` — ...

## Open questions
- [Question that came up but we punted on]
- [Question for next session]

## Patterns observed
- [Reusable insight: "when X happens, do Y because Z"]
- [Anti-pattern we fell into: ...]

## Next session
- [Concrete next action]
- [Person/agent who should pick this up]
```

## How to Write Each Section

### What we did
Bullets, not prose. Each bullet = one concrete thing. If you can't make it concrete, drop it.

### Decisions made
The format `**Decision**: ... because ...` is mandatory. The "because" is the part that matters. Without it, you don't know what to revisit.

### Files changed
Include paths and one-line descriptions. This becomes the audit trail.

### Open questions
Questions you didn't answer. They go to the next session's `plans/sessions/` file. Don't lose them.

### Patterns observed
The most valuable section. This is what makes the session reusable:
- Reusable patterns go to `skills/optional/<draft-name>/SKILL.md` (use `knowledge-extract` to draft)
- Anti-patterns we fell into → write to `plans/anti-patterns.md` so we don't repeat

### Next session
Specific, not vague. "Pick up the open questions" is not specific. "Implement the retry logic for the webhook handler per `plans/sessions/2026-07-20-distill.md#open-questions`" is.

## When to Run

| Trigger | Why |
|---------|-----|
| End of work session | Capture context before it fades |
| Before context-compaction | Preserve the most important things |
| After a long debug | Record what worked |
| Before handoff | Other agent/person needs the context |
| Weekly (Friday) | Distill the week into one doc |

## Auto-trigger Option

Add to your hooks config:

```json
{
  "hooks": {
    "SessionEnd": [
      {
        "matcher": "*",
        "hooks": [{
          "type": "command",
          "command": "bash ~/.claude/skills/agent-foundry/hooks/session-distill.sh"
        }]
      }
    ]
  }
}
```

The hook reads the current transcript and writes the structured artifact.

## Anti-patterns

- "I'll remember it" — you won't
- Writing a wall of prose (no signal)
- Decisions without "because" (can't revisit them)
- Skipping open questions (they vanish)
- No patterns observed (the most valuable section missed)

## Verification Checklist

- [ ] Output file is in `plans/sessions/YYYY-MM-DD-<name>.md`
- [ ] All sections filled (or explicitly "none")
- [ ] Every decision has a "because"
- [ ] Every open question has a specific next action
- [ ] At least one pattern observed (or "no patterns")
