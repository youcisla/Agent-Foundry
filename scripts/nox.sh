#!/usr/bin/env bash
# nox.sh — NO_EXTERNAL_REFS gate.
# Fails the build if any known external-project name appears in a TRACKED file.
# Rationale: the catalog is original work; nothing here credits or vendors other repos.
set -euo pipefail

# Denylist of external project/handle names that must never appear in tracked files.
NOX_TERMS=(
  "multica-ai" "andrej-karpathy" "karpathy-skills"
  "Leonxlnx" "taste-skill"
  "JuliusBrussee" "caveman"
  "obra/superpowers" "superpowers-v"
  "mksglu" "context-mode"
  "thedotmack" "claude-mem"
  "REMvisual" "claude-handoff"
  "KKKKhazix" "khazix"
  "pbakaus" "impeccable"
  "headroomlabs" "headroom-token-compression" "claude-mem-persistent"
  "emilkowalski" "apple-design"
  "Glint-Research" "fable-5-traces"
  "SupraLabs" "reasoning-corpus"
  "wshobson" "affaan-m" "affaan/" "ruvnet" "ruflo" "claude-flow"
  "ATTRIBUTIONS.md"
)

# Files allowed to mention these terms (this gate itself only).
ALLOW_REGEX='^scripts/nox\.sh$'

FAILED=0
for term in "${NOX_TERMS[@]}"; do
  # -F fixed-string, -i case-insensitive, over tracked files only.
  HITS="$(git ls-files -z | xargs -0 grep -Fil "$term" 2>/dev/null || true)"
  HITS="$(printf '%s\n' "$HITS" | grep -vE "$ALLOW_REGEX" || true)"
  HITS="$(printf '%s\n' "$HITS" | sed '/^$/d')"
  if [ -n "$HITS" ]; then
    echo "FAIL: '$term' found in tracked file(s):"
    printf '  %s\n' $HITS
    FAILED=1
  fi
done

if [ "$FAILED" = "1" ]; then
  echo ""
  echo "nox.sh: external references found in tracked files. Gate FAILS."
  exit 1
fi
echo "nox.sh: 0 external references in tracked files. Gate passes."
