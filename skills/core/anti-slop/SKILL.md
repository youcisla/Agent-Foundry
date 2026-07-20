---
name: anti-slop
description: "Kill generic AI patterns before they ship — filler prose, over-commenting, defensive over-engineering, unnecessary abstractions, emoji headers. Apply on any UI, copy, or code that will be read by a human. Inspired by Leonxlnx/taste-skill (MIT) and JuliusBrussee/caveman (MIT)."
version: 0.1.0
license: MIT
provenance:
  source:
    - Leonxlnx/taste-skill
    - JuliusBrussee/caveman
  license: MIT
  adapted: false
  inspired: true
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
