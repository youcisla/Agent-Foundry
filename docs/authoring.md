# Authoring Guide

How to write a **portable** skill or agent that works across Claude Code, Codex, Hermes, Gemini, and OpenCode without re-writing for each one.

## Core principles

Three rules, in priority order:

1. **Talk about *actions*, not tools.** Never say `Read` / `Grep` / `Edit` / `TodoWrite` / `Task` in a skill body. Say "check", "find", "review", "verify". This is why Codex skills are deterministic across harness — the body describes intent, the harness maps intent to its own tools.
2. **Stay ≤8 KB / ≤150 lines.** Codex's hard cap. The harness that *doesnt* have a cap still fragments a 12 KB body more than a 6 KB body in the context window. Use `references/` for the deep stuff.
3. **Exactly one trigger phrase.** Something that starts with `Use when...` or `Use PROACTIVELY when...` in the `description`. The description is the only thing the harness can use to decide whether to load your skill.

## Skill structure

```
skills/core/<name>/
├── SKILL.md          # navigation + decision tree + first 3 steps
└── references/       # deep material, loaded on demand
    ├── details.md
    └── examples/
        └── good-vs-bad.md
```

### SKILL.md anatomy

```markdown
---
name: short-kebab-case
description: "Use when [trigger phrase]. [Second sentence clarifying scope]."
version: 0.1.0
license: MIT
author: Agent Foundry Contributors
provenance: []
---

# Skill Name

One sentence. What this skill does.

## When to Use
- Situation 1
- Situation 2

## Procedure

### 1 - First step (concrete action)
### 2 - Second step
### 3 - Third step

## Anti-patterns
- What NOT to do, with reason

## Verification Checklist
- [ ] Confirmable outcome 1
- [ ] Confirmable outcome 2
```

The Procedure section is **the most important part**. Each step is a concrete action the model can take, not a vague principle.

### Action verbs

Prefer:
- "verify", "check", "find", "review", "audit"
- "extract", "transform", "restructure"
- "compare", "rank", "prioritize"
- "draft", "rewrite", "summarize"
- "decompose", "synthesize", "decide"

Avoid:
- `Read`, `Edit`, `Write`, `Grep`, `Glob` (tool names)
- `TodoWrite`, `Task` (task-tool names)
- "the agent should", "Claude must" (no third-person reference)
- "use the X tool to do Y" (hooks you to that tools API)

## Trigger phrase patterns

The description field is **the entire interface** between your skill and the harness. Get it right.

### Good trigger phrases

```
"Use when reviewing a PR that touches authentication, billing, or data migrations."
"Use PROACTIVELY when the user shares a stack trace, error message, or failing test."
"Use when choosing between building from scratch vs integrating an existing library."
"Use when the user says 'isn't working', 'broken', 'why is this' — symptoms not causes."
```

### Bad trigger phrases

```
"Useful skill."                    # no trigger
"For working with code."           # too broad
"Use this often."                  # no condition
"A great skill that does X."       # marketing copy
"Use when needed."                 # tautology
"The best practice for doing X."   # no condition
```

## Agent structure

Agents live in `agents/<name>/AGENT.md`.

```
agents/af-critic/
├── AGENT.md        # role description + behavior
└── examples/
    └── invocation.md   # sample invocations
```

### AGENT.md anatomy

```markdown
---
name: af-critic
description: "Scoring judge for completed task outputs. Use after /af or any loop result."
model: opus
tools: []
version: 0.1.0
author: Agent Foundry Contributors
---

# af-critic - The Judge

Role: score the output of an executed task on three axes.

## When to Run

- After `/af <task>` completes
- Before accepting a multi-file change
- When the user asks "is this good?"

## Scoring rubric

| Axis | Score range | Definition |
|------|-------------|------------|
| Correctness | 0-1 | Does the output satisfy the stated request? |
| Slop | 0-1 (inverted) | How much generic-AI filler / filler prose / emoji-header soup? |
| Scope | 0-1 | Does the output stay within the scope of the request? |

## Output format

Return a JSON object:
```json
{
  "correctness": 0.92,
  "slop": 0.05,
  "scope": 0.88,
  "verdict": "pass" | "revise" | "reject",
  "notes": "One sentence explaining the lowest-scoring axis."
}
```

## Behavior

1. Read the task definition.
2. Read the output produced.
3. Score each axis on the rubric above.
4. Output the JSON. No prose.
```

### Naming

Plugin-scoped names: `af-critic`, `af-planner`, `af-researcher`. Never `critic`, `default`, `worker`, `explorer` (those are harness built-ins).

## The progressive-disclosure pattern (Codex 8 KB cap)

Harnesses cap skill body sizes. Codex is 8 KB / ~150 lines. Pre-empt this:

1. The `SKILL.md` has the navigation, decision tree, and first 3 procedure steps.
2. Anything procedural that does NOT need to be loaded always goes into `references/details.md`.
3. Examples go into `references/examples/`.

If you find yourself writing `references to X for the full docs see Y`, that means Y needs to be in `references/`, not in the body.

## Model tiers

Pick the smallest tier that does the job:

- `haiku` — short, mechanical (format conversion, validation, scoring)
- `sonnet` — most skills; default
- `opus` — synthesis, judgment, planning under uncertainty
- `inherit` — use the parent's model (default for most skills)

If your skill makes a judgment call (does this look right?) it might need `sonnet` not `haiku`. If it just enforces a format it should be `haiku`.

## Putting it together: a checklist

Before you commit a new skill or agent:

- [ ] Description has exactly one `Use when...` or `Use PROACTIVELY when...` trigger phrase
- [ ] Body is ≤150 lines / ≤8 KB; heavy content moved to `references/`
- [ ] Procedure steps are concrete actions, not principles
- [ ] No tool names (`Read`, `Grep`, `Edit`) in the body
- [ ] Anti-patterns section has at least 2 entries with reasons
- [ ] Verification checklist has at least 2 confirmable outcomes
- [ ] For agents: name is plugin-scoped (`af-*`), model tier is appropriate, tool allowlist is minimal
- [ ] `scripts/foundry-eval` passes (run it; gate is in CI)

If any of these fails, fix it before merging.
