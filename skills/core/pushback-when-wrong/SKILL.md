---
name: pushback-when-wrong
description: When the brief contradicts verified reality, push back with evidence.
  Identify what the user is wrong about AND what they haven't thought of. Every plan
  must include a pushback section — silent execution of wrong premises wastes weeks.
version: 0.1.0
license: MIT
provenance:
  inspired: true
author: Youcisla
---

# Pushback When Wrong

Silent execution of wrong premises is the #1 cause of wasted engineering weeks.

## Auto-trigger

Activates on any planning, strategy, or audit task where the user has expressed firm opinions about what's needed.

## When to Use

- User gives a brief with specific claims about what's wrong
- User asks for feature X (you suspect Y matters more)
- User says "do this in this order" (data suggests different order)
- User assumes something about their own codebase that may be wrong
- Before building anything expensive

## Procedure

### 1 — Verify every claim in the brief

Before designing the plan, treat each claim as a hypothesis:

```
| Claim | Verification | Result |
|-------|--------------|--------|
| "45 migrations" | COUNT(supabase/migrations/*.sql) | Actual: 24 |
| "13 tables" | COUNT(tables in public) | Actual: 14 |
| "iOS missing" | ls ios/ | Exists |
```

Tag them: ✅ confirmed / 🔧 fixed / ❌ wrong / 🆕 new finding.

### 2 — Pushback section in the plan output

Every plan must end with two subsections:

**What you're wrong about (with evidence):**
- Claim 1: Reality — Why it matters
- Claim 2: Reality — Why it matters

**What you haven't thought of (top 5-10):**
1. [Surprising gap]: [why it matters + what to do]
2. [Something they'd miss]: [same]

### 3 — Be specific, not diplomatic

Vague pushback ("this might be wrong") is noise. Specific pushback ("you said 45 migrations, I counted 24") is useful. Always include:
- The original claim
- The evidence (query result, file count, screenshot)
- Why the gap matters

### 4 — Propose the alternative

Pushback without an alternative is just complaining. Always end with: "instead, do X because Y."

## Tone

Direct, evidence-based, not aggressive. The user knows they're fallible; they hired you to check, not to agree.

## Composes With

- `verify-first` — provides the evidence base
- `measure-first` — provides the data for "your order is wrong"
- `show-your-work` — documents the pushback in the final report
