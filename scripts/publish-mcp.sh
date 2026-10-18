#!/usr/bin/env bash
# publish-mcp.sh — publish server.json to the official MCP Registry.
#
# Prerequisites (one-time):
#   1. The PyPI package for this version must exist:
#        python -m build && python -m twine upload dist/*
#   2. Install the publisher:
#        https://github.com/modelcontextprotocol/registry
#   3. Authenticate:
#        mcp-publisher login github
#
# Usage:
#   bash scripts/publish-mcp.sh            # validate + publish
#   bash scripts/publish-mcp.sh --dry-run  # validate only

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
cd "$ROOT"

fail() { echo "  ✗ $*" >&2; exit 1; }

DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --help|-h) sed -n '2,18p' "$0"; exit 0 ;;
    *) fail "unknown arg: $arg" ;;
  esac
done

command -v node >/dev/null 2>&1 || fail "node not found"
if command -v python >/dev/null 2>&1; then PY=python
elif command -v python3 >/dev/null 2>&1; then PY=python3
else fail "python not found"; fi
command -v curl >/dev/null 2>&1 || fail "curl not found"

echo "=== Version alignment ==="
VERSION=$(node -p "require('./package.json').version")
SERVER_VERSION=$($PY -c "import json;print(json.load(open('server.json'))['version'])")
PKG_VERSION=$($PY -c "import json;print(json.load(open('server.json'))['packages'][0]['version'])")
[[ "$VERSION" == "$SERVER_VERSION" ]] || fail "server.json version $SERVER_VERSION != package.json $VERSION (run python scripts/sync-version.py)"
[[ "$VERSION" == "$PKG_VERSION" ]] || fail "server.json package version $PKG_VERSION != package.json $VERSION (run python scripts/sync-version.py)"
echo "  ✓ $VERSION"

echo ""
echo "=== PyPI availability ==="
PYPI_JSON=$(curl -fsS "https://pypi.org/pypi/agent-foundry-runtime/json" 2>/dev/null || true)
[[ -n "$PYPI_JSON" ]] || fail "agent-foundry-runtime not on PyPI yet. Publish it first: python -m build && python -m twine upload dist/*"
echo "$PYPI_JSON" | $PY -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if '$VERSION' in d.get('releases', {}) else 1)" \
  || fail "PyPI has agent-foundry-runtime but not version $VERSION. Upload it first."
echo "  ✓ agent-foundry-runtime $VERSION on PyPI"

echo ""
echo "=== Publisher ==="
if ! command -v mcp-publisher >/dev/null 2>&1; then
  fail "mcp-publisher not installed: https://github.com/modelcontextprotocol/registry"
fi
echo "  ✓ $(command -v mcp-publisher)"

if [[ $DRY_RUN -eq 1 ]]; then
  echo ""
  echo "Dry-run only — not publishing."
  exit 0
fi

echo ""
echo "=== Publishing io.github.youcisla/agent-foundry ==="
echo "  (run 'mcp-publisher login github' first if this fails on auth)"
mcp-publisher publish

echo ""
echo "  ✓ MCP Registry entry submitted for $VERSION"
