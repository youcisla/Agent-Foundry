#!/usr/bin/env bash
# install.sh — Thin bash wrapper that delegates to install.js (Node).
# Mirrors ECC's architecture: one Node entry, this shell wrapper just dispatches.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"

# Convert MSYS/Git Bash POSIX path to Windows path (Node resolves Windows paths natively)
case "$(uname -s 2>/dev/null || echo Windows)" in
  MINGW*|CYGWIN*|MSYS*)
    if command -v cygpath >/dev/null 2>&1; then
      INSTALL_JS="$(cygpath -w "$SCRIPT_DIR/install.js")"
    else
      INSTALL_JS="$SCRIPT_DIR/install.js"
    fi
    ;;
  *)
    INSTALL_JS="$SCRIPT_DIR/install.js"
    ;;
esac

# Find Node — prefer Node 18+, fall back to system node
NODE=""
if command -v node >/dev/null 2>&1; then NODE="node"
elif command -v node18 >/dev/null 2>&1; then NODE="node18"
elif command -v nodejs >/dev/null 2>&1; then NODE="nodejs"
fi

if [[ -z "$NODE" ]]; then
  echo "Node.js >=18 is required. Install from https://nodejs.org/" >&2
  exit 1
fi

# Disable Git Bash path auto-conversion before exec (MSYS_NO_PATHCONV=1)
# Forward all args to the Node script
exec "$NODE" "$INSTALL_JS" "$@"