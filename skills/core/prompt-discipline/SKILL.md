---
name: prompt-discipline
description: "Enforce the four coding rules — think before acting, minimum viable change, surgical edits, stay on the stated goal. Use on every non-trivial task. Adapted from multica-ai/andrej-karpathy-skills (MIT)."
version: 0.1.0
license: MIT
provenance:
  source: multica-ai/andrej-karpathy-skills
  license: MIT
  adapted: true
  url: https://github.com/multica-ai/andrej-karpathy-skills
---

# Prompt Discipline

The four rules that prevent the most common LLM coding mistakes. Apply on every task beyond a typo fix.

## 1. Think before acting

State assumptions, surface tradeoffs, push back. One short preamble is worth an hour of wasted work.

- If a simpler approach exists, say so.
- If the user gave a detailed spec, skip — spec is the thinking.
- If the task is ambiguous, **stop and ask** one question. Not five.
- Never start coding with "Sure, I can..." — start with the assumption + the plan.

## 2. Minimum viable change

No features beyond what was asked. No abstractions for single-use code. No "flexibility" that wasn't requested. No error handling for impossible scenarios.

If 200 lines can be 50, rewrite it. The senior-engineer test: *would a reviewer say this is overcomplicated?*

## 3. Surgical edits

Touch only what you must. Match existing style, even if you'd do it differently. If you notice unrelated dead code, **mention it** — don't delete it.

The test: every changed line traces to the user's request. If it doesn't, delete it.

## 4. Stay on the stated goal

Transform the task into verifiable success criteria. *"Make X work"* → *"the test for case Y passes."* Strong criteria let you loop independently.

For multi-step tasks, state a brief plan before the first action:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

## When to skip these rules

- One-line typo fix.
- Pure Q&A, no code change.
- The user explicitly says "just do it, don't overthink" — then go fast and check at the end.
