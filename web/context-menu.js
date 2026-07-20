/**
 * Agent Foundry — shared right-click context menu.
 * Themed to the brand system, uses the SVG icon set (icons.js), and
 * exposes repo-specific commands. Include on every page AFTER icons.js.
 */
(function () {
  const REPO = "https://github.com/youcisla/Agent-Foundry";
  const INSTALL = "curl -fsSL https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/install.sh | bash";
  const ic = (name) => (window.ICONS && ICONS[name]) || "";

  const items = [
    { icon: "back", label: "Back", run: () => history.back() },
    { icon: "refresh", label: "Reload", run: () => location.reload() },
    { sep: true },
    { icon: "terminal", label: "Copy install command", run: () => copyText(INSTALL, "Install command copied") },
    { icon: "layers", label: "Browse catalog", run: () => (location.href = "catalog.html") },
    { icon: "graph", label: "Open graph", run: () => (location.href = "graph.html") },
    { icon: "shield", label: "Open audit", run: () => (location.href = "audit.html") },
    { sep: true },
    { icon: "link", label: "Copy page link", run: () => copyText(location.href, "Link copied") },
    { icon: "github", label: "Open on GitHub", run: () => window.open(REPO, "_blank", "noopener") },
  ];

  function copyText(text, msg) {
    navigator.clipboard && navigator.clipboard.writeText(text);
    toast(msg);
  }

  let toastEl;
  function toast(msg) {
    if (!toastEl) {
      toastEl = document.createElement("div");
      toastEl.className = "af-toast";
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = msg;
    toastEl.classList.add("show");
    clearTimeout(toastEl._t);
    toastEl._t = setTimeout(() => toastEl.classList.remove("show"), 1600);
  }

  const menu = document.createElement("div");
  menu.id = "af-context-menu";
  menu.setAttribute("role", "menu");
  items.forEach((it, i) => {
    if (it.sep) {
      const s = document.createElement("div");
      s.className = "cm-sep";
      menu.appendChild(s);
      return;
    }
    const el = document.createElement("button");
    el.type = "button";
    el.className = "cm-item";
    el.setAttribute("role", "menuitem");
    el.innerHTML = '<span class="cm-ic">' + ic(it.icon) + "</span><span>" + it.label + "</span>";
    el.addEventListener("click", () => { hide(); it.run(); });
    menu.appendChild(el);
  });

  function place(x, y) {
    menu.style.display = "block";
    const w = menu.offsetWidth || 200;
    const h = menu.offsetHeight || 260;
    menu.style.left = Math.min(x, window.innerWidth - w - 8) + "px";
    menu.style.top = Math.min(y, window.innerHeight - h - 8) + "px";
  }
  function hide() { menu.style.display = "none"; }

  function init() {
    document.body.appendChild(menu);
    document.addEventListener("contextmenu", (e) => { e.preventDefault(); place(e.clientX, e.clientY); });
    document.addEventListener("click", hide);
    document.addEventListener("scroll", hide, true);
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") hide(); });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
