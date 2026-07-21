#!/usr/bin/env bash
# activate.sh — Cross-platform venv activator for Agent Foundry.
#
# Detects the OS and activates the .venv regardless of platform:
#   - Windows (Git Bash / MSYS): sources .venv/Scripts/activate
#   - Linux / macOS: sources .venv/bin/activate
#
# Usage:
#   source scripts/activate.sh
#   . scripts/activate.sh
#
# After activation:
#   python -V      -> 3.11+
#   which python   -> .venv/bin/python or .venv/Scripts/python.exe

# Resolve repo root from this script's location (cross-platform).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV="$REPO_ROOT/.venv"

if [ ! -d "$VENV" ]; then
    echo "No .venv found at $VENV"
    echo "Run: python3 -m venv .venv && .venv/bin/pip install -e ."
    return 1 2>/dev/null || exit 1
fi

# Detect OS via uname (works in Git Bash on Windows, native macOS, Linux)
case "$(uname -s 2>/dev/null || echo Windows)" in
    MINGW*|CYGWIN*|MSYS*)
        # Git Bash on Windows
        if [ -f "$VENV/Scripts/activate" ]; then
            . "$VENV/Scripts/activate"
        else
            echo "Activate script not found at $VENV/Scripts/activate"
            return 1 2>/dev/null || exit 1
        fi
        ;;
    Darwin|Linux|*BSD)
        # macOS or Linux
        if [ -f "$VENV/bin/activate" ]; then
            . "$VENV/bin/activate"
        else
            echo "Activate script not found at $VENV/bin/activate"
            return 1 2>/dev/null || exit 1
        fi
        ;;
    *)
        echo "Unknown OS: $(uname -s)"
        # Try both layouts
        if [ -f "$VENV/bin/activate" ]; then
            . "$VENV/bin/activate"
        elif [ -f "$VENV/Scripts/activate" ]; then
            . "$VENV/Scripts/activate"
        else
            return 1 2>/dev/null || exit 1
        fi
        ;;
esac

# Export the resolved Python path for child processes (works across shells)
if [ -n "$VIRTUAL_ENV" ]; then
    case "$(uname -s 2>/dev/null || echo Windows)" in
        MINGW*|CYGWIN*|MSYS*)
            export AGENT_FOUNDRY_PY="$VIRTUAL_ENV/Scripts/python.exe"
            ;;
        *)
            export AGENT_FOUNDRY_PY="$VIRTUAL_ENV/bin/python"
            ;;
    esac
    echo "✓ Agent Foundry venv activated (Python: $AGENT_FOUNDRY_PY)"
fi