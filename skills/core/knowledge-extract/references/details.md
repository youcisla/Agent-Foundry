# Knowledge Extract - Details

Deep material that was moved out of the main skill body to keep it under the 150-line cap.

## When to Use
- <Situation 1>
- <Situation 2>

## Procedure

### 1 — <Step>
<Concrete action, not abstract guidance>

### 2 — <Step>
...

## Anti-patterns
- <What NOT to do>

## Verification Checklist
- [ ] <Confirmable outcome>
```

## Step 4 — Validate

```bash
./scripts/validate.sh
```

Test the trigger:

```
Ask the agent: "What skills do you know?"
Look for: <name> in the list with the right description
```

If the trigger doesn't fire, rewrite the description.

## Step 5 — Adopt

Once validated, move from `skills/core/draft-<name>/` to `skills/core/<name>/`. Add to CHANGELOG and catalog/decisions.md.

## What Makes a Good Skill

| ✅ Good | ❌ Bad |
|---------|-------|
| Trigger phrase in description | Vague "useful for X" |
| Concrete procedure steps | Abstract principles |
| Anti-patterns section | Just "best practices" |
| Verification checklist | No success criteria |
| ≤150 lines | 500-line reference doc |

## Update vs Create New

Before creating, search:

```bash
grep -ri "<pattern keyword>" skills/
```

If similar exists:
- modify it (don't create a near-duplicate)
- Add the new trigger phrase
- Add an anti-pattern if you've fallen into one

## Anti-patterns

- Extracting from one observation (over-fit)
- "Let me skill this up" before 3 data points
- Writing skills you don't actually use
- Skipping validation (broken triggers = invisible skills)
- Naming after tools instead of behaviors (`git-foo` not `commit-then-verify`)
