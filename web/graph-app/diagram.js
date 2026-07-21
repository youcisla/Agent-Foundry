/**
 * Self-mounting embedded React Flow diagrams. Finds every [data-rf-diagram]
 * element on the page and renders the matching spec as a small, non-interactive
 * (pan/zoom-button) canvas. Replaces the static D2 SVGs. No build step.
 */
import {
  html, createRoot, ReactFlow, ReactFlowProvider, Background, BackgroundVariant,
  Handle, Position, memo, useMemo,
} from "./deps.js";
import { DIAGRAMS } from "./diagram-specs.js";

const COLOR = { accent: "#f5a623", green: "#4ade80", blue: "#6496ff", muted: "#8b8b95", io: "#f5a623", group: "#2a2a33" };

const BoxNode = memo(function BoxNode({ data }) {
  const c = COLOR[data.variant] || "#8b8b95";
  if (data.variant === "group") {
    return html`<div className="dg-group" style=${{ width: data.w + "px", height: data.h + "px", "--c": COLOR[data.color] || "#2a2a33" }}>
      <span className="dg-group-label">${data.label}</span>
    </div>`;
  }
  const tPos = data.dir === "TB" ? Position.Top : Position.Left;
  const sPos = data.dir === "TB" ? Position.Bottom : Position.Right;
  return html`
    <div className=${"dg-box dg-" + (data.variant || "muted") + (data.io ? " dg-io" : "")} style=${{ "--c": c }}>
      <${Handle} type="target" position=${tPos} className="dg-h" isConnectable=${false} />
      <span className="dg-box-label">${data.label}</span>
      ${data.sub ? html`<span className="dg-box-sub">${data.sub}</span>` : null}
      <${Handle} type="source" position=${sPos} className="dg-h" isConnectable=${false} />
    </div>`;
});
const nodeTypes = { box: BoxNode };

function Diagram({ spec }) {
  const nodes = useMemo(() => [
    ...(spec.groups || []).map((g, i) => ({
      id: "g" + i, type: "box", position: { x: g.x, y: g.y }, draggable: false, selectable: false, zIndex: 0,
      data: { variant: "group", label: g.label, w: g.w, h: g.h, color: g.color },
    })),
    ...spec.nodes.map((n) => ({
      id: n.id, type: "box", position: { x: n.x, y: n.y }, draggable: false, zIndex: 1,
      data: { variant: n.variant || "muted", label: n.label, sub: n.sub, io: n.variant === "io", dir: spec.dir || "LR" },
    })),
  ], [spec]);

  const edges = useMemo(() => (spec.edges || []).map((e, i) => {
    const stroke = COLOR[e.color] || "#8b8b95";
    return {
      id: "e" + i, source: e.source, target: e.target, label: e.label, animated: !!e.animated, type: "default",
      style: { stroke, strokeWidth: 1.6, strokeDasharray: e.dashed ? "5 4" : undefined },
      labelStyle: { fill: "#c9c9d0", fontSize: 10, fontFamily: "var(--font-mono)" },
      labelBgStyle: { fill: "#131316", fillOpacity: 0.9 }, labelBgPadding: [4, 2], labelBgBorderRadius: 4,
      markerEnd: { type: "arrowclosed", color: stroke, width: 16, height: 16 },
    };
  }), [spec]);

  return html`
    <${ReactFlow} nodes=${nodes} edges=${edges} nodeTypes=${nodeTypes}
      fitView fitViewOptions=${{ padding: 0.15 }}
      nodesDraggable=${false} nodesConnectable=${false} elementsSelectable=${false}
      zoomOnScroll=${false} panOnScroll=${false} zoomOnDoubleClick=${false}
      panOnDrag=${true} preventScrolling=${false} minZoom=${0.2} maxZoom=${2}>
      <${Background} variant=${BackgroundVariant.Dots} gap=${22} size=${1} color="#22222a" />
    <//>`;
}

function mountAll() {
  document.querySelectorAll("[data-rf-diagram]").forEach((el) => {
    const spec = DIAGRAMS[el.getAttribute("data-rf-diagram")];
    if (!spec) { el.innerHTML = '<div class="dg-fallback">Diagram unavailable.</div>'; return; }
    el.classList.add("rf-diagram-mounted");
    try {
      createRoot(el).render(html`<${ReactFlowProvider}><${Diagram} spec=${spec} /><//>`);
    } catch (e) {
      el.innerHTML = '<div class="dg-fallback">Diagram failed to load.</div>';
    }
  });
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mountAll);
else mountAll();
