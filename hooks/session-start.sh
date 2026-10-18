#!/usr/bin/env bash
# SessionStart bootstrap: inject a compact skill index so the agent knows what
# exists without loading every skill body. Opt out with AGENT_FOUNDRY_NO_BOOTSTRAP=1.
set -euo pipefail

if [ "${AGENT_FOUNDRY_NO_BOOTSTRAP:-0}" = "1" ]; then
  exit 0
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INDEX="$ROOT/hooks/skill-index.txt"

cat <<'EOF'
<agent-foundry>
Agent Foundry skills are available. If there is even a 1% chance one applies to
the task, invoke it before acting. Prefer one focused skill over many.
EOF

if [ -f "$INDEX" ]; then
  cat "$INDEX"
else
  echo "(skill index missing: run scripts/gen-skill-index.py)"
fi

cat <<'EOF'
</agent-foundry>
EOF
