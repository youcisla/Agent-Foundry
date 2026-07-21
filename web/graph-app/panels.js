/**
 * Overlay panels rendered inside the React Flow pane via <Panel>. All read the
 * app store through useStore and dispatch via store actions; they hold no graph
 * geometry themselves.
 */
import { html, Panel, useState, useRef, Icon, useReactFlow } from "./deps.js";
import { toPng } from "html-to-image";
import { useStore, shallow, graphStore } from "./store.js";
import { GRAPH_MODES } from "./schema.js";

/* ── Mode toggle + canvas toolbar (single top-left panel — no overlap) ── */
export function CanvasControls() {
  const mode = useStore((s) => s.mode);
  const showMinimap = useStore((s) => s.showMinimap);
  const rf = useReactFlow();
  const set = (m) => graphStore.getState().setMode(m);

  const exportPng = async () => {
    const wrap = document.querySelector("#graph-root .react-flow");
    if (!wrap) return;
    try {
      const url = await toPng(wrap, {
        backgroundColor: "#0a0a0b",
        pixelRatio: 2,
        filter: (n) => !(n.classList && (
          n.classList.contains("gp-panel") ||
          n.classList.contains("react-flow__minimap") ||
          n.classList.contains("react-flow__attribution") ||
          n.classList.contains("gp-inspector")
        )),
      });
      const a = document.createElement("a");
      a.href = url;
      a.download = "agent-foundry-graph.png";
      a.click();
    } catch (e) { console.error("export failed", e); }
  };

  const Tool = (icon, title, onClick, active) => html`
    <button className=${"gp-tool" + (active ? " active" : "")} title=${title} aria-label=${title} onClick=${onClick}>
      <${Icon} name=${icon} />
    </button>`;

  return html`
    <${Panel} position="top-left" className="gp-panel gp-controls">
      <div className="gp-modes">
        <button className=${"gp-seg" + (mode === GRAPH_MODES.AST ? " active" : "")}
                onClick=${() => set(GRAPH_MODES.AST)}>Knowledge graph</button>
        <button className=${"gp-seg" + (mode === GRAPH_MODES.PIPELINE ? " active" : "")}
                onClick=${() => set(GRAPH_MODES.PIPELINE)}>Orchestration</button>
      </div>
      <div className="gp-toolbar">
        ${Tool("fit", "Fit to view", () => rf.fitView({ padding: 0.2, duration: 400 }))}
        ${Tool("plus", "Zoom in", () => rf.zoomIn({ duration: 200 }))}
        ${Tool("minus", "Zoom out", () => rf.zoomOut({ duration: 200 }))}
        ${Tool("refresh", "Reset filters", () => graphStore.getState().resetFilters())}
        ${Tool("map", "Toggle minimap", () => graphStore.getState().toggleMinimap(), showMinimap)}
        ${Tool("download", "Export PNG", exportPng)}
      </div>
    <//>`;
}

/* ── Filter panel (search + kind chips + god-only) ── */
export function FilterPanel({ availableKinds = [] }) {
  const filters = useStore((s) => s.filters, shallow);
  const stats = useStore((s) => s.stats);
  const qTimer = useRef(null);
  const [q, setQ] = useState(filters.query);

  const onSearch = (e) => {
    const v = e.target.value;
    setQ(v);
    clearTimeout(qTimer.current);
    qTimer.current = setTimeout(() => graphStore.getState().setQuery(v), 120);
  };
  const kinds = filters.kinds;
  const total = (stats && stats.node_count) || 0;

  return html`
    <${Panel} position="top-right" className="gp-panel gp-filter">
      <div className="gp-search">
        <span className="gp-search-ic"><${Icon} name="search" /></span>
        <input type="search" placeholder="Search nodes…" value=${q} onInput=${onSearch} />
      </div>
      <div className="gp-chiprow">
        ${availableKinds.map(
          (k) => html`<button key=${k}
            className=${"gp-chip" + (kinds.has(k) ? " active" : "")}
            onClick=${() => graphStore.getState().toggleKind(k)}>${k}</button>`
        )}
      </div>
      <label className="gp-check">
        <input type="checkbox" checked=${filters.godOnly}
               onChange=${(e) => graphStore.getState().setGodOnly(e.target.checked)} />
        Hubs only
      </label>
      <div className="gp-meta">
        <span>${total} nodes</span>
        <button className="gp-link" onClick=${() => { setQ(""); graphStore.getState().resetFilters(); }}>Reset</button>
      </div>
    <//>`;
}

