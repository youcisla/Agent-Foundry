#!/usr/bin/env bash
# nox.sh — NO_EXTERNAL_REFS lint gate
# Scans tracked files for known external-reference names. Fails the build if any reappear.

set -e
FAILED=0

NOX_TERMS=(
  "multica-ai"
  "Leonxlnx"
  "JuliusBrussee"
  "obra/superpowers"
  "mksglu"
  "thedotmack"
  "pbakaus"
  "headroomlabs"
  "emilkowalski"
  "fable-5-traces"
  "reasoning-corpus"
  "Glint-Research"
  "SupraLabs"
  "claude-mem-persistent"
  "headroom-token-compression"
)

# Only scan tracked files (excludes gitignored catalog/, generated index.json, etc.)
for term in "${NOX_TERMS[@]}"; do
  HITS=$(git ls-files | xargs grep -ali "$term" 2>/dev/null || true)
  if [ -n "$HITS" ]; then
    echo "FAIL: '$term' found in tracked files"
    echo "$HITS"
    FAILED=1
  fi
done

if [ "$FAILED" = "1" ]; then
  echo ""
  echo "nox.sh: External references found in tracked files. Gate fails."
  exit 1
else
  echo "nox.sh: 0 external references in tracked files. Gate passes."
  exit 0
fi
