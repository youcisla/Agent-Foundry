#!/usr/bin/env bash
# install.sh - install Agent-Foundry into a detected (or specified) harness
# Usage:
#   ./scripts/install.sh                       # auto-detect
#   ./scripts/install.sh --harness=claude-code  # explicit
#   ./scripts/install.sh --manual              # just print instructions
#   ./scripts/install.sh --dry-run             # show what would be done
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Cross-platform Python discovery (Windows + Unix)
detect_python() {
  if [[ -n "${AGENT_FOUNDRY_PY:-}" ]] && [[ -x "$AGENT_FOUNDRY_PY" ]]; then
    echo "$AGENT_FOUNDRY_PY"; return 0
  fi
  if command -v python3 >/dev/null 2>&1; then echo "python3"; return 0; fi
  if command -v python >/dev/null 2>&1; then echo "python"; return 0; fi
  # Windows .venv fallback
  if [[ -x "$REPO_ROOT/.venv/Scripts/python.exe" ]]; then
    echo "$REPO_ROOT/.venv/Scripts/python.exe"; return 0
  fi
  return 1
}

# Cross-platform HOME detection
if [[ -z "${HOME:-}" ]]; then
  if [[ -n "${USERPROFILE:-}" ]]; then export HOME="$USERPROFILE"; fi
fi

# Detect OS once
case "$(uname -s 2>/dev/null || echo Windows)" in
  MINGW*|CYGWIN*|MSYS*) OS=windows ;;
  Darwin)               OS=macos ;;
  Linux|*BSD)           OS=linux ;;
  *)                    OS=unknown ;;
esac
export AGENT_FOUNDRY_OS="$OS"

# Convert MSYS/Git Bash POSIX paths to native Windows paths (mirrors ECC).
# Used when invoking native Windows tools (cmd.exe, mklink, PowerShell).
cygpath_w() {
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -w "$1"
  else
    echo "$1"
  fi
}

