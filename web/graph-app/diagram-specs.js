/**
 * Static diagram specs rendered as small React Flow canvases (replacing the old
 * D2 SVGs on index.html and audit.html). Positions are hand-placed for clarity.
 * variant: accent | green | blue | muted | io | group
 */
export const DIAGRAMS = {
  // index.html — orchestrator flow
  orchestrator: {
    dir: "LR",
    nodes: [
      { id: "prompt", x: 0, y: 90, variant: "io", label: "Your prompt" },
      { id: "matcher", x: 175, y: 90, variant: "accent", label: "Skill matcher" },
      { id: "planner", x: 360, y: 10, variant: "blue", label: "Planner", sub: "rank & cost" },
      { id: "executor", x: 360, y: 165, variant: "blue", label: "Executor", sub: "LiteLLM" },
      { id: "provider", x: 565, y: 165, variant: "green", label: "LLM provider" },
      { id: "sqlite", x: 565, y: 10, variant: "muted", label: "SQLite log" },
      { id: "response", x: 760, y: 90, variant: "io", label: "Response" },
    ],
    edges: [
      { source: "prompt", target: "matcher" },
      { source: "matcher", target: "planner", color: "blue" },
      { source: "planner", target: "executor", color: "blue", label: "plan" },
      { source: "executor", target: "provider", color: "green", label: "call" },
      { source: "provider", target: "executor", color: "green", label: "tokens", dashed: true },
      { source: "executor", target: "sqlite", color: "muted", label: "log" },
      { source: "sqlite", target: "response", color: "accent" },
    ],
  },

  // audit.html — community cohesion clusters (no edges, just grouped members)
  cohesion: {
    dir: "TB",
    groups: [
      { x: 0, y: 0, w: 190, h: 165, color: "green", label: "Tight · > 0.5" },
      { x: 220, y: 0, w: 190, h: 235, color: "accent", label: "Medium · 0.1–0.5" },
      { x: 440, y: 0, w: 210, h: 190, color: "muted", label: "Low · < 0.1 (cross-cutting)" },
    ],
    nodes: [
      { id: "fe", x: 25, y: 55, variant: "green", label: "foundry-eval" },
      { id: "pa", x: 25, y: 105, variant: "green", label: "provenance-audit" },
      { id: "log", x: 245, y: 55, variant: "accent", label: "logging_db" },
      { id: "idx", x: 245, y: 105, variant: "accent", label: "indexer" },
      { id: "exx", x: 245, y: 155, variant: "accent", label: "executor" },
      { id: "plx", x: 245, y: 200, variant: "accent", label: "planner" },
      { id: "cfg", x: 465, y: 55, variant: "muted", label: "Config" },
      { id: "cli", x: 465, y: 105, variant: "muted", label: "cli" },
      { id: "sch", x: 465, y: 155, variant: "muted", label: "JSON schema fields" },
    ],
    edges: [],
  },

  // audit.html — request lifecycle (was a sequence diagram)
  sequence: {
    dir: "LR",
    nodes: [
      { id: "u", x: 0, y: 70, variant: "io", label: "User prompt" },
      { id: "loop", x: 165, y: 70, variant: "accent", label: "run_loop" },
      { id: "rank", x: 340, y: 0, variant: "blue", label: "rank_skills" },
      { id: "exec", x: 340, y: 140, variant: "blue", label: "executor" },
      { id: "llm", x: 525, y: 140, variant: "green", label: "LiteLLM" },
      { id: "judge", x: 525, y: 0, variant: "accent", label: "af-critic", sub: "judge" },
      { id: "db", x: 710, y: 70, variant: "muted", label: "executions.db" },
      { id: "resp", x: 880, y: 70, variant: "io", label: "LoopResponse" },
    ],
    edges: [
      { source: "u", target: "loop", label: "/af …" },
      { source: "loop", target: "rank", color: "blue", label: "rank" },
      { source: "rank", target: "exec", color: "blue", label: "top match" },
      { source: "exec", target: "llm", color: "green", label: "POST" },
      { source: "llm", target: "exec", color: "green", label: "resp", dashed: true },
      { source: "exec", target: "judge", color: "accent", label: "score" },
      { source: "judge", target: "db", color: "muted", label: "log" },
      { source: "db", target: "resp", color: "accent" },
    ],
  },

  // audit.html — god-node dependency graph
  godnodes: {
    dir: "TB",
    nodes: [
      { id: "cfg", x: 40, y: 0, variant: "accent", label: "Config", sub: "14 edges" },
      { id: "cap", x: 230, y: 0, variant: "accent", label: "create_app", sub: "15 edges" },
      { id: "rl", x: 135, y: 95, variant: "accent", label: "run_loop", sub: "14 edges" },
      { id: "bi", x: -30, y: 200, variant: "accent", label: "build_index", sub: "12" },
      { id: "gc", x: 95, y: 200, variant: "accent", label: "get_index_cached", sub: "12" },
      { id: "rs", x: 250, y: 200, variant: "accent", label: "rank_skills", sub: "12" },
      { id: "ex", x: 380, y: 200, variant: "accent", label: "execute", sub: "10" },
      { id: "pl", x: 500, y: 200, variant: "accent", label: "plan", sub: "10" },
      { id: "si", x: 110, y: 305, variant: "accent", label: "SkillIndex", sub: "11" },
      { id: "te", x: 380, y: 305, variant: "accent", label: "TokenEstimate", sub: "12" },
    ],
    edges: [
      { source: "cfg", target: "cap", label: "consumed", dashed: true },
      { source: "cfg", target: "rl", label: "consumed", dashed: true },
      { source: "cap", target: "rl" },
      { source: "rl", target: "bi" }, { source: "rl", target: "gc" }, { source: "rl", target: "rs" },
      { source: "rl", target: "ex" }, { source: "rl", target: "pl" },
      { source: "bi", target: "si" }, { source: "rs", target: "si" }, { source: "ex", target: "te" },
    ],
  },

  // audit.html — repository architecture map
  architecture: {
    dir: "LR",
    groups: [
      { x: 0, y: 0, w: 250, h: 360, color: "muted", label: "Agent Foundry /" },
      { x: 340, y: 0, w: 250, h: 300, color: "muted", label: "Repo root" },
    ],
    nodes: [
      { id: "cfg", x: 25, y: 50, variant: "accent", label: "config.py" },
      { id: "daemon", x: 25, y: 100, variant: "green", label: "daemon.py" },
      { id: "indexer", x: 25, y: 150, variant: "muted", label: "indexer.py" },
      { id: "planner", x: 25, y: 200, variant: "muted", label: "planner.py" },
      { id: "loop", x: 140, y: 175, variant: "muted", label: "loop.py" },
      { id: "executor", x: 25, y: 250, variant: "muted", label: "executor.py" },
      { id: "judge", x: 140, y: 250, variant: "muted", label: "judge.py" },
      { id: "logdb", x: 25, y: 300, variant: "muted", label: "logging_db.py" },
      { id: "sk", x: 365, y: 50, variant: "muted", label: "skills/" },
      { id: "ag", x: 365, y: 100, variant: "muted", label: "agents/" },
      { id: "sc", x: 365, y: 150, variant: "muted", label: "scripts/" },
      { id: "gfy", x: 365, y: 200, variant: "blue", label: "graphify-out/" },
      { id: "web", x: 365, y: 250, variant: "muted", label: "web/" },
    ],
    edges: [
      { source: "cfg", target: "daemon", color: "muted" },
      { source: "cfg", target: "loop", color: "muted" },
      { source: "indexer", target: "planner", color: "muted" },
      { source: "planner", target: "loop", color: "muted" },
      { source: "loop", target: "executor", color: "muted" },
      { source: "loop", target: "judge", color: "muted" },
      { source: "loop", target: "logdb", color: "muted" },
      { source: "daemon", target: "loop", color: "green" },
      { source: "sk", target: "indexer", color: "accent" },
      { source: "sk", target: "gfy", color: "muted" },
      { source: "sc", target: "gfy", color: "muted" },
      { source: "gfy", target: "web", color: "blue" },
    ],
  },
};
