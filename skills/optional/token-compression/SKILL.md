---
name: token-compression
description: Token-compression proxy + MCP server + library that compresses tool outputs,
  logs, files, and RAG chunks before they consume context. 60-95% token reduction
  on JSON, 15-25% on coding-agent outputs. Use when token usage is high and output
  could be compressed without losing signal.
version: 0.1.0
license: MIT
author: Agent Foundry Contributors
---

# Token Compression

A token-compression proxy + MCP server + library that sits between your tools and your LLM, compressing tool outputs, logs, files, and RAG chunks before they consume context.

## Benchmarks

- Coding agent tool outputs: **15-25% fewer tokens**
- JSON outputs: **60-95% fewer tokens**
- Same LLM answers (no semantic loss)

## Three Deploy Modes

| Mode | When to use |
|------|-------------|
| **MCP server** | When your harness supports MCP (Claude Code, Hermes, etc.) |
| **Proxy** | When you need to intercept all LLM-bound traffic |
| **Library/SDK** | When you want programmatic control over compression |

## When to Use

- Tool outputs are eating your context window (>2K tokens per call)
- JSON responses are too large (especially from API queries)
- Long file reads consume budget
- RAG chunks include irrelevant content
- Before using a large-codebase-reasoning task

## Installation

Refer to the upstream repository for the latest install instructions.

## Anti-patterns

- Compressing already-small outputs (<200 tokens)
- Using this instead of backend pagination (compression is a band-aid, not a fix)
- Expecting compression on streaming outputs


## Verification Checklist

- [ ] The claim or action has been verified against a live source
- [ ] The output matches the request's scope (no scope creep)
- [ ] Slop markers are absent (filler, hedging, emoji headers)
