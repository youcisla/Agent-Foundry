---
name: autonomous-briefing
description: Run a fully autonomous morning briefing: research the day's trending topics with last30days, scan HuggingFace model/dataset changes, check GitHub for new releases, then write a structured briefing to agent-memory-vault and deliver to the user. Use when the user asks for a daily/weekly briefing, autonomous news scan, or wants to orchestrate all installed skills into a single output.
version: 1.0.0
license: MIT
author: Agent Foundry Contributors
category: optional
tags: [agent-foundry, autonomous, briefing, orchestration, cron, daily, agent-loop]
platforms: [linux, macos, windows]
---

# Autonomous Briefing

The end-to-end autonomous agentic workflow. Combines:

- `last30days` for trending research
- `hf-trending-monitor` for ML/HF ecosystem changes
- `hf-papers-tracker` for new papers
- `github` skill for release notifications
- `agent-memory-vault` for persistent context
- `effective-agent-skills` for output quality

## Cron invocation

```bash
# Daily 8 AM: full briefing
0 8 * * * pi run "use --autonomous-briefing"
# Or manually:
python scripts/autonomous_briefing.py --memory-home=~/.agent-memory --emit=md
```

## What it produces

1. **Trending research** (last30days output, condensed)
2. **AI/ML ecosystem shifts** (HF top movers, new datasets, papers)
3. **Codebase signal** (recent GitHub activity if monitoring a project)
4. **Memory delta** (what changed since yesterday's run)
5. **Actionable items** (top 3 things you should look at today)

Saved to:
- `~/.agent-memory/topics/briefing/YYYY-MM-DD.md`
- `agent-memory-vault put --topic=briefing --key=YYYY-MM-DD --value=$(cat briefing.md)`

## Companion skills (all installed)

- last30days (research)
- hf-trending-monitor, hf-papers-tracker (HF ecosystem)
- agent-memory-vault (persistent context)
- effective-agent-skills (output format standards)
- goal-loop / agent-self-scheduling (run scheduling)

## Output format

See `scripts/autonomous_briefing.py --help` for full options.

Sample:

```
# Autonomous Briefing - 2026-08-14

## Today's research (last30days)
- Trending: ...

## ML/AI ecosystem (HF)
- New top datasets: ...
- New papers: ...

## Memory delta
- Decisions made: 2
- Errors logged: 0

## Today's top 3 actions
1. ...
2. ...
3. ...
```
