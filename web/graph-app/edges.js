/**
 * Custom edge types.
 * - astEdge: static, muted, styled by relation; thickness from weight; surprising
 *   cross-community edges rendered as accent dashes. Dims when a selection is
 *   active and neither endpoint is in the highlight set.
 * - dispatchEdge: animated orchestration edge; when the simulation marks it
 *   active, a token pulse travels along the path (SVG animateMotion).
 */
import { html, Fragment, BaseEdge, getBezierPath } from "./deps.js";
import { useStore } from "./store.js";
import { astEdgeStyle, orchEdgeStyle } from "./schema.js";

function useEdgeDim(source, target) {
  return useStore((s) => {
    if (s.highlightSet === null) return false;
    return !(s.highlightSet.has(source) || s.highlightSet.has(target));
  });
}

export function AstDependencyEdge(props) {
  const { id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, data = {} } = props;
  const [path] = getBezierPath({ sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition });
  const dim = useEdgeDim(props.source, props.target);
  const st = data.surprising ? { stroke: "#f5a623", dash: "5 4" } : astEdgeStyle(data.relation);
  const style = {
    stroke: st.stroke,
    strokeWidth: data.weight || 1,
    strokeDasharray: st.dash || undefined,
    opacity: dim ? 0.06 : data.surprising ? 0.9 : 0.4,
    transition: "opacity 160ms ease",
  };
  return html`<${BaseEdge} id=${id} path=${path} style=${style} />`;
}

export function DispatchEdge(props) {
  const { id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, data = {} } = props;
  const [path] = getBezierPath({ sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition });
  const active = useStore((s) => s.simulation.activeEdgeId === id);
  const st = orchEdgeStyle(data.relation);
  const style = {
    stroke: st.stroke,
    strokeWidth: active ? 3 : 1.8,
    opacity: active ? 1 : 0.55,
    filter: active ? "drop-shadow(0 0 4px " + st.stroke + ")" : "none",
    transition: "opacity 160ms ease, stroke-width 160ms ease",
  };
  return html`
    <${Fragment}>
      <${BaseEdge} id=${id} path=${path} style=${style} className=${"rf-dispatch" + (active ? " active" : "")} />
      ${active
        ? html`<circle r="4.5" fill=${st.stroke}>
            <animateMotion dur="0.9s" repeatCount="indefinite" path=${path} />
          </circle>`
        : null}
    <//>`;
}

export const edgeTypes = {
  astEdge: AstDependencyEdge,
  dispatchEdge: DispatchEdge,
  animatedDataEdge: DispatchEdge,
};
