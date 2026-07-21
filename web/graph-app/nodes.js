/**
 * Custom node types. Each is memoized and subscribes only to its own
 * highlight/dim/hover slice (shallow-compared), so a selection change re-renders
 * only the nodes whose visual state actually flips — critical at ~400 nodes.
 */
import { html, memo, Handle, Position } from "./deps.js";
import { useStore, shallow, graphStore } from "./store.js";

function useVisual(id) {
  return useStore(
    (s) => ({
      dim: s.highlightSet !== null && !s.highlightSet.has(id),
      hi: s.highlightSet !== null && s.highlightSet.has(id),
      hovered: s.hoverId === id,
      active: s.simulation.activeNodeId === id,
    }),
    shallow
  );
}

function cls(base, v, selected, extra) {
  return [
    base,
    selected ? "is-selected" : "",
    v.hi ? "is-hi" : "",
    v.dim ? "is-dim" : "",
    v.hovered ? "is-hover" : "",
    v.active ? "is-active" : "",
    extra || "",
  ]
    .filter(Boolean)
    .join(" ");
}

const H = (pos, type) => html`<${Handle} type=${type} position=${pos} className="rf-h" isConnectable=${false} />`;

/** AST code symbol (also renders pipeline input/output pills). */
export const SymbolNode = memo(function SymbolNode({ id, data, selected }) {
  const v = useVisual(id);
  const io = data.io ? " rf-io rf-io-" + data.io : "";
  const size = 8 + Math.min((data.degree || 0) * 0.5, 14);
  return html`
    <div className=${cls("rf-node rf-symbol", v, selected, (data.isGod ? "is-god" : "") + io)}
         style=${{ "--c": data.color }} title=${data.title}>
      ${H(Position.Left, "target")}
      <span className="rf-dot" style=${{ width: size + "px", height: size + "px" }}></span>
      <span className="rf-label">${data.label}</span>
      ${data.isGod ? html`<span className="rf-god">hub</span>` : null}
      ${H(Position.Right, "source")}
    </div>`;
});

/** Agent (planner / critic / orchestrator). */
export const AgentNode = memo(function AgentNode({ id, data, selected }) {
  const v = useVisual(id);
  return html`
    <div className=${cls("rf-node rf-agent", v, selected, "role-" + (data.role || "agent"))}
         style=${{ "--c": data.color }} title=${data.title}>
      ${H(Position.Left, "target")}
      <span className="rf-kind">${data.role || "agent"}</span>
      <span className="rf-label">${data.label}</span>
      ${H(Position.Right, "source")}
    </div>`;
});

export const SkillNode = memo(function SkillNode({ id, data, selected }) {
  const v = useVisual(id);
  return html`
    <div className=${cls("rf-node rf-skill", v, selected)} style=${{ "--c": data.color }} title=${data.title}>
      ${H(Position.Left, "target")}
      <span className="rf-kind">skill</span>
      <span className="rf-label">${data.label}</span>
      ${H(Position.Right, "source")}
    </div>`;
});

export const DatabaseNode = memo(function DatabaseNode({ id, data, selected }) {
  const v = useVisual(id);
  return html`
    <div className=${cls("rf-node rf-db", v, selected)} style=${{ "--c": data.color }} title=${data.title}>
      ${H(Position.Left, "target")}
      <span className="rf-db-top"></span>
      <span className="rf-label">${data.label}</span>
      ${H(Position.Right, "source")}
    </div>`;
});

export const ProviderNode = memo(function ProviderNode({ id, data, selected }) {
  const v = useVisual(id);
  return html`
    <div className=${cls("rf-node rf-provider", v, selected)} style=${{ "--c": data.color }} title=${data.title}>
      ${H(Position.Left, "target")}
      <span className="rf-label">${data.label}</span>
      ${H(Position.Right, "source")}
    </div>`;
});

/** Optional cluster container used in community "cluster mode". */
export const CommunityGroup = memo(function CommunityGroup({ data }) {
  return html`
    <div className="rf-community" style=${{ "--c": data.color }}>
      <span className="rf-community-label">${data.label}</span>
    </div>`;
});

export const nodeTypes = {
  symbolNode: SymbolNode,
  agentNode: AgentNode,
  skillNode: SkillNode,
  databaseNode: DatabaseNode,
  providerNode: ProviderNode,
  communityGroup: CommunityGroup,
};
