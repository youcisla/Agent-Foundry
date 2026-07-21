/**
 * Entry point. Mounts the graph app into #graph-root, wrapped in
 * ReactFlowProvider. Populates any static .icon-svg placeholders inside the
 * React subtree after mount, and clears the module-load watchdog in graph.html.
 */
import { createRoot, html, ReactFlowProvider } from "./deps.js";
import { GraphApp } from "./app.js";

const el = document.getElementById("graph-root");
if (el) {
  window.__afGraphLoaded = true; // signal to graph.html's fallback watchdog
  try {
    createRoot(el).render(html`<${ReactFlowProvider}><${GraphApp} /><//>`);
  } catch (e) {
    el.innerHTML =
      '<div class="gp-fatal"><strong>Interactive graph failed to initialize.</strong>' +
      '<span>' + (e && e.message ? e.message : "unknown error") + '</span></div>';
  }
}
