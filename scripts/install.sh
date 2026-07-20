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
          local skills_dst="$HOME/.codex/skills/agent-foundry"
          local codex_dst="$HOME/.codex"
          if $DRY_RUN; then
            echo "Would symlink: $REPO_ROOT/skills -> $skills_dst"
            echo "Would symlink: $REPO_ROOT/.codex -> $codex_dst/agent-foundry-config"
          else
            mkdir -p "$(dirname "$skills_dst")"
            ln -sfn "$REPO_ROOT/skills" "$skills_dst"
            echo "Installed: $skills_dst -> $REPO_ROOT/skills"

            # Codex auto-loads AGENTS.md from the project root and config.toml
            # from ~/.codex/. Symlink the whole .codex/ directory so Codex picks
            # up AGENTS.md, config.toml, and per-agent configs at once.
            mkdir -p "$codex_dst"
            # Don't overwrite an existing ~/.codex — place Agent Foundry at a
            # sibling location and instruct the user to merge.
            if [ ! -e "$codex_dst/agent-foundry-config" ]; then
              ln -sfn "$REPO_ROOT/.codex" "$codex_dst/agent-foundry-config"
              echo "Installed: $codex_dst/agent-foundry-config -> $REPO_ROOT/.codex"
              echo ""
              echo "To activate, copy or merge into ~/.codex/:"
              echo "  cp -n $codex_dst/agent-foundry-config/AGENTS.md $codex_dst/AGENTS.md"
              echo "  cp -n $codex_dst/agent-foundry-config/config.toml $codex_dst/config.toml"
            fi
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
# Auto-run smoke test on the harness we just installed
if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  PYTHON=""
fi

if [[ -n "$PYTHON" && -n "$HARNESS" && "$HARNESS" != "" ]]; then
  echo ""
  echo "Smoke test:"
  if $PYTHON scripts/smoke-test.py "$HARNESS" 2>&1; then
    echo "Adapter ready."
  else
    echo "Adapter installed but smoke test failed. See scripts/smoke-test.py."
  fi
fi

echo ""
echo "Validate anytime: ./scripts/validate.sh"
