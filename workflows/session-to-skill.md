# Workflow: Session → Skill Extraction

A reusable runbook for turning a work session into a reusable skill (using the agent-foundry `knowledge-extract` and `session-distill` skills).

## When to Use

- After a long work session
- Noticed a recurring pattern that should be formalized
- Want to convert institutional knowledge into a shareable skill

## Steps

### 1. Distill the Session

At session end, run the `session-distill` skill (or trigger it via hook):

```
What skills do you know? → look for session-distill
Trigger: "session-distill this session"
```

It writes `plans/sessions/YYYY-MM-DD-<name>.md` with:
- What we did
- Decisions made (with "because")
- Files changed
- Open questions
- Patterns observed
- Next session

### 2. Identify a Pattern Worth Extracting

In the session doc, look at the "Patterns observed" section. For each pattern:

| Pattern type | Worth extracting? |
|--------------|-------------------|
| "I always do X before Y" | ✅ Yes |
| "Every time Z happens, I check W" | ✅ Yes |
| "When the user says A, they mean B" | ✅ Yes |
| One-off decision | ❌ No, just a session note |
| Project-specific detail | ❌ No, not reusable |

### 3. Capture the Pattern

`plans/skills/drafts/YYYY-MM-DD-<name>.md`:

```markdown
## Pattern
[One sentence: what you noticed]

## Why it matters
[Why this is worth formalizing — what pain does it prevent?]

## Examples
- 2026-07-15: Used this in the billing refactor (saved 2 hours)
- 2026-07-18: Used this when debugging the auth flow

## Provisional trigger
"<trigger phrase that should activate this skill>"
```

Wait at least a week. If the pattern comes up again, move to Step 4.

### 4. Distill to a Skill

Use the `knowledge-extract` skill:

```
Trigger: "knowledge-extract — draft a skill from this pattern"

Input: the capture from Step 3

Output: skills/core/draft-<name>/SKILL.md
```

The skill draft follows the standard template (frontmatter, when to use, procedure, anti-patterns, verification checklist).

### 5. Validate

```bash
./scripts/validate.sh
```

Then test the trigger:

```
Ask the agent: "What skills do you know?"
Look for: <name> with the right description
```

If the trigger doesn't fire, rewrite the description.

### 6. Adopt or Reject

**Adopt** if:
- Trigger fires correctly
- Procedure is concrete
- Anti-patterns section has real content
- You've used it 3+ times successfully

Move from `skills/core/draft-<name>/` to `skills/core/<name>/`. Add to CHANGELOG and `catalog/decisions.md`.

**Reject** if:
- Trigger is too generic (fires too often)
- Procedure is too project-specific
- One-time use case
- Hard to verify

Delete the draft. Move on.

### 7. Maintain

Quarterly:
- Re-read the skill. Still relevant?
- Update anti-patterns with new ones you've fallen into
- Refine trigger phrase if needed

## Cadence

| When | Task |
|------|------|
| End of every long session | Distill (`session-distill`) |
| When a pattern emerges | Capture (`plans/skills/drafts/`) |
| After 3+ captures of same pattern | Distill to skill |
| After validation passes | Adopt (`skills/core/<name>/`) |
| Quarterly | Review existing skills |

## Anti-patterns

- Skipping distillation (you'll forget)
- Creating a skill from one observation (over-fit)
- Skill with vague trigger phrase (never fires)
- Skill with no anti-patterns section
- Skill with no verification checklist
- Never reviewing existing skills (drift)
