# Session Distill - Details

Deep material that was moved out of the main skill body to keep it under the 150-line cap.

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
