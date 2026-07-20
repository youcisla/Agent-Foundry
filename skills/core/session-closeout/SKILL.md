---
name: session-closeout
description: 'Before ending a session: reconcile changed files, update docs and changelog,
  list loose ends, write a handoff note. Apply at the end of any multi-step project.'
version: 0.1.0
license: MIT
provenance:
  inspired: true
author: Agent Foundry Contributors
---

# Session Closeout

A session that ends without closeout is work that has to be redone. Apply at the end of any multi-step project, before /reset, before stopping for the day, or before handing to someone else.

## The 6 surfaces

Reconcile each before declaring done. Tag with status: `verified` / `pending` / `not-applicable`.

| Surface | Question | Evidence |
|---|---|---|
| **Code** | What did we actually change? | `git diff` + tests passing |
| **Runtime** | Does it actually work? | Live URL, deployed artifact, manual test |
| **Docs** | Can a new person understand what we built? | README, changelog, inline comments |
| **Rules** | Are the constraints the next session will see still correct? | AGENTS.md / CLAUDE.md / hooks |
| **Memory** | Is there anything the next session should know that isn't in code or docs? | Note to self, vault entry |
| **Workspace** | Any untracked files, stale branches, temp dirs? | `git status` clean, no `.tmp` |

If a surface isn't applicable, tag it `n/a` — don't fabricate evidence.

## The handoff note

End every multi-step session with a handoff. Format:

```
## Handoff — <date>

**Done:** [list of completed work, with PR/branch links]
**In progress:** [what was started but not finished]
**Loose ends:** [bugs, tech debt, follow-ups]
**Decisions:** [non-obvious choices and why]
**Next steps:** [what to do first next session, in order]
```

Save it: commit to the repo, paste it as the session's last message, both.

## When to skip

- Single-question Q&A
- Throwaway experiments
- Sessions that produced nothing (deleted the work, no code change)

## When in doubt

Do the closeout. The cost is 2 minutes. The cost of NOT doing it is the next session starting from zero.


## Anti-patterns

- Skipping verification when the change "feels small"
- Reasoning by analogy without a real example
- Acting on a claim you have not verified this session
- Choosing speed over accuracy when accuracy is what the task requires


## Verification Checklist

- [ ] The claim or action has been verified against a live source
- [ ] The output matches the request's scope (no scope creep)
- [ ] Slop markers are absent (filler, hedging, emoji headers)