# link_or_copy: prefer symlinks; fall back to Windows junction/copy when symlink fails.
# Mirrors ECC's behavior — file copy is the universal fallback that works everywhere.
link_or_copy() {
  local src="$1" dst="$2"
  # Remove existing target if present
  [ -e "$dst" ] || [ -L "$dst" ] && rm -rf "$dst" 2>/dev/null || true

  # Try symlink first (works on macOS/Linux, and Windows with admin/dev mode)
  if ln -sfn "$src" "$dst" 2>/dev/null; then
    echo "  → linked $dst -> $src"
    return 0
  fi

  # Fallback 1: Windows junction (no admin needed)
  if [[ "$OS" == "windows" ]] && command -v cmd >/dev/null 2>&1; then
    local win_src win_dst
    win_src=$(cygpath_w "$src")
    win_dst=$(cygpath_w "$dst")
    if cmd //c "mklink /J \"$win_dst\" \"$win_src\"" >/dev/null 2>&1; then
      echo "  → junction $dst -> $src (Windows)"
      return 0
    fi
  fi

  # Fallback 2: recursive copy (universal fallback)
  if command -v cp >/dev/null 2>&1; then
    if cp -r "$src" "$dst" 2>/dev/null; then
      echo "  → copied $dst <- $src"
      return 0
    fi
  fi

  echo "  → ERROR: failed to link or copy $dst" >&2
  return 1
}

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
      if $DRY_RUN; then echo "Would link: $REPO_ROOT/skills -> $dst"
      else mkdir -p "$(dirname "$dst")"
           link_or_copy "$REPO_ROOT/skills" "$dst"
           echo "Installed: $dst"
      fi
      ;;
    codex)
          local skills_dst="$HOME/.codex/skills/agent-foundry"
          local codex_dst="$HOME/.codex"
          if $DRY_RUN; then
            echo "Would link: $REPO_ROOT/skills -> $skills_dst"
            echo "Would link: $REPO_ROOT/.codex -> $codex_dst/agent-foundry-config"
          else
            mkdir -p "$(dirname "$skills_dst")"
            link_or_copy "$REPO_ROOT/skills" "$skills_dst"
            echo "Installed: $skills_dst"

            # Codex auto-loads AGENTS.md from the project root and config.toml
            # from ~/.codex/. Link the whole .codex/ directory so Codex picks
            # up AGENTS.md, config.toml, and per-agent configs at once.
            mkdir -p "$codex_dst"
            if [ ! -e "$codex_dst/agent-foundry-config" ]; then
              link_or_copy "$REPO_ROOT/.codex" "$codex_dst/agent-foundry-config"
              echo "Installed: $codex_dst/agent-foundry-config -> $REPO_ROOT/.codex"
              echo ""
              echo "To activate, copy or merge into ~/.codex/:"
              echo "  cp -n $codex_dst/agent-foundry-config/AGENTS.md $codex_dst/AGENTS.md"
              echo "  cp -n $codex_dst/agent-foundry-config/config.toml $codex_dst/config.toml"
            fi
          fi
          ;;
    cursor)
      local cursor_dst="$HOME/.cursor/rules"
      if $DRY_RUN; then
        echo "Would copy: $REPO_ROOT/.cursor/rules/*.mdc -> $cursor_dst"
        echo "Would copy: $REPO_ROOT/.cursor/hooks.json -> $HOME/.cursor/hooks.json"
      else
        mkdir -p "$cursor_dst"
        cp "$REPO_ROOT/.cursor/rules/"*.mdc "$cursor_dst/" 2>/dev/null && echo "Installed: $cursor_dst/ (rules)"
        cp "$REPO_ROOT/.cursor/hooks.json" "$HOME/.cursor/hooks.json" 2>/dev/null && echo "Installed: $HOME/.cursor/hooks.json"
        echo "Cursor: restart to pick up rules + hooks."
      fi
      ;;
    hermes)
      local dst="$HOME/AppData/Local/hermes/skills/agent-foundry"
      if $DRY_RUN; then echo "Would link: $REPO_ROOT/skills -> $dst"
      else mkdir -p "$(dirname "$dst")"
           link_or_copy "$REPO_ROOT/skills" "$dst"
           echo "Installed: $dst"
      fi
      ;;
    gemini-cli)
      local d="$HOME/.gemini"
      if $DRY_RUN; then
        echo "Would link: $REPO_ROOT/.gemini -> $d/agent-foundry-config"
      else
        mkdir -p "$d"
        if [ ! -e "$d/agent-foundry-config" ]; then
          link_or_copy "$REPO_ROOT/.gemini" "$d/agent-foundry-config"
          echo "Installed: $d/agent-foundry-config -> $REPO_ROOT/.gemini"
        fi
        echo "Gemini CLI has no plugin system. Reference: $d/agent-foundry-config/AGENTS.md"
      fi
      ;;
    opencode)
      local d="$HOME/.config/opencode"
      if $DRY_RUN; then
        echo "Would copy: $REPO_ROOT/.opencode/ -> $d/agent-foundry-config"
        echo "Would link: $REPO_ROOT/skills -> $d/skills/agent-foundry"
      else
        mkdir -p "$d"
        cp -r "$REPO_ROOT/.opencode" "$d/agent-foundry-config" 2>/dev/null
        echo "Installed: $d/agent-foundry-config/ -> $REPO_ROOT/.opencode"
        mkdir -p "$d/skills"
        link_or_copy "$REPO_ROOT/skills" "$d/skills/agent-foundry"
        echo "Installed: $d/skills/agent-foundry -> $REPO_ROOT/skills"
        echo "Merge config: jq -s '.[0] * .[1]' $d/opencode.json $d/agent-foundry-config/opencode.json > merge.json"
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
PYTHON=""
if command -v python3 >/dev/null 2>&1; then PYTHON=python3
elif command -v python >/dev/null 2>&1; then PYTHON=python
elif [[ -x "$REPO_ROOT/.venv/Scripts/python.exe" ]]; then PYTHON="$REPO_ROOT/.venv/Scripts/python.exe"
elif [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then PYTHON="$REPO_ROOT/.venv/bin/python"
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
