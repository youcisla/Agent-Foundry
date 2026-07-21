/**
 * Top-level composition. Loads the graph-rf.json contract, adapts it per mode,
 * derives visibility from filters (preserving drag positions), wires selection /
 * hover / inspector, and drives the pipeline simulation. React Flow owns
 * geometry; this owns interaction + domain state (via the app store).
 */
import {
  html, useState, useEffect, useMemo, useCallback, useRef,
} from "./deps.js";
import { toAstGraph, toPipeline } from "./adapters.js";
import { GraphCanvas } from "./canvas.js";
import {
  CanvasControls, FilterPanel, LegendPanel, SimulationControls, NodeInspectorPanel,
} from "./panels.js";
import { useStore, graphStore, nodeMatchesFilters } from "./store.js";
import { startGraphLive } from "./liveSync.js";
import { makeSimulation } from "./simulation.js";
import { communityColor } from "./palette.js";
import { GRAPH_MODES } from "./schema.js";
import { applyNodeChanges } from "./deps.js";

export function GraphApp() {
  const [rf, setRf] = useState(null);
  const [error, setError] = useState(null);
  const mode = useStore((s) => s.mode);
  const filters = useStore((s) => s.filters);
  const selectedId = useStore((s) => s.selectedId);
  const overrides = useRef({}); // id -> {x,y} drag persistence

  // Load the data contract + bind live updates.
  useEffect(() => {
    let alive = true;
    fetch("graph-rf.json", { cache: "no-store" })
      .then((r) => { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then((d) => { if (alive) setRf(d); })
      .catch((e) => { if (alive) setError(e.message || "load failed"); });
    const poll = startGraphLive({ onGraphData: (d) => { if (alive) setRf(d); } });
    return () => { alive = false; };
  }, []);

  // Adapt raw data per mode.
  const astData = useMemo(() => (rf ? toAstGraph(rf) : { nodes: [], edges: [] }), [rf]);
  const pipeData = useMemo(() => (rf ? toPipeline(rf) : { nodes: [], edges: [] }), [rf]);
  const base = mode === GRAPH_MODES.PIPELINE ? pipeData : astData;

  const communities = useMemo(
    () => (rf?.communities || []).map((c) => ({ ...c, _color: communityColor(c.colorIndex ?? c.id, rf.communities.length) })),
    [rf]
  );
  const availableKinds = useMemo(() => {
    const s = new Set();
    base.nodes.forEach((n) => s.add(n.data.kind));
    return [...s].sort();
  }, [base]);

  const nodesById = useMemo(() => {
    const m = {};
    base.nodes.forEach((n) => (m[n.id] = n));
    return m;
  }, [base]);
  const adjacency = useMemo(() => {
    const a = {};
    base.edges.forEach((e) => {
      (a[e.source] = a[e.source] || []).push({ id: e.target, label: (nodesById[e.target]?.data.full) || e.target, relation: e.data.relation });
      (a[e.target] = a[e.target] || []).push({ id: e.source, label: (nodesById[e.source]?.data.full) || e.source, relation: e.data.relation });
    });
    return a;
  }, [base, nodesById]);

  // Controlled RF arrays (rebuilt on mode/data or filter change; positions kept).
  const [rfNodes, setRfNodes] = useState([]);
  const [rfEdges, setRfEdges] = useState([]);
  useEffect(() => {
    const visible = new Set();
    const nodes = base.nodes.map((n) => {
      const show = nodeMatchesFilters(n.data, filters);
      if (show) visible.add(n.id);
      const o = overrides.current[n.id];
      return { ...n, position: o || n.position, hidden: !show };
    });
    const edges = base.edges.map((e) => ({ ...e, hidden: !(visible.has(e.source) && visible.has(e.target)) }));
    setRfNodes(nodes);
    setRfEdges(edges);
  }, [base, filters]);

  const onNodesChange = useCallback((changes) => {
    setRfNodes((nds) => applyNodeChanges(changes, nds));
    changes.forEach((c) => {
      if (c.type === "position" && c.position) overrides.current[c.id] = c.position;
    });
  }, []);

  const onNodeClick = useCallback((_e, node) => {
    const neigh = adjacency[node.id] || [];
    graphStore.getState().selectNode(node.id, neigh.map((n) => n.id));
  }, [adjacency]);
  const onPaneClick = useCallback(() => graphStore.getState().clearSelection(), []);
  const onNodeMouseEnter = useCallback((_e, node) => graphStore.getState().setHover(node.id), []);
  const onNodeMouseLeave = useCallback(() => graphStore.getState().setHover(null), []);
  const onViewSource = useCallback((file) => { if (window.openFile) window.openFile(file, file); }, []);

  // Pipeline simulation controller + step labels.
  const controller = useMemo(() => makeSimulation(() => pipeData.edges), [pipeData]);
  const stepLabels = useMemo(
    () => pipeData.edges.slice().sort((a, b) => (a.data?.step || 0) - (b.data?.step || 0))
      .map((e) => (nodesById[e.source]?.data.label || e.source) + " → " + (nodesById[e.target]?.data.label || e.target)),
    [pipeData, nodesById]
  );

  const selectedNode = selectedId ? nodesById[selectedId] : null;
  const selectedNeighbors = selectedId ? (adjacency[selectedId] || []) : [];

  if (error) {
    return html`<div className="gp-fatal">
      <strong>Interactive graph unavailable.</strong>
      <span>Serve the site over HTTP (e.g. <code>python -m http.server</code>) so the graph data can load, or view the source on
      <a href="https://github.com/youcisla/Agent-Foundry" target="_blank" rel="noopener">GitHub</a>.</span>
    </div>`;
  }
  if (!rf) return html`<div className="gp-loading"><span className="gp-spinner"></span> Loading knowledge graph…</div>`;

  return html`
    <div className="gp-wrap">
      <${GraphCanvas}
        nodes=${rfNodes}
        edges=${rfEdges}
        onNodesChange=${onNodesChange}
        onNodeClick=${onNodeClick}
        onPaneClick=${onPaneClick}
        onNodeMouseEnter=${onNodeMouseEnter}
        onNodeMouseLeave=${onNodeMouseLeave}
        fitKey=${mode + ":" + (rf.generated_at || "")}>
        <${CanvasControls} />
        <${FilterPanel} availableKinds=${availableKinds} />
        ${mode === GRAPH_MODES.AST ? html`<${LegendPanel} communities=${communities} />` : null}
        ${mode === GRAPH_MODES.PIPELINE ? html`<${SimulationControls} controller=${controller} steps=${stepLabels} />` : null}
      <//>
      <${NodeInspectorPanel} node=${selectedNode} neighbors=${selectedNeighbors}
        onSelect=${(id) => graphStore.getState().selectNode(id, (adjacency[id] || []).map((n) => n.id))}
        onViewSource=${onViewSource} />
    </div>`;
}
