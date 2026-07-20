---
name: show-your-work
description: After any complex task (audit, plan, redesign, multi-agent execution), output a separate THINKING TRACE section. Document how you decomposed the problem, what surprised you, what you rejected, and what uncertainties remain. The reasoning is where the learning happens.
version: 0.1.0
license: MIT
provenance:
  author: Youcisla
  source: operational methodology
  inspired: true
---

# Show Your Work

After complex work, the output alone isn't enough — the reasoning behind it is where the real learning happens.

## Auto-trigger

Activates on: "audit", "master plan", "strategy", "analysis", "trace", "thinking", "decompose", "complex task", "reasoning".

## When to Use

- After any multi-source audit or investigation
- After creating a plan with trade-offs
- After discovering something that changed the approach
- When the user asks "how did you reach that conclusion?"
- Any task where the reasoning is as valuable as the result

## Procedure

### 1 — Structure the thinking trace

After the main deliverable, add a `---` separator and a `# THINKING TRACE` section with these subsections:

**1. Trust posture: the brief vs. reality.**
How you treated the user's claims — did you verify or accept? What was wrong / stale? What did you discover that the brief didn't mention?

**2. The moment the plan pivoted.**
What was the single finding that reordered everything? Before finding X, your plan was heading in direction A. After X, it went to direction B. Describe the pivot.

**3. What I rejected, explicitly.**
List every approach you considered and deliberately rejected, with reasoning. This prevents the user from wondering "why didn't you just do X?"

**4. Uncertainties I could not close this session.**
What do you NOT know? What would you verify next time? What's deferred?

**5. Process notes.**
What tooling sequence worked? What would you do differently next time? What did you learn about navigating this codebase?

### 2 — Be honest, not flattering

The trace should reveal genuine uncertainty, not perform confidence. "I assumed X because Y, but I didn't verify" is more useful than "I knew all along."

### 3 — Make it reusable

Future agents reading the trace should be able to apply the same reasoning. Generic praise ("did great work") is noise. Specific method ("checked the API before the DB because X") is signal.

## Anti-pattern

Skipping the trace because the result looks obvious. The trace explains WHY, not WHAT.

## Composes With

- `verify-first` — the trust posture section
- `pushback-when-wrong` — feeds into the pivot section
- `bottleneck-gating` — drives the rejected-approaches section
