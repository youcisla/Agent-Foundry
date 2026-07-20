# Auto-Learning System

The plugin gets better the more you use it. Three mechanisms:

1. **Session-end hook** — every session produces a structured artifact
2. **Weekly upstream scan** — detects new versions of upstream skills
3. **On-demand extraction** — distill a session into a new skill draft

All three are wired through simple bash scripts in `scripts/` and `hooks/`. None require a specific harness to function — they read inputs and write outputs.

## 1. Session-End Hook (`hooks/session-end.sh`)

### What it does

At session end, reads the transcript (via stdin or `--transcript PATH`) and writes a session-distill artifact at:

```
plans/sessions/YYYY-MM-DD-<short-name>.md
```

The artifact follows the `session-distill` skill format: what we did, decisions made (with "because"), files changed, open questions, patterns observed, next session.

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

**Hermes** (config.yaml):
```yaml
hooks:
  session_end:
    command: bash ~/.claude/skills/agent-foundry/hooks/session-end.sh
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

**Manual invocation** (in any session):
```bash
bash ~/.claude/skills/agent-foundry/hooks/session-end.sh --transcript ./transcript.json
```

### What it writes

The hook writes a placeholder with the raw transcript attached. To get the full distilled form, invoke the `session-distill` skill on the artifact, or manually fill in the sections.

```
plans/sessions/2026-07-20-debug-payment-webhook.md
plans/sessions/2026-07-20-add-e2e-tests.md
plans/sessions/2026-07-20-ship-v0.2.md
```

## 2. Weekly Upstream Scan (`scripts/skill-update.sh`)

### What it does

Once a week, scans every non-skipped upstream source in `catalog/skills.csv` and compares the latest commit hash against `catalog/state.json`. Writes a digest to:

```
plans/updates/YYYY-MM-DD-upstream-scan.md
```

### Wiring per harness

**Host cron** (Sunday 9am):
```cron
0 9 * * 0 cd /path/to/Agent-Foundry && ./scripts/skill-update.sh
```

**GitHub Actions** (`.github/workflows/skill-update.yml`):
```yaml
name: Weekly Upstream Scan
on:
  schedule:
    - cron: '0 9 * * 0'
  workflow_dispatch:

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ./scripts/skill-update.sh
      - uses: actions/upload-artifact@v4
        with:
          name: upstream-digest
          path: plans/updates/
```

**Manual**:
```bash
./scripts/skill-update.sh                # full scan
./scripts/skill-update.sh --dry-run      # preview only
./scripts/skill-update.sh --source URL   # single source
```

### What it writes

A markdown digest of changed sources since last scan. Review manually, then for each:
1. Visit the source repo, review the diff
2. Decide: port, skip, or just update state.json
3. Open a PR if the change is material

```markdown
# Upstream Skill Scan — 2026-07-20



```

### State File

_(This workflow was retired with the external-reference purge.)_

```json
{
  "sources": {


  }
}
```

## 3. On-Demand Skill Extraction (`scripts/auto-extract.sh`)

### What it does

Reads a session doc's "Patterns observed" section, drafts a new skill to `skills/core/draft-<name>/SKILL.md` using the knowledge-extract template, with TODOs for human review.

### Usage

```bash
./scripts/auto-extract.sh plans/sessions/2026-07-20-debug-payment-webhook.md
./scripts/auto-extract.sh --latest        # use most recent session
./scripts/auto-extract.sh --list          # list available sessions
```

### Pipeline

```
1. Read session doc
2. Extract "Patterns observed" section
3. Generate draft directory name from pattern (heuristic)
4. Write skills/core/draft-<name>/SKILL.md with TODOs
5. User reviews, fills in trigger phrase + procedure + anti-patterns
6. Run ./scripts/validate.sh
7. If trigger fires correctly → rename draft-<name>/ to <name>/
8. Add to CHANGELOG and catalog/decisions.md
```

### What it writes

```markdown
---
name: draft-skill
description: "<!-- TODO: trigger phrase here -->..."
version: 0.1.0
license: MIT
provenance:
  author: Youcisla
  source: plans/sessions/2026-07-20-debug-payment-webhook.md
  inspired: true
---

# draft-skill

> Auto-drafted by scripts/auto-extract.sh.
> Review, fill in the trigger phrase, then run ./scripts/validate.sh.

## Source Material
[extracted patterns]

## When to Use
<!-- TODO: 2-3 specific situations -->

## Procedure
<!-- TODO -->
```

## How They Work Together

```
Session work
   ↓
[1] SessionEnd hook fires → plans/sessions/<date>.md created
   ↓
Manual or auto: review patterns
   ↓
[3] auto-extract.sh → skills/core/draft-<name>/SKILL.md
   ↓
Human review + validation
   ↓
Move to skills/core/<name>/ → CHANGELOG + decisions.md
   ↓
Meanwhile, weekly:
[2] skill-update.sh → plans/updates/<date>-upstream-scan.md
   ↓
Review changes → port relevant → update state.json
```

## Installation

```bash
# Copy scripts + hooks into your skills directory
cp -r Agent-Foundry/scripts/* ~/.claude/skills/agent-foundry/scripts/
cp -r Agent-Foundry/hooks/* ~/.claude/skills/agent-foundry/hooks/
chmod +x ~/.claude/skills/agent-foundry/scripts/*.sh
chmod +x ~/.claude/skills/agent-foundry/hooks/*.sh

# Wire into your harness (see above for config)
# Then trigger manually once:
bash ~/.claude/skills/agent-foundry/hooks/session-end.sh --help
./scripts/skill-update.sh --dry-run
./scripts/auto-extract.sh --list
```

## Limitations

- **Session-end hook** depends on the harness passing the transcript via stdin. Some harnesses don't do this — in that case the hook produces an empty artifact. Manual invocation with `--transcript` works around this.
- **Skill-update.sh** is a heuristic. It detects hash changes but doesn't summarize what changed. Review the diff yourself.
- **Auto-extract** writes drafts, not finished skills. Human review is mandatory. The `knowledge-extract` skill describes the full pipeline.

## Anti-patterns

- Treating the hook output as a finished session-distill (it's a placeholder — fill in manually or invoke `session-distill`)
- Auto-porting every upstream change (you'll drown)
- Auto-extracting from sessions without reading the draft (junk in, junk out)
