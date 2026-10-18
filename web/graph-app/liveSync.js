/**
 * Live data binding for the graph.
 * - Polls graph-rf.json (the build's React Flow data contract) and refetches on
 *   window focus, so a rebuild (new skill / changed AST) updates the canvas.
 * - Opens the local daemon SSE (/events) for instant dev updates; on any static
 *   host the connection simply errors and we lean on polling.
 * The app supplies onGraphData() to re-adapt and reconcile nodes/edges.
 */
import { graphStore } from "./store.js";

export function startGraphLive({ onGraphData, pollMs = 20000, sseUrl = null } = {}) {
  const isLocal = ["localhost", "127.0.0.1", ""].includes(window.location.hostname);
  const wantSse = !!(sseUrl || new URLSearchParams(window.location.search).has("live"));
  const eventsUrl = wantSse && isLocal ? (sseUrl || "http://127.0.0.1:8765/events") : null;
  let lastSig = null;

  async function poll() {
    try {
      const r = await fetch("graph-rf.json", { cache: "no-store" });
      if (!r.ok) return;
      const data = await r.json();
      const s = data.stats || {};
      const sig = (data.generated_at || "") + ":" + s.node_count + ":" + s.edge_count;
      if (sig !== lastSig) {
        lastSig = sig;
        graphStore.getState().setStats(s);
        if (onGraphData) onGraphData(data);
      }
    } catch (e) {
      /* offline / not served over http — ignore */
    }
  }

  if (eventsUrl && "EventSource" in window) {
    fetch(eventsUrl.replace(/\/events$/, "/health"), { cache: "no-store" })
      .then((r) => {
        if (!r.ok) return;
        try {
          const es = new EventSource(eventsUrl);
          const onChange = () => poll();
          es.onmessage = onChange;
          es.addEventListener("changed", onChange);
          es.onerror = () => es.close();
        } catch (e) {
          /* no-op */
        }
      })
      .catch(() => { /* daemon not running */ });
  }

  poll();  // initial load/stats
  setInterval(() => { if (!document.hidden) poll(); }, pollMs);
  window.addEventListener("focus", poll);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) poll(); });
  return poll;
}
