/**
 * Application store (Tier 2). React Flow keeps geometry/viewport in its own
 * internal store; this holds cross-cutting interaction + domain state:
 * mode, selection, hover, highlight neighborhood, filters, side panel, and the
 * data-flow simulation. Built on zustand/vanilla + a useSyncExternalStore hook
 * so we fully control the React instance (no react/zustand version coupling).
 */
import { createStore } from "zustand/vanilla";
import { useSyncExternalStore, useRef } from "./deps.js";
import { GRAPH_MODES } from "./schema.js";

const emptyFilters = () => ({
  kinds: new Set(),
  communities: new Set(),
  godOnly: false,
  query: "",
});

export const graphStore = createStore((set, get) => ({
  mode: GRAPH_MODES.AST,
  selectedId: null,
  hoverId: null,
  highlightSet: null, // Set<id> of the selected node + neighbors, or null
  filters: emptyFilters(),
  sidePanelOpen: false,
  stats: null,
  simulation: { running: false, step: -1, speed: 1, activeEdgeId: null, activeNodeId: null, done: false },

  setMode: (mode) =>
    set({ mode, selectedId: null, hoverId: null, highlightSet: null, sidePanelOpen: false }),

  selectNode: (id, neighbors) =>
    set({
      selectedId: id,
      highlightSet: id ? new Set([id, ...(neighbors || [])]) : null,
      sidePanelOpen: !!id,
    }),
  clearSelection: () => set({ selectedId: null, highlightSet: null, sidePanelOpen: false }),
  setHover: (id) => set({ hoverId: id }),

  toggleKind: (k) =>
    set((s) => {
      const kinds = new Set(s.filters.kinds);
      kinds.has(k) ? kinds.delete(k) : kinds.add(k);
      return { filters: { ...s.filters, kinds } };
    }),
  toggleCommunity: (c) =>
    set((s) => {
      const communities = new Set(s.filters.communities);
      communities.has(c) ? communities.delete(c) : communities.add(c);
      return { filters: { ...s.filters, communities } };
    }),
  soloCommunity: (c) =>
    set((s) => ({ filters: { ...s.filters, communities: c == null ? new Set() : new Set([c]) } })),
  setGodOnly: (v) => set((s) => ({ filters: { ...s.filters, godOnly: !!v } })),
  setQuery: (q) => set((s) => ({ filters: { ...s.filters, query: q } })),
  resetFilters: () => set({ filters: emptyFilters() }),

  setStats: (stats) => set({ stats }),
  simSet: (patch) => set((s) => ({ simulation: { ...s.simulation, ...patch } })),
}));

/** Shallow object/array equality for object-returning selectors. */
export function shallow(a, b) {
  if (Object.is(a, b)) return true;
  if (typeof a !== "object" || typeof b !== "object" || !a || !b) return false;
  const ka = Object.keys(a), kb = Object.keys(b);
  if (ka.length !== kb.length) return false;
  return ka.every((k) => Object.is(a[k], b[k]));
}

/** useSyncExternalStore-backed selector hook with cached snapshot + equality. */
export function useStore(selector = (s) => s, equals = Object.is) {
  const cache = useRef(undefined);
  const getSnapshot = () => {
    const next = selector(graphStore.getState());
    if (cache.current !== undefined && equals(cache.current, next)) return cache.current;
    cache.current = next;
    return next;
  };
  return useSyncExternalStore(graphStore.subscribe, getSnapshot, getSnapshot);
}

// ── Visibility selectors (derived, not mutating) ──
export function nodeMatchesFilters(data, filters) {
  if (filters.godOnly && !data.isGod) return false;
  if (filters.kinds.size && !filters.kinds.has(data.kind)) return false;
  if (filters.communities.size && !filters.communities.has(data.community)) return false;
  const q = filters.query.trim().toLowerCase();
  if (q) {
    const hay = (data.full + " " + (data.file || "") + " " + (data.communityLabel || "")).toLowerCase();
    if (!hay.includes(q)) return false;
  }
  return true;
}

/** Returns { nodes, edges } with `hidden` flags applied (layout preserved). */
export function applyVisibility(nodes, edges, filters) {
  const visible = new Set();
  const outNodes = nodes.map((n) => {
    const show = nodeMatchesFilters(n.data, filters);
    if (show) visible.add(n.id);
    return n.hidden === !show ? n : { ...n, hidden: !show };
  });
  const outEdges = edges.map((e) => {
    const show = visible.has(e.source) && visible.has(e.target);
    return e.hidden === !show ? e : { ...e, hidden: !show };
  });
  return { nodes: outNodes, edges: outEdges };
}
