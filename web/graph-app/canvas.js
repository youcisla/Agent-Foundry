/**
 * Layout wrapper around <ReactFlow>: Background (dots), MiniMap (colored by
 * node color), Controls, and any overlay panels passed as children. Auto-fits
 * the view when `fitKey` changes (mode/data switch). Keeps the React Flow
 * attribution intact (MIT-core requirement).
 */
import {
  html, ReactFlow, Background, BackgroundVariant, MiniMap,
  useEffect, useReactFlow,
} from "./deps.js";
import { nodeTypes } from "./nodes.js";
import { edgeTypes } from "./edges.js";
import { useStore } from "./store.js";

const minimapColor = (n) => (n.data && n.data.color) || "#8b8b95";

export function GraphCanvas({
  nodes, edges, onNodesChange, onNodeClick, onPaneClick,
  onNodeMouseEnter, onNodeMouseLeave, fitKey, children,
}) {
  const rf = useReactFlow();
  const showMinimap = useStore((s) => s.showMinimap);
  useEffect(() => {
    if (!nodes.length) return;
    const top = nodes.reduce((best, n) => {
      const d = (n.data && n.data.degree) || 0;
      return d > best.d ? { n, d } : best;
    }, { n: null, d: -1 });
    const t = setTimeout(() => {
      if (top.n) {
        // Center on the highest-degree node at a readable zoom; user can fit out.
        rf.setCenter(top.n.position.x + 60, top.n.position.y + 20, { zoom: 0.55, duration: 400 });
      } else {
        rf.fitView({ padding: 0.2, duration: 400 });
      }
    }, 300);
    return () => clearTimeout(t);
  }, [fitKey, nodes.length]);

  return html`
    <${ReactFlow}
      nodes=${nodes}
      edges=${edges}
      nodeTypes=${nodeTypes}
      edgeTypes=${edgeTypes}
      onNodesChange=${onNodesChange}
      onNodeClick=${onNodeClick}
      onPaneClick=${onPaneClick}
      onNodeMouseEnter=${onNodeMouseEnter}
      onNodeMouseLeave=${onNodeMouseLeave}
      onlyRenderVisibleElements=${true}
      minZoom=${0.04}
      maxZoom=${2.5}
      nodesConnectable=${false}
      elevateNodesOnSelect=${true}>
      <${Background} variant=${BackgroundVariant.Dots} gap=${28} size=${1} color="#2a2a33" />
      ${showMinimap
        ? html`<${MiniMap} pannable=${true} zoomable=${true} nodeColor=${minimapColor}
                  maskColor="rgba(10,10,11,0.72)" style=${{ background: "#131316", border: "1px solid #2a2a33" }} />`
        : null}
      ${children}
    <//>`;
}
