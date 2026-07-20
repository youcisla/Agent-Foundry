---
name: anti-slop
description: Kill generic AI patterns before they ship — filler prose, over-commenting,
  defensive over-engineering, unnecessary abstractions, emoji headers. Apply on any
  UI, copy, or code that will be read by a human. Use when reviewing or writing UI
  text, code comments, READMEs, or any output a human will read.
version: 0.1.0
license: MIT
provenance:
  inspired: true
author: Agent Foundry Contributors
---

# Anti-Slop

Generic AI output has tells. Catch them before the user does.

## The five categories

1. **Filler prose.** "It's worth noting that...", "In this implementation, we...", "Let me explain how this works..." — delete on sight. If a sentence doesn't add information, cut it.
2. **Over-commenting.** Code that explains what it does (`// loop through array` above `for (const x of arr)`). The code *is* the comment. Comments should explain *why*, not *what*.
3. **Defensive over-engineering.** Try/catches around things that can't throw. Null checks on values that just got validated. Validation of external API inputs you control. If a failure mode can't happen, don't code for it.
4. **Unnecessary abstractions.** Helper functions called once. Config objects for two settings. Factory classes with one implementation. If it's only used once, inline it.
5. **Emoji headers.** "🚀 Quick Start", "✨ Features", "💡 Tip" — emoji in docs screams "AI wrote this." Strip them.

## The test

Before declaring done, read your output and ask: **"If a human wrote this, would their coworker assume they were trying too hard?"**

If yes, cut.

## When in doubt

Show your output to a fresh pair of eyes (a subagent with no context). If they say "this is generic AI," trust them and rewrite.

## When to skip

- The user is asking for a specific style and slop is what they want (rare, but it happens — internal brainstorming, first drafts).
- The output is throwaway (a debug print, a test).


## Anti-patterns

- Skipping verification when the change "feels small"
- Reasoning by analogy without a real example
- Acting on a claim you have not verified this session
- Choosing speed over accuracy when accuracy is what the task requires


## Verification Checklist

- [ ] The claim or action has been verified against a live source
- [ ] The output matches the request's scope (no scope creep)
- [ ] Slop markers are absent (filler, hedging, emoji headers)