/* ── Community legend (click to isolate) ── */
export function LegendPanel({ communities = [] }) {
  const active = useStore((s) => s.filters.communities, shallow);
  const [open, setOpen] = useState(false);
  const sorted = communities.slice().sort((a, b) => b.size - a.size);
  return html`
    <${Panel} position="bottom-left" className=${"gp-panel gp-legend" + (open ? " open" : "")}>
      <button className="gp-legend-head" onClick=${() => setOpen((o) => !o)}>
        <span>${communities.length} communities</span>
        <span className="gp-legend-caret">${open ? "▾" : "▸"}</span>
      </button>
      ${open
        ? html`<div className="gp-legend-list">
            ${active.size
              ? html`<button className="gp-link" onClick=${() => graphStore.getState().soloCommunity(null)}>Clear isolation</button>`
              : null}
            ${sorted.map(
              (c) => html`<button key=${c.id}
                className=${"gp-legend-row" + (active.has(c.id) ? " active" : "")}
                onClick=${() => graphStore.getState().toggleCommunity(c.id)}>
                <span className="gp-swatch" style=${{ background: c._color || "var(--accent)" }}></span>
                <span className="gp-legend-name">${c.label}</span>
                <span className="gp-legend-size">${c.size}</span>
              </button>`
            )}
          </div>`
        : null}
    <//>`;
}

/* ── Simulation controls (pipeline mode only) ── */
export function SimulationControls({ controller, steps = [] }) {
  const sim = useStore((s) => s.simulation, shallow);
  const stepLabel = sim.step >= 0 && steps[sim.step] ? steps[sim.step] : "idle";
  return html`
    <${Panel} position="bottom-center" className="gp-panel gp-sim">
      <button className="gp-btn" onClick=${() => (sim.running ? controller.pause() : controller.play())}>
        <${Icon} name=${sim.running ? "pause" : "play"} />
        ${sim.running ? "Pause" : sim.done ? "Replay" : "Simulate dispatch"}
      </button>
      <button className="gp-btn ghost" onClick=${() => controller.stepOnce()}>Step</button>
      <button className="gp-btn ghost" onClick=${() => controller.reset()}>Reset</button>
      <div className="gp-sim-status">
        <span className="gp-sim-dot" data-on=${sim.running || sim.step >= 0}></span>
        <span>${stepLabel}</span>
      </div>
    <//>`;
}

/* ── Node inspector (right drawer) ── */
export function NodeInspectorPanel({ node, neighbors = [], onSelect, onViewSource }) {
  const open = useStore((s) => s.sidePanelOpen);
  if (!open || !node) return null;
  const d = node.data;
  const swatch = d.color || "var(--accent)";
  return html`
    <div className="gp-inspector">
      <div className="gp-insp-head">
        <span className="gp-insp-kind" style=${{ "--c": swatch }}>${d.role || d.kind}</span>
        <button className="gp-insp-close" aria-label="Close"
                onClick=${() => graphStore.getState().clearSelection()}>
          <${Icon} name="close" />
        </button>
      </div>
      <h3 className="gp-insp-title">${d.full || d.label}</h3>
      ${d.community >= 0
        ? html`<div className="gp-insp-row"><span className="k">Community</span>
            <span className="v"><span className="gp-swatch" style=${{ background: swatch }}></span>${d.communityLabel}</span></div>`
        : null}
      <div className="gp-insp-row"><span className="k">Degree</span><span className="v">${d.degree} connections</span></div>
      ${d.file
        ? html`<div className="gp-insp-row"><span className="k">File</span>
            <button className="gp-link" onClick=${() => onViewSource && onViewSource(d.file)}>${d.file}<//></div>`
        : null}
      ${d.isGod ? html`<div className="gp-insp-badge">Hub node — refactors here ripple widely</div>` : null}
      <div className="gp-insp-conns">
        <div className="gp-insp-subhead">Connections (${neighbors.length})</div>
        <div className="gp-insp-list">
          ${neighbors.length
            ? neighbors.slice(0, 40).map(
                (n) => html`<button key=${n.id} className="gp-conn"
                  onClick=${() => onSelect && onSelect(n.id)}>
                  <span className="gp-conn-rel">${n.relation}</span>
                  <span className="gp-conn-label">${n.label}</span>
                <//>`
              )
            : html`<div className="gp-empty">No connections</div>`}
        </div>
      </div>
      ${d.file
        ? html`<a className="gp-insp-src" href=${"https://github.com/youcisla/Agent-Foundry/blob/main/" + d.file}
             target="_blank" rel="noopener"><${Icon} name="github" /> Open on GitHub</a>`
        : null}
    </div>`;
}
