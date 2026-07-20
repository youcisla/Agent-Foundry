# Agent Foundry — Codex CLI Guide

This supplements the root `AGENTS.md` with Codex-specific guidance. After
`bash scripts/install.sh --harness=codex`, this file lives at
`~/.codex/AGENTS.md` (per-project) or inside this repo's `.codex/` for
shipped defaults.

## Model Recommendations

| Task Type | Recommended Model |
|-----------|-------------------|
| Routine coding, tests, formatting | `gpt-5-mini` |
| Complex features, architecture | `gpt-5` |
| Debugging, refactoring | `gpt-5` |
| Security review | `gpt-5` |
| Skill body generation | `gpt-5-mini` (cost-efficient) |

## Skills Discovery

After install, skills are auto-loaded from `~/.codex/skills/agent-foundry/`.
Each skill contains:

- `SKILL.md` — Detailed instructions and workflow
- `agents/openai.yaml` — Codex interface metadata (description + required_tools)

Per-skill, per-agent manifests live at `agents/<skill-id>/agents/openai.yaml`.

## MCP Servers

Agent Foundry does **not** require MCP servers. The orchestrator (`agent-foundry serve`)
is the only external service the user might enable. Recommended baseline:

```toml
[mcp_servers.agent-foundry]
command = "agent-foundry"
args = ["serve", "--port", "8765"]
startup_timeout_sec = 10
```

This lets Codex route LLM calls through the Foundry's plan → execute → log
pipeline. Without it, Codex runs skills in isolation (no budget guard, no
judge, no execution log).

## External Action Boundaries

Treat networked tools as read-only by default. Search, inspect, and draft
freely within the user's requested scope, but require explicit user approval
before posting, publishing, pushing, merging, opening paid jobs, dispatching
remote agents, changing third-party resources, or modifying credentials.

When approval is ambiguous, produce a local plan or draft artifact instead
of taking the external action. Preserve user config and private state unless
the user specifically asks for a scoped change.

## Multi-Agent Support

Codex supports multi-agent workflows behind `features.multi_agent`. Agent
Foundry ships two native roles:

- `af-planner` — decomposes a request into a skill/agent plan
- `af-critic` — judges a completed output on correctness/slop/scope

To dispatch via Codex CLI, point the role at the agent's directory:

```toml
[agents]
[agents.af-planner]
description = "Decomposes a request into a skill/agent plan."
config_file = "agents/af-planner/agents/openai.yaml"
```

## Key Differences from Claude Code

| Feature | Claude Code | Codex CLI |
|---------|-------------|-----------|
| Hooks | 8+ event types | Not yet supported |
| Context file | `CLAUDE.md` + `AGENTS.md` | `AGENTS.md` only |
| Skills | Skills loaded via plugin | `.codex/skills/` directory |
| Commands | `/slash` commands | Instruction-based |
| Agents | Subagent Task tool | Multi-agent via `/agent` and `[agents.]` roles |
| Security | Hook-based enforcement | Instruction + sandbox |
| MCP | Full support | Supported via `config.toml` and `codex mcp add` |

## Security Without Hooks

Since Codex lacks hooks, security enforcement is instruction-based:

1. Always validate inputs at system boundaries.
2. Never hardcode secrets — use environment variables.
3. Run `pip audit` before committing (the project ships a Python daemon).
4. Review `git diff` before every push.
5. Use `sandbox_mode = "workspace-write"` in `.codex/config.toml`.

## Daemon Lifecycle

Agent Foundry uses a lazy-started daemon. If you want Codex to invoke
the orchestrator, start the daemon explicitly first:

```bash
agent-foundry serve --port 8765 &  # or rely on lazy-start
```

The daemon serves on `http://127.0.0.1:8765` with endpoints:

- `/health` — GET, returns daemon status
- `/index` — POST, rebuilds the skill index
- `/plan` — POST, returns ranked skills for a prompt
- `/execute` — POST, runs a specific skill
- `/loop` — POST, full plan → execute → return

## Compatibility Notes

Tested on:

- `codex-cli` 0.144.6, npm install (`npm i -g @openai/codex`)
- Windows 10, Node 22+, Python 3.10+

Not tested on:

- Mac/Linux standalone installer (`curl -fsSL https://chatgpt.com/codex/install.sh | sh`)
- Codex cloud / Codex IDE extension
- Codex app (desktop)