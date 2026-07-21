#!/usr/bin/env bash
# publish.sh — Agent Foundry
#
# Wraps the npm publish flow. Runs gates first, then dry-run, then publish.
# Handles the 2FA prompt automatically (npm will prompt for the TOTP code).
#
# Usage:
#   bash scripts/publish.sh                 # patch bump + publish
#   bash scripts/publish.sh --no-bump        # publish current version as-is
#   bash scripts/publish.sh --dry-run        # just run gates + dry-run
#   bash scripts/publish.sh --version=minor # explicit bump

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

DO_BUMP=1
DO_DRY_RUN=0
BUMP_TYPE="patch"

for arg in "$@"; do
  case "$arg" in
    --no-bump)    DO_BUMP=0 ;;
    --dry-run)    DO_DRY_RUN=1 ;;
    --version=*)  BUMP_TYPE="${arg#--version=}" ;;
    --help|-h)
      echo "Usage: bash scripts/publish.sh [--no-bump] [--dry-run] [--version=patch|minor|major]"
      echo ""
      echo "  Default: bump patch version, run gates + dry-run, then publish"
      echo "  --no-bump    publish current package.json version without bumping"
      echo "  --dry-run    stop after gates + dry-run (don't actually publish)"
      echo "  --version=X  bump type: patch (default), minor, or major"
      exit 0
      ;;
    *)
      echo "Unknown arg: $arg" >&2
      exit 2
      ;;
  esac
done

# 1. Pre-flight
echo "=== Pre-flight ==="
if ! command -v node >/dev/null 2>&1; then
  echo "  ✗ node not found" >&2
  exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
  echo "  ✗ npm not found" >&2
  exit 1
fi

# 2. Auth check
echo ""
echo "=== Auth ==="
if ! npm whoami >/dev/null 2>&1; then
  echo "  ✗ not logged in. Run: npm login" >&2
  echo "    If 2FA is enabled, you'll need your authenticator app ready." >&2
  exit 1
fi
NPM_USER=$(npm whoami)
echo "  ✓ logged in as: $NPM_USER"

# 3. Working tree check
echo ""
echo "=== Working tree ==="
if [[ -n "$(git status --short)" ]]; then
  echo "  ⚠ working tree is dirty:"
  git status --short | head -5
  echo ""
  echo "  Commit or stash before publishing."
  exit 1
fi
echo "  ✓ clean"

# 4. Quality gates
echo ""
echo "=== Quality gates ==="
bash scripts/validate.sh 2>&1 | tail -1
python scripts/foundry-eval.py 2>&1 | tail -1
bash scripts/nox.sh 2>&1 | tail -1

# 5. Bump version
LOCAL_VER=$(node -p "require('./package.json').version")
PUBLISHED_VER=$(npm view agent-foundry version 2>/dev/null || echo "0.0.0")
echo ""
echo "=== Version ==="
echo "  local:     $LOCAL_VER"
echo "  published: $PUBLISHED_VER"

if [[ $DO_BUMP -eq 1 ]]; then
  if [[ "$LOCAL_VER" == "$PUBLISHED_VER" ]]; then
    echo ""
    echo "  Bumping $BUMP_TYPE version..."
    npm version "$BUMP_TYPE" --no-git-tag-version
    NEW_VER=$(node -p "require('./package.json').version")
    echo "  new:       $NEW_VER"
    # Commit the bump
    git add package.json
    git commit -m "chore: bump v$LOCAL_VER → v$NEW_VER for npm publish" --no-verify
  else
    echo "  ✓ local > published, no bump needed"
  fi
fi

# 6. Dry-run
echo ""
echo "=== Dry-run ==="
npm publish --dry-run 2>&1 | tail -10

if [[ $DO_DRY_RUN -eq 1 ]]; then
  echo ""
  echo "Dry-run only — not publishing."
  exit 0
fi

# 7. Publish
NEW_VER=$(node -p "require('./package.json').version")
echo ""
echo "=== Publishing agent-foundry@$NEW_VER ==="
echo "  (npm will prompt for 2FA OTP if enabled)"
echo ""

# Use --otp=$(2fa) if NPM_CONFIG_OTP env var is set (for CI), else interactive
if [[ -n "${NPM_CONFIG_OTP:-}" ]]; then
  npm publish --access public --otp="$NPM_CONFIG_OTP"
else
  npm publish --access public
fi

# 8. Tag + verify
echo ""
echo "=== Tag + verify ==="
git tag -a "v$NEW_VER" -m "Release v$NEW_VER"
git push origin main --tags

# Install fresh and verify
if command -v agent-foundry >/dev/null 2>&1; then
  INSTALLED_VER=$(agent-foundry --list >/dev/null 2>&1 && echo "ok" || echo "FAIL")
  echo "  agent-foundry bin: $INSTALLED_VER"
fi

echo ""
echo "  ✓ agent-foundry@$NEW_VER is live on npm"
echo "    https://www.npmjs.com/package/agent-foundry"