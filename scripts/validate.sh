#!/usr/bin/env bash
# validate.sh - lint every SKILL.md
# Rules (from PLAN.md §2):
#   - Required frontmatter: name, description, version, author
#   - description <= 500 chars
#   - File <= 150 lines
#   - author is present (original authorship attestation)
set -e

# Auto-regenerate site data if skills/ or agents/ changed
if [ -n "$(git diff --name-only --cached -- skills/ agents/ 2>/dev/null)" ] || [ -n "$(git diff --name-only -- skills/ agents/ 2>/dev/null)" ]; then
  echo "[validate] skills/ or agents/ changed — regenerating site data..."
  python scripts/gen-site-data.py 2>/dev/null || echo "[validate] gen-site-data skipped (no graphify-out?)"
fi

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_COUNT=0
FAIL=0

# Check if yq is available; fall back to python
if command -v yq >/dev/null 2>&1; then
  PARSE="yq -r"
elif command -v python >/dev/null 2>&1; then
  PARSE="python -c"
else
  echo "FATAL: need yq or python for YAML parsing" >&2
  exit 1
fi

extract_field() {
  local file=$1 field=$2
  awk '/^---$/{c++; next} c==1 && $0 ~ "^"field":" {sub("^"field":[ ]*",""); print; exit}' "$file"
}

check_skill() {
  local file=$1
  local skill_name
  local errors=()

  skill_name=$(basename "$(dirname "$file")")

  # Frontmatter exists?
  if ! head -1 "$file" | grep -q '^---$'; then
    errors+=("missing frontmatter")
  fi

  # Required fields
  local name desc version author
  name=$(awk '/^---$/{c++; next} c==1 && $0 ~ /^name:/{sub(/^name:[ ]*/,""); print; exit}' "$file")
  desc=$(awk '/^---$/{c++; next} c==1 && $0 ~ /^description:/{sub(/^description:[ ]*/,""); print; exit}' "$file")
  version=$(awk '/^---$/{c++; next} c==1 && $0 ~ /^version:/{sub(/^version:[ ]*/,""); print; exit}' "$file")
  author=$(awk '/^---$/{c++; next} c==1 && $0 ~ /^author:/{sub(/^author:[ ]*/,""); print; exit}' "$file")

  [[ -z "$name" ]] && errors+=("missing: name")
  [[ -z "$desc" ]] && errors+=("missing: description")
  [[ -z "$version" ]] && errors+=("missing: version")
  [[ -z "$author" ]] && errors+=("missing: author")

  # description length
  if [[ -n "$desc" ]]; then
    local desc_len=${#desc}
    if (( desc_len > 500 )); then
      errors+=("description too long: ${desc_len} chars (max 500)")
    fi
  fi

  # line count
  local lines
  lines=$(wc -l < "$file")
  if (( lines > 150 )); then
    errors+=("too long: ${lines} lines (max 150)")
  fi

  SKILL_COUNT=$((SKILL_COUNT+1))

  if (( ${#errors[@]} > 0 )); then
    echo "FAIL  $skill_name"
    for e in "${errors[@]}"; do
      echo "        - $e"
    done
    FAIL=$((FAIL+1))
  else
    printf "OK    %-30s %3d lines  desc=%d chars\n" "$skill_name" "$lines" "${#desc}"
  fi
}

echo "Validating skills in $REPO_ROOT/skills/"
echo "---"

while IFS= read -r -d '' file; do
  check_skill "$file"
done < <(find "$REPO_ROOT/skills" -name "SKILL.md" -print0)

echo "---"
echo "Total: $SKILL_COUNT skills, $FAIL failed"

exit $((FAIL > 0 ? 1 : 0))
