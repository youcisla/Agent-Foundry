#!/usr/bin/env bash
# auto-extract.sh - On-demand: extract a skill draft from a session or conversation
#
# Reads plans/sessions/<file>.md (or any markdown conversation log),
# extracts the "Patterns observed" section, and asks the agent-foundry
# knowledge-extract skill to draft a new skill.
#
# Usage:
#   ./scripts/auto-extract.sh plans/sessions/2026-07-20-foo.md
#   ./scripts/auto-extract.sh --latest        # use most recent session
#   ./scripts/auto-extract.sh --list           # list available sessions
#
# Output:
#   skills/core/draft-<name>/SKILL.md (requires manual review before promotion)

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SESSIONS_DIR="$REPO_ROOT/plans/sessions"
DRAFTS_DIR="$REPO_ROOT/skills/core"

LIST_ONLY=false
USE_LATEST=false
SOURCE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --list)      LIST_ONLY=true ;;
    --latest)    USE_LATEST=true ;;
    --help|-h)
      grep "^#" "$0" | sed 's/^# \?//'
      exit 0
      ;;
    *) SOURCE="$1" ;;
  esac
  shift
done

# List mode
if [[ "$LIST_ONLY" == "true" ]]; then
  echo "Available session docs in $SESSIONS_DIR:"
  if [[ -d "$SESSIONS_DIR" ]]; then
    ls -la "$SESSIONS_DIR"/*.md 2>/dev/null | awk '{print "  " $NF " (" $5 " bytes)"}'
  else
    echo "  (no sessions directory yet)"
  fi
  exit 0
fi

# Resolve source
if [[ "$USE_LATEST" == "true" ]]; then
  SOURCE=$(ls -t "$SESSIONS_DIR"/*.md 2>/dev/null | head -1)
  [[ -z "$SOURCE" ]] && { echo "no sessions found" >&2; exit 1; }
  echo "Using most recent: $SOURCE"
fi

[[ -z "$SOURCE" ]] && { echo "Usage: $0 <session.md | --latest | --list>" >&2; exit 1; }
[[ ! -f "$SOURCE" ]] && { echo "file not found: $SOURCE" >&2; exit 1; }

echo "Reading $SOURCE..."

# Extract the "Patterns observed" section
PATTERNS=$(awk '/^## Patterns observed/,/^## /' "$SOURCE" | head -50)

if [[ -z "$PATTERNS" || "$PATTERNS" == *"## Patterns observed"* && ${#PATTERNS} -lt 80 ]]; then
  echo "No 'Patterns observed' section found, or it's empty."
  echo "Fill it in first, then re-run."
  exit 1
fi

echo ""
echo "=== Extracted Patterns ==="
echo "$PATTERNS"
echo "=========================="
echo ""

# Generate a draft directory name
NAME=$(echo "$PATTERNS" | \
  grep -oE '`[a-z-]+`' | head -1 | tr -d '`' | sed 's/ /-/g')
[[ -z "$NAME" ]] && NAME="draft-skill"
DRAFT_DIR="$DRAFTS_DIR/draft-$NAME"

echo "Drafting to: $DRAFT_DIR/"
mkdir -p "$DRAFT_DIR"

# Generate the SKILL.md draft using the knowledge-extract template
cat > "$DRAFT_DIR/SKILL.md" <<EOF
---
name: $NAME
description: "<!-- TODO: trigger phrase here -->. Use when <!-- specific situation -->."
version: 0.1.0
license: MIT
author: Agent Foundry Contributors
---

# $NAME

> Auto-drafted by scripts/auto-extract.sh on $(date +%Y-%m-%d).
> Review, fill in the trigger phrase, then run \`./scripts/validate.sh\`.

## Source Material

$PATTERNS

## When to Use
<!-- TODO: 2-3 specific situations -->

## Procedure

### 1 — <!-- TODO -->
<!-- TODO: concrete steps -->

### 2 — <!-- TODO -->

## Anti-patterns
- <!-- TODO: what NOT to do -->

## Verification Checklist
- [ ] <!-- TODO: confirmable outcome -->
EOF

echo "Drafted: $DRAFT_DIR/SKILL.md"
echo ""
echo "Next steps:"
echo "1. Edit the draft (fill in trigger phrase, procedure, anti-patterns)"
echo "2. Run: ./scripts/validate.sh"
echo "3. Test the trigger by asking the agent 'What skills do you know?'"
echo "4. If trigger fires correctly, move to skills/core/<name>/ (rename from draft-)"
echo "5. Add to CHANGELOG and catalog/decisions.md"
