# Agent Foundry — Antigravity Adapter

**Status:** Beta — paths follow current Antigravity docs; harness load not yet
verified on a live install.

Antigravity has separate roots per product:

| Product | Global skills | Global rules |
| --- | --- | --- |
| App / IDE | `~/.gemini/config/skills/` | `~/.gemini/config/rules/` |
| Antigravity CLI | `~/.gemini/antigravity-cli/skills/` | `~/.gemini/antigravity-cli/rules/` |
| Workspace | `.agents/skills/` | `.agents/rules/` |

Legacy `.agent/skills/` is still read but is not a valid new-install target.
Legacy workflows are deprecated; use skills.

## Install

```bash
node scripts/install.js --harness=antigravity
```

## Layout

Each of the 35 skills is a direct child of the chosen skills root:

```text
~/.gemini/config/
  skills/
    api-design/SKILL.md
    plan-before-code/SKILL.md
    ... (35 total)
  rules/
    agent-foundry.md
```

## Test status

- [x] Adapter structure updated to current paths
- [x] Install dry-run succeeds
- [ ] End-to-end test on a real Antigravity install
