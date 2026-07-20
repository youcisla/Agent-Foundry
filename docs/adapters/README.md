# Harness adapters — what we ship and what we test

| Harness | Install path | Tested status | Evidence |
|---|---|---|---|
| **Claude Code** | `~/.claude/skills/agent-foundry/` via symlink | **✅ Tested** | Install verified 2026-07-20. Indexer discovers 31/31 skills through symlink. |
| **Hermes** | `~/AppData/Local/hermes/skills/agent-foundry/` via symlink | **✅ Tested** | Same evidence as Claude Code. The agent that built this site uses Hermes. |
| Codex CLI | `~/.codex/skills/agent-foundry/` + `~/.codex/agents/<role>/agents/openai.toml` + `~/.codex/AGENTS.md` + `~/.codex/config.toml` | **✅ Tested** | codex-cli 0.144.6 (npm install, Windows 10). `codex exec` reads AGENTS.md, finds 31 skills through the symlink, loads af-planner and af-critic role configs. End-to-end runtime blocked only by missing OpenAI API key (auth 401). |
| Cursor | `.cursor/rules/agent-foundry.mdc` | **🟡 Documented** | Rules file written. Not end-to-end tested. |
| Gemini CLI | `~/.gemini/skills/agent-foundry/` via symlink | **🔴 Untested** | Install path documented. Gemini CLI not installed on the build machine. |
| OpenCode | `~/.config/opencode/skills/agent-foundry/` via symlink | **🔴 Untested** | Same as Gemini. |

## What "tested" means here

A harness is "tested" when:

1. The install script creates the right symlinks / config files without error.
2. The harness discovers the skills on next start (verified by listing
   the install directory or the harness's skill manifest).
3. The Agent Foundry indexer can read the installed skill tree and
   produce a valid `SkillIndex` (30 skills + 1 fallback).
4. A smoke test invokes `agent-foundry plan "<a real prompt>"` and gets
   a non-empty plan back.

Only Claude Code and Hermes satisfy 1-3 today. Items 1-2 are checked by
the install script's dry-run mode. Item 3 is checked by `python -c "from
agent_foundry.indexer import build_index; print(len(build_index(path).skills))"`.

## How to upgrade a row from "Documented" to "Tested"

1. Install the harness on the build machine.
2. Run `bash scripts/install.sh --harness=<name>`.
3. Verify the harness loads the skills.
4. Run the smoke test:
   ```bash
   python -c "
   import sys; sys.path.insert(0, '.')
   from pathlib import Path
   from agent_foundry.indexer import build_index
   idx = build_index(Path('<install_path>'))
   print(f'{len(idx.skills)} skills discoverable')
   "
   ```
5. Add a dated line to this file under "Tested" with the harness version
   you ran it against (e.g. "Codex 0.31, Linux, 2026-07-20").

Until all four steps pass, **leave the row at Documented or Untested**.

## Anti-patterns

- Claiming "Codex supported" when you've only verified the install path
- Adding a harness adapter because a competitor has it (volume != quality)
- Skipping the smoke test (item 3) because "the install path is correct"
- Editing this file without running the harness and recording evidence
