# Auto-Learning System

Agent Foundry gets sharper the more you use it. Two internal mechanisms, both wired through small scripts in `scripts/` and `hooks/`. Neither requires a specific harness — they read inputs and write outputs.

1. **Session-end hook** — every session produces a structured distill artifact.
2. **On-demand extraction** — turn a session's observed patterns into a new skill draft.

Both feed the same flywheel: your real work becomes reusable disciplines, gated by the quality eval before anything is shipped.

## 1. Session-End Hook (`hooks/session-end.sh`)

### What it does

At session end, reads the transcript (via stdin or `--transcript PATH`) and writes a session-distill artifact at:

```
plans/sessions/YYYY-MM-DD-<short-name>.md
```

The artifact follows the `session-distill` skill format: what we did, decisions made (with "because"), files changed, open questions, patterns observed, next session. When the daemon is reachable it produces a filled distillation; otherwise it writes a fillable placeholder with the transcript attached.

### Wiring per harness

**Claude Code** (`~/.claude/settings.json`):
```json
{
  "hooks": {
    "SessionEnd": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "bash ~/.claude/skills/agent-foundry/hooks/session-end.sh"
      }]
    }]
  }
}
```

**Codex** (`~/.codex/settings.json`):
```json
{
  "hooks": {
    "session_end": [{
      "hooks": [{
        "type": "command",
        "command": "bash ~/.claude/skills/agent-foundry/hooks/session-end.sh"
      }]
    }]
  }
}
```

**Manual invocation** (any harness):
```bash
bash ~/.claude/skills/agent-foundry/hooks/session-end.sh --transcript ./transcript.json
```

## 2. On-Demand Skill Extraction (`scripts/auto-extract.sh`)

### What it does

Reads a session doc's "Patterns observed" section and drafts a new skill to `skills/core/draft-<name>/SKILL.md` using the `knowledge-extract` template, with TODOs for human review.

### Usage

```bash
./scripts/auto-extract.sh plans/sessions/2026-07-20-debug-payment-webhook.md
./scripts/auto-extract.sh --latest        # use the most recent session
./scripts/auto-extract.sh --list          # list available sessions
```

### Pipeline

```
1. Read session doc
2. Extract "Patterns observed"
3. Generate a draft directory name
4. Write skills/core/draft-<name>/SKILL.md with TODOs
5. Human fills in the trigger phrase + procedure + anti-patterns
6. Run scripts/foundry-eval.py (quality gate) and scripts/validate.sh
7. If the trigger fires correctly, rename draft-<name>/ to <name>/
8. Add a CHANGELOG entry and a catalog/decisions.md line
```

## How they work together

```
Session work
   ↓
[1] session-end hook → plans/sessions/<date>.md
   ↓
Review "Patterns observed"
   ↓
[2] auto-extract.sh → skills/core/draft-<name>/SKILL.md
   ↓
Human review + foundry-eval gate
   ↓
Promote to skills/core/<name>/ → CHANGELOG + decisions.md
```

## Limitations

- The session-end hook depends on the harness passing the transcript via stdin. Where a harness doesn't, the hook writes an empty artifact — use `--transcript` to work around it.
- `auto-extract` writes drafts, not finished skills. Human review is mandatory. The `knowledge-extract` skill describes the full pipeline.

## Anti-patterns

- Treating the hook output as a finished distillation (it's a placeholder unless the daemon filled it).
- Promoting an auto-extracted draft without reading it (junk in, junk out).
- Shipping a draft that hasn't passed `foundry-eval`.
