/**
 * Shared enums + relationship styling contract. Keeps presentational decisions
 * (edge color, dash, animation) in one place, decoupled from the raw AST data.
 *
 * @typedef {Object} RFNodeData
 * @property {string} label       Display label (truncated)
 * @property {string} full        Untruncated label
 * @property {string} kind        function|class|file|symbol|agent|skill|store|provider
 * @property {number} community   0–43 (or -1 for pipeline nodes)
 * @property {string} color       resolved hex/hsl
 * @property {number} degree      incident-edge count
 * @property {boolean} isGod      top-10 hub flag
 * @property {string} [file]      source path (feeds the in-app viewer)
 * @property {string} [role]      agent role, if kind==="agent"
 *
 * @typedef {Object} RFEdgeData
 * @property {string} relation    calls|imports|references|contains|dispatches|returns|logs|…
 * @property {number} weight      clamped 1–4, drives strokeWidth + flow speed
 * @property {("ast"|"orchestration")} kind
 * @property {boolean} [surprising]
 * @property {number} [step]      ordering for the pipeline simulation
 */

export const AGENT_ROLES = ["orchestrator", "planner", "critic"];

// AST structural relations → muted, static styling.
export const AST_RELATION_STYLE = {
  calls: { stroke: "#f5a623", dash: null },
  imports: { stroke: "#6496ff", dash: null },
  imports_from: { stroke: "#6496ff", dash: "4 3" },
  references: { stroke: "#8b8b95", dash: "4 3" },
  contains: { stroke: "#2a2a33", dash: null },
  extends: { stroke: "#ff6b35", dash: null },
  inherits: { stroke: "#ff6b35", dash: "4 3" },
  method: { stroke: "#8b8b95", dash: null },
  defines: { stroke: "#8b8b95", dash: null },
  indirect_call: { stroke: "#f5a623", dash: "2 4" },
  rationale_for: { stroke: "#4ade80", dash: "1 5" },
  _default: { stroke: "#2a2a33", dash: null },
};

export function astEdgeStyle(relation) {
  return AST_RELATION_STYLE[relation] || AST_RELATION_STYLE._default;
}

// Orchestration relations → animated, accent styling.
export const ORCH_RELATION_STYLE = {
  dispatches: { stroke: "#f5a623" },
  returns: { stroke: "#4ade80" },
  calls: { stroke: "#6496ff" },
  logs: { stroke: "#8b8b95" },
  _default: { stroke: "#f5a623" },
};

export function orchEdgeStyle(relation) {
  return ORCH_RELATION_STYLE[relation] || ORCH_RELATION_STYLE._default;
}

export const GRAPH_MODES = { AST: "ast", PIPELINE: "pipeline" };
