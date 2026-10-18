# ADR 0001: Routing pipeline and MCP surface

Date: 2026-10-17
Status: accepted

## Context

The 0.3 planner scored skills with regular expressions only. Trigger derivation
produced malformed patterns, so common prompts matched nothing and `plan()`
raised on a missing field. Adoption data (SkillsBench, Jev/Hermes, plugin
marketplaces) shows two expectations the project did not meet: measurable skill
lift, and a machine-callable surface for other agents.

## Decision

1. **Routing is tiered.** Engram cache (O(1)) first, then regex triggers, then
   keyword overlap, then optional embeddings. An optional LLM or decision-model
   rerank can sit on top. Every tier degrades to the previous one; no tier is
   required.
2. **Weights are learned, not guessed.** Judge scores and feedback update a
   per-skill multiplier (clipped to 0.6-1.4). The planner applies it after the
   cost penalty.
3. **One runtime, several surfaces.** CLI, HTTP daemon, and MCP stdio share the
   same planner/executor functions. The MCP server is dependency-free JSON-RPC
   so it can ship inside the existing package.
4. **Evaluation is paired.** `agent-foundry eval` runs each task with and
   without a skill and reports lift. The task layout follows SkillsBench v1.1.
5. **Integrity is checked.** Skill files carry a SHA-256 in the index and are
   refused if the bytes changed after indexing.

## Consequences

- The package stays dependency-light: embeddings are an optional extra, MCP is
  stdlib only.
- Routing quality is measurable per release, not asserted.
- Publishing to the MCP registry and the Claude directory becomes a packaging
  task, not a rewrite.
- Learned weights require judge or feedback data; with no data every skill
  keeps weight 1.0.
