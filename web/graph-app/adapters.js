/**
 * Pure transforms: graph-rf.json → React Flow node/edge arrays.
 * No React, no side effects. One adapter per graph mode.
 */
import { communityColor, KIND_COLORS, ROLE_COLORS } from "./palette.js";

const truncate = (s, n = 44) => (s && s.length > n ? s.slice(0, n) + "…" : s || "");
const clampWeight = (w) => Math.max(1, Math.min(4, Math.round(w || 1)));

/** Build the AST knowledge graph (≈396 nodes / 626 edges, 44 communities). */
export function toAstGraph(rf) {
  const layout = rf.layout || {};
  const communities = rf.communities || [];
  const total = communities.length || 44;
  const colorById = {};
  const labelById = {};
  communities.forEach((c) => {
    colorById[c.id] = communityColor(c.colorIndex ?? c.id, total);
    labelById[c.id] = c.label || "Community " + c.id;
  });

  const nodes = rf.nodes.map((n) => {
    const p = layout[n.id] || [0, 0];
    return {
      id: n.id,
      type: "symbolNode",
      position: { x: p[0], y: p[1] },
      draggable: true,
      data: {
        label: truncate(n.label),
        full: n.label,
        title: n.title || n.label,
        kind: n.kind,
        file: n.file || "",
        loc: n.loc || "",
        community: n.community,
        communityLabel: labelById[n.community] || "Community " + n.community,
        color: colorById[n.community] || "#8b8b95",
        degree: n.degree || 0,
        isGod: !!n.isGod,
      },
    };
  });

  const edges = rf.edges.map((e, i) => ({
    id: "e" + i,
    source: e.source,
    target: e.target,
    type: "astEdge",
    animated: false,
    data: {
      relation: e.relation,
      weight: clampWeight(e.weight),
      surprising: !!e.surprising,
      kind: "ast",
    },
  }));

  return { nodes, edges };
}

// Fixed left-to-right layout for the orchestration pipeline.
const PIPE_POS = {
  prompt: [0, 0],
  "af-orchestrator": [260, 0],
  "af-planner": [520, -110],
  executor: [780, 0],
  provider: [1040, -110],
  "af-critic": [780, 150],
  db: [1040, 150],
  response: [1300, 20],
};
const PIPE_TYPE = {
  input: "symbolNode",
  output: "symbolNode",
  agent: "agentNode",
  symbol: "symbolNode",
  provider: "providerNode",
  store: "databaseNode",
  skill: "skillNode",
};

/** Build the interactive orchestration pipeline (8 nodes, animated dispatch). */
export function toPipeline(rf) {
  const P = rf.pipeline || { nodes: [], edges: [] };
  const nodes = P.nodes.map((n) => {
    const p = PIPE_POS[n.id] || [0, 0];
    return {
      id: n.id,
      type: PIPE_TYPE[n.kind] || "symbolNode",
      position: { x: p[0], y: p[1] },
      draggable: true,
      data: {
        label: n.label,
        full: n.label,
        title: n.label,
        kind: n.kind,
        role: n.role || null,
        io: n.kind === "input" ? "in" : n.kind === "output" ? "out" : null,
        color: (n.role && ROLE_COLORS[n.role]) || KIND_COLORS[n.kind] || "#8b8b95",
        community: -1,
        degree: 0,
        isGod: false,
        pipeline: true,
      },
    };
  });
  const edges = P.edges.map((e, i) => ({
    id: "p" + i,
    source: e.source,
    target: e.target,
    type: "dispatchEdge",
    animated: true,
    data: { relation: e.relation, step: e.step || i + 1, kind: "orchestration", weight: 2 },
  }));
  return { nodes, edges };
}
