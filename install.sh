#!/usr/bin/env bash
# install.sh: install Agent Foundry (macOS / Linux / Git Bash on Windows)
#
# Idempotent: re-run to update.

set -e

REPO_URL="${AGENT_FOUNDRY_REPO:-https://github.com/youcisla/Agent-Foundry.git}"
INSTALL_DIR="${AGENT_FOUNDRY_DIR:-$HOME/.agent-foundry}"
PLUGIN_DIR="$HOME/.claude/plugins/agent-foundry"
CONFIG_DIR="$HOME/.config/agent-foundry"

echo "Agent Foundry install"
echo "  repo:    $REPO_URL"
echo "  install: $INSTALL_DIR"
echo "  plugin:  $PLUGIN_DIR"
echo

# Profile selection: minimal, core (default), full
AF_PROFILE="${AF_PROFILE:-core}"
echo "  profile: $AF_PROFILE"

OS="$(uname -s)"
case "$OS" in
  Linux)  PLATFORM=linux ;;
  Darwin) PLATFORM=mac ;;
  MINGW*|MSYS*|CYGWIN*)
    # Git Bash / MSYS / Cygwin on Windows. The native shell installer below
    # relies on macOS/Linux idioms, so delegate to the cross-platform Node
    # installer instead. First clone (if needed), then hand off.
    if ! command -v node >/dev/null 2>&1; then
      echo "ERROR: Node.js 18+ is required to install on Windows under Git Bash." >&2
      echo "       Install from https://nodejs.org, or use scripts/install.ps1 / install.bat." >&2
      exit 1
    fi
    if [ ! -d "$INSTALL_DIR/.git" ]; then
      echo "Cloning repo to $INSTALL_DIR ..."
      mkdir -p "$(dirname "$INSTALL_DIR")"
      git clone --depth=1 "$REPO_URL" "$INSTALL_DIR"
    else
      (cd "$INSTALL_DIR" && git pull --depth=1 --ff-only) || true
    fi
    echo "Windows detected (Git Bash). Launching the Node installer..."
    exec node "$INSTALL_DIR/scripts/install.js" "$@"
    ;;
  *) echo "ERROR: unsupported OS '$OS'. supports macOS/Linux/Windows." >&2; exit 1 ;;
esac

# 1) Python 3.10+
PY="${PYTHON:-python3}"
if ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)'; then
  echo "ERROR: Python 3.10+ required (have $($PY --version))." >&2; exit 1
fi

# 2) Clone or pull
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "Updating existing repo at $INSTALL_DIR ..."
  (cd "$INSTALL_DIR" && git pull --depth=1 --ff-only) || true
else
  echo "Cloning repo to $INSTALL_DIR ..."
  mkdir -p "$(dirname "$INSTALL_DIR")"
  git clone --depth=1 "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# 3) venv + editable install
VENV_DIR="$CONFIG_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating venv at $VENV_DIR ..."
  "$PY" -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
pip install --upgrade pip >/dev/null
pip install -e . >/dev/null

# 4) Symlink the Claude Code plugin
if [ ! -e "$PLUGIN_DIR" ]; then
  echo "Symlinking plugin to $PLUGIN_DIR ..."
  mkdir -p "$(dirname "$PLUGIN_DIR")"
  ln -s "$INSTALL_DIR" "$PLUGIN_DIR"
fi

# 5) Initialize (writes config + first index)
if agent-foundry init --force 2>&1 | tail -1; then :; else
  echo "WARN: agent-foundry init failed; you can retry later." >&2
fi

# 6) Profile-specific component selection
case "$AF_PROFILE" in
  full)
    # Make hooks executable
    if [ -d "hooks" ]; then
      chmod +x hooks/*.sh 2>/dev/null || true
    fi
    ;;
  minimal)
    # Remove daemon support (skills only)
    echo "  (minimal: daemon not installed; use agent-foundry commands directly)"
    ;;
  core|*)
    # Everything installed (default)
    ;;
esac

echo
echo "Installed."
echo "Next steps:"
echo "  1) Set your API key:"
echo "       export ANTHROPIC_API_KEY=sk-..."
echo "     (or OPENAI_API_KEY)"
echo "  2) Use slash commands in Claude Code:"
echo "       /plan \"build a react component\""
echo "       /af   \"build a react component\""
echo "  3) CLI options:"
echo "       agent-foundry --help"
