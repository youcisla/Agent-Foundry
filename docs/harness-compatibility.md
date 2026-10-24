# Harness compatibility

Verified against vendor documentation on 2026-10-18. Agent Foundry ships one
canonical skill set; adapters only translate discovery paths.

## Discovery matrix

| Harness | Global skills root | Project skills root | Instructions | Other |
| --- | --- | --- | --- | --- |
| Claude Code | `~/.claude/skills/` | `.claude/skills/` | `CLAUDE.md`, `AGENTS.md` | Plugin: `.claude-plugin/plugin.json` with a `skills` path list |
| Codex CLI | `~/.agents/skills/` | `.agents/skills/` at any repo level | `~/.codex/AGENTS.md`, repo `AGENTS.md` | `~/.codex/config.toml`; symlinked skill folders supported |
| Cursor | `~/.cursor/skills/`, `~/.agents/skills/` | `.cursor/skills/`, `.agents/skills/` | `AGENTS.md`; `.cursor/rules/*.mdc` | Global file rules `~/.cursor/rules/`; commands `.cursor/commands/` |
| Gemini CLI | `~/.gemini/skills/`, `~/.agents/skills/` | `.gemini/skills/`, `.agents/skills/` | `GEMINI.md` | Extension: `~/.gemini/extensions/<name>/gemini-extension.json` |
| Antigravity App / IDE | `~/.gemini/config/skills/` | `.agents/skills/` | `~/.gemini/AGENTS.md`, `.agents/rules/*.md` | Legacy `.agent/skills/` read-only |
| Antigravity CLI | `~/.gemini/antigravity-cli/skills/` | `.agents/skills/` | `~/.gemini/GEMINI.md` | Plugin skills under `.../plugins/<name>/skills/` |
| OpenCode | `~/.config/opencode/skills/`, `~/.agents/skills/`, `~/.claude/skills/` | `.opencode/skills/`, `.agents/skills/`, `.claude/skills/` | `AGENTS.md`, configured `instructions` | Config `~/.config/opencode/opencode.json` |
| Hermes | `~/.hermes/skills/` (category folders) | `.hermes/skills/`, `.agents/skills/` | `AGENTS.md` | Extra roots via `skills.external_dirs` |
| Kimi CLI | `~/.kimi-code/skills/`, `~/.agents/skills/` | `.kimi-code/skills/`, `.agents/skills/` | `AGENTS.md` | Legacy `~/.kimi/skills/`, `~/.claude/skills/`, `~/.codex/skills/` |
| Qwen Code | `~/.qwen/skills/` | `.qwen/skills/` | `QWEN.md`, `AGENTS.md` | Commands in `.qwen/commands/` |
| OpenClaw | `~/.agents/skills/`, `~/.openclaw/skills/` | `skills/`, `.agents/skills/` | `AGENTS.md` | Grouped skills scanned recursively (max depth 6) |
| CodeBuddy | `~/.codebuddy/skills/` | `.codebuddy/skills/` | `AGENTS.md` | Commands `~/.codebuddy/commands/`; files in `.codebuddy/rules/` |
| JoyCode | `~/.joycode/skills/` | `.joycode/skills/` | `.joycode/rules/` | Commands `.joycode/commands/` |
| Zed | `~/.agents/skills/` | `.agents/skills/` | `~/.config/zed/AGENTS.md` (Windows `%APPDATA%\Zed\AGENTS.md`) | Project instructions: `.rules`, `AGENTS.md`, etc. |

## Instruction-only harnesses

Some tools (Windsurf, Cline, Copilot, Aider, Continue) consume rules or
`AGENTS.md` but have no skill loader. Do not invent a skills root for them:
point their native rule file at this repo's `AGENTS.md`, or copy the relevant
block into `.windsurfrules`, `.clinerules`, `.github/copilot-instructions.md`,
or the tool's documented rule directory. Skills remain available through the
CLI (`agent-foundry run`) and MCP, even when the harness cannot load them
natively.

## Dos

1. **Install direct children.** Every skill goes to `<root>/<skill>/SKILL.md`.
   The repo's `core/` and `optional/` grouping is an authoring detail, not an
   install layout.
2. **Use the shared root when possible.** `~/.agents/skills/` is read by
   Codex, Cursor, Gemini CLI, Kimi, Zed, OpenCode, OpenClaw, jcode, and Hermes
   (when configured), so one install reaches many harnesses.
3. **Prefer links.** Directory symlinks stay current; on Windows use
   junctions, which do not need administrator rights. Offer `--copy` for
   portable installs.
4. **Record what you installed.** `.agent-foundry-installed.json` lets a
   re-run refresh its own entries and delete only skills that disappeared
   upstream.
5. **Preserve user files.** Copy global instructions only when the target does
   not exist; print a merge command otherwise. Never overwrite
   `config.toml`, `opencode.json`, or user rules.
6. **Put `name` and `description` in frontmatter.** Names must be lowercase
   alphanumerics with single hyphens, and should match the folder name.
7. **Keep one canonical instruction file.** Repo `AGENTS.md` is the source;
   harness files (`GEMINI.md`, `QWEN.md`, rules) should be thin pointers.
8. **Verify with the harness's own command** after install (`/skills`,
   `/extensions list`, `codex`, `hermes skills list`, Zed's Skills panel).

## Don'ts

1. **Don't nest a parent skill folder.** Most harnesses scan one level only.
   A `~/.claude/skills/agent-foundry/core/api-design/SKILL.md` layout is
   invisible.
2. **Don't assume plugin format portability.** Claude plugins, Gemini
   extensions, Codex plugins, and OpenCode configs are different formats.
3. **Don't copy a repo's `.codex/`, `.gemini/`, or `.opencode/` directory into
   a config path and call it installed.** Those directories are not loaded
   from arbitrary locations; the actual skills/manifests must land in the
   documented discovery roots.
4. **Don't install legacy Antigravity workflows.** They are deprecated in
   favor of skills; migrate standalone workflow `.md` files to
   `SKILL.md` bundles.
5. **Don't duplicate divergent rules.** Two copies of the same policy drift.
   Point adapters at one source.
6. **Don't claim a harness is tested without running the smoke test.**
   Vendor docs and path checks alone do not prove the install lands.
7. **Don't write global instructions silently.** A user's `AGENTS.md` may
   contain personal policy.
8. **Don't use `.agent/skills/` for new installs.** It is a legacy
   Antigravity alias; use `.agents/skills/`.

## Adapter status

| Status | Meaning |
| --- | --- |
| `tested` | Installer and indexer smoke test pass; 41 skills land at the documented root |
| `coming-soon` | No working adapter; target does not expose a stable discovery path |

All 14 adapters are `tested` by `scripts/test-install.js`, which installs every
target into a throwaway home and asserts 41 managed skills plus an indexable
manifest. Claude Code (`/skills`), Hermes (`hermes skills list`), and OpenClaw
(`openclaw skills`) additionally loaded the skills in a live session.
