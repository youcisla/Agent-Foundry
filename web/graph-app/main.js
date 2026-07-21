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
    // Resolve icon-svg placeholders that our components emit (search/close/etc.).
    const paint = () => {
      document.querySelectorAll("#graph-root .icon-svg").forEach((s) => {
        const n = s.textContent.trim();
        if (window.ICONS && window.ICONS[n] && !s.querySelector("svg")) s.innerHTML = window.ICONS[n];
      });
    };
    const mo = new MutationObserver(paint);
    mo.observe(el, { childList: true, subtree: true });
    setTimeout(paint, 300);
  } catch (e) {
    el.innerHTML =
      '<div class="gp-fatal"><strong>Interactive graph failed to initialize.</strong>' +
      '<span>' + (e && e.message ? e.message : "unknown error") + '</span></div>';
  }
}
