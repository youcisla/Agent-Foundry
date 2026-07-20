/**
 * Agent Foundry — tiny framework-free reactive store.
 *
 * First paint uses the data embedded at build time (SKILLS / AGENTS / GRAPH_STATS),
 * so there is no loading flash. startLive() then keeps the UI in sync WITHOUT a
 * manual refresh:
 *   • Production (static hosting): polls data.json + refetches on window focus.
 *   • Local dev: instant push via Server-Sent Events from the FastAPI daemon.
 * Consumers call subscribe(fn) and re-render from get().
 */
(function (global) {
  const listeners = new Set();

  const state = {
    skills: (typeof SKILLS !== "undefined" ? SKILLS : []),
    agents: (typeof AGENTS !== "undefined" ? AGENTS : []),
    skillCount: (typeof SKILL_COUNT !== "undefined" ? SKILL_COUNT : 0),
    agentCount: (typeof AGENT_COUNT !== "undefined" ? AGENT_COUNT : 0),
    graphStats: (typeof GRAPH_STATS !== "undefined" ? GRAPH_STATS : null),
    generatedAt: null,
    live: false,
  };

  function signature(s) {
    return JSON.stringify({
      n: s.skillCount, a: s.agentCount,
      sk: (s.skills || []).map((x) => x.id),
      ag: (s.agents || []).map((x) => x.id),
      g: s.graphStats,
    });
  }
  let lastSig = signature(state);

  function get() { return state; }
  function subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); }
  function notify() { listeners.forEach((fn) => { try { fn(state); } catch (e) { console.error(e); } }); }

  // Merge a data.json payload; returns true and notifies only if something changed.
  function apply(data) {
    if (!data) return false;
    if (Array.isArray(data.skills)) state.skills = data.skills;
    if (Array.isArray(data.agents)) state.agents = data.agents;
    if (typeof data.skill_count === "number") state.skillCount = data.skill_count;
    if (typeof data.agent_count === "number") state.agentCount = data.agent_count;
    if (data.graph_stats) state.graphStats = data.graph_stats;
    if (data.generated_at) state.generatedAt = data.generated_at;
    const sig = signature(state);
    if (sig !== lastSig) { lastSig = sig; notify(); return true; }
    return false;
  }

  async function refetch(url) {
    try {
      const r = await fetch(url, { cache: "no-store" });
      if (!r.ok) return false;
      return apply(await r.json());
    } catch (e) { return false; }
  }

  function startLive(opts) {
    opts = opts || {};
    const dataUrl = opts.dataUrl || "data.json";
    const pollMs = opts.pollMs || 15000;
    const sseUrl = opts.sseUrl || "http://127.0.0.1:8765/events";

    // Local-dev instant updates via SSE (silently ignored in production where the
    // daemon isn't reachable — the connection errors and we lean on polling).
    if ("EventSource" in global) {
      try {
        const es = new EventSource(sseUrl);
        const onChange = () => refetch(dataUrl);
        es.onopen = () => { state.live = true; notify(); };
        es.onmessage = onChange;
        es.addEventListener("changed", onChange);
        es.onerror = () => { es.close(); state.live = false; };
      } catch (e) { /* no-op */ }
    }

    // Production-safe polling + refetch when the tab regains focus.
    setInterval(() => { if (!document.hidden) refetch(dataUrl); }, pollMs);
    global.addEventListener("focus", () => refetch(dataUrl));
    document.addEventListener("visibilitychange", () => { if (!document.hidden) refetch(dataUrl); });
    refetch(dataUrl); // catch anything changed between build and page load
  }

  global.AFStore = { get, subscribe, apply, refetch, startLive, signature };
})(window);
