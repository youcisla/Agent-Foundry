#!/usr/bin/env bash
# install.sh - install Agent-Foundry into a detected (or specified) harness
# Usage:
#   ./scripts/install.sh                       # auto-detect
#   ./scripts/install.sh --harness=claude-code  # explicit
#   ./scripts/install.sh --manual              # just print instructions
#   ./scripts/install.sh --dry-run             # show what would be done
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HARNESS=""
MANUAL=false
DRY_RUN=false

for arg in "$@"; do
  case "$arg" in
    --harness=*) HARNESS="${arg#*=}" ;;
    --manual)    MANUAL=true ;;
    --dry-run)   DRY_RUN=true ;;
    *) echo "Unknown arg: $arg" >&2; exit 1 ;;
  esac
done

detect_harness() {
  if [[ -d "$HOME/.claude" ]]; then echo "claude-code"
  elif command -v codex >/dev/null 2>&1 && [[ -d "$HOME/.codex" ]]; then echo "codex"
  elif [[ -d "$HOME/.cursor" ]]; then echo "cursor"
  elif [[ -d "$HOME/.hermes" ]]; then echo "hermes"
  elif command -v gemini >/dev/null 2>&1; then echo "gemini-cli"
  elif [[ -d "$HOME/.config/opencode" ]]; then echo "opencode"
  else echo ""
  fi
}

if [[ -z "$HARNESS" ]]; then
  HARNESS=$(detect_harness)
fi

install_for_harness() {
  local harness=$1
  case "$harness" in
    claude-code)
      local dst="$HOME/.claude/skills/agent-foundry"
      if $DRY_RUN; then echo "Would symlink: $REPO_ROOT/skills -> $dst"
      else mkdir -p "$(dirname "$dst")"
           ln -sfn "$REPO_ROOT/skills" "$dst"
           echo "Installed: $dst -> $REPO_ROOT/skills"
      fi
      ;;
    codex)
      local dst="$HOME/.codex/skills/agent-foundry"
      if $DRY_RUN; then echo "Would symlink: $REPO_ROOT/skills -> $dst"
      else mkdir -p "$(dirname "$dst")"
           ln -sfn "$REPO_ROOT/skills" "$dst"
           echo "Installed: $dst -> $REPO_ROOT/skills"
      fi
      ;;
    cursor)
      echo "Cursor: copy skills/core/ and skills/optional/ contents into .cursor/rules/ as you see fit."
      echo "  Source: $REPO_ROOT/skills/core"
      echo "  Source: $REPO_ROOT/skills/optional"
      ;;
    hermes)
      local dst="$HOME/AppData/Local/hermes/skills/agent-foundry"
      if $DRY_RUN; then echo "Would symlink: $REPO_ROOT/skills -> $dst"
      else mkdir -p "$(dirname "$dst")"
           ln -sfn "$REPO_ROOT/skills" "$dst"
           echo "Installed: $dst -> $REPO_ROOT/skills"
      fi
      ;;
    gemini-cli)
      local dst="$HOME/.gemini/skills/agent-foundry"
      if $DRY_RUN; then echo "Would symlink: $REPO_ROOT/skills -> $dst"
      else mkdir -p "$(dirname "$dst")"
           ln -sfn "$REPO_ROOT/skills" "$dst"
           echo "Installed: $dst -> $REPO_ROOT/skills"
      fi
      ;;
    opencode)
      local dst="$HOME/.config/opencode/skills/agent-foundry"
      if $DRY_RUN; then echo "Would symlink: $REPO_ROOT/skills -> $dst"
      else mkdir -p "$(dirname "$dst")"
           ln -sfn "$REPO_ROOT/skills" "$dst"
           echo "Installed: $dst -> $REPO_ROOT/skills"
      fi
      ;;
    *)
      echo "Unknown harness: $harness" >&2
      echo "Supported: claude-code, codex, cursor, hermes, gemini-cli, opencode" >&2
      return 1
      ;;
  esac
}

if $MANUAL; then
  echo "Manual install instructions:"
  echo ""
  echo "  1. Choose your harness: claude-code, codex, cursor, hermes, gemini-cli, opencode"
  echo "  2. Symlink or copy $REPO_ROOT/skills into the harness's skills directory"
  echo "  3. Restart the harness so it picks up the new skills"
  echo ""
  echo "  Example for Claude Code:"
  echo "    ln -s $REPO_ROOT/skills ~/.claude/skills/agent-foundry"
  exit 0
fi

if [[ -z "$HARNESS" ]]; then
  echo "No harness detected. Use --harness=<name> or --manual" >&2
  echo "Supported: claude-code, codex, cursor, hermes, gemini-cli, opencode" >&2
  exit 1
fi

echo "Installing for harness: $HARNESS"
install_for_harness "$HARNESS"

echo ""
echo "Done. Restart your harness so it picks up the new skills."
echo "Validate anytime: ./scripts/validate.sh"
