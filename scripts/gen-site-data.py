"""Generate web/ assets from live repo state."""
import json
import re
from pathlib import Path

REPO = Path(r"C:\Users\Y.CHEHBOUB\PERSONAL__DO_NOT_TOUCH\Agent-Foundry")
WEB = REPO / "web"


def parse_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n?(.*)", text, re.DOTALL)
    if not m:
        return None, text
    fm = {}
    for line in m.group(1).split("\n"):
        if ":" in line and not line.startswith((" ", "-")):
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm, m.group(2)


# 1. site-data.js
skills = []
for sm in sorted((REPO / "skills").rglob("SKILL.md")):
    text = sm.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    if not fm:
        continue
    rid = sm.parent.name
    rel = str(sm.relative_to(REPO)).replace("\\", "/")
    skills.append({
        "id": rid,
        "name": fm.get("name", rid),
        "description": fm.get("description", ""),
        "category": "core" if "/core/" in rel else "optional",
        "lines": text.count(chr(10)),
        "version": fm.get("version", "0.1.0"),
        "author": fm.get("author", "Agent Foundry Contributors"),
    })

agents = []
for ap in sorted((REPO / "agents").rglob("AGENT.md")):
    text = ap.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    if not fm:
        continue
    agents.append({
        "id": ap.parent.name,
        "name": fm.get("name", ap.parent.name),
        "description": fm.get("description", ""),
        "model": fm.get("model", "inherit"),
    })

(WEB / "site-data.js").write_text(
    "// Auto-generated from skills/ SKILL.md and agents/ AGENT.md frontmatter.\n"
    "// DO NOT EDIT. Regenerate via scripts/build-site-data.sh.\n\n"
    f"const SKILLS = {json.dumps(skills, indent=2)};\n\n"
    f"const AGENTS = {json.dumps(agents, indent=2)};\n\n"
    f"const SKILL_COUNT = {len(skills)};\n"
    f"const AGENT_COUNT = {len(agents)};\n",
    encoding="utf-8",
)
print(f"site-data.js: {len(skills)} skills, {len(agents)} agents")

# 2. graph-data.js + graph-stats.js
graph_path = REPO / "graphify-out" / "graph.json"
analysis_path = REPO / "graphify-out" / ".graphify_analysis.json"

def _empty_graph_files():
    """Write empty graph assets so the web app doesn't 404 when graphify hasn't run yet."""
    (WEB / "graph-data.js").write_text(
        "// Empty graph (no graphify-out yet). Run python scripts/graphify-run.py to populate.\n\n"
        "const GRAPH_NODES = [];\n\n"
        "const GRAPH_EDGES = [];\n",
        encoding="utf-8",
    )
    empty_stats = {
        "node_count": 0, "edge_count": 0,
        "skill_count": len(skills), "agent_count": len(agents),
        "community_count": 0, "god_nodes": [], "surprising": [],
    }
    (WEB / "graph-stats.js").write_text(
        "const GRAPH_STATS = " + json.dumps(empty_stats, indent=2) + ";\n",
        encoding="utf-8",
    )
    print("graph-data.js + graph-stats.js: stub (no graphify-out yet)")


if graph_path.exists() and analysis_path.exists():
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))

    nodes_js = []
    for n in graph.get("nodes", []):
        label = n.get("label", n.get("id", ""))
        nodes_js.append({
            "id": n["id"],
            "label": (label[:40] + "...") if len(label) > 40 else label,
            "title": n.get("title", n.get("label", n["id"])),
            "group": str(n.get("community", "default")),
        })

    edges_js = []
    for e in graph.get("links", graph.get("edges", [])):
        edges_js.append({
            "from": e.get("source", ""),
            "to": e.get("target", ""),
            "label": e.get("relation", e.get("type", "")),
            "arrows": "to",
        })

    (WEB / "graph-data.js").write_text(
        "// Knowledge graph for the web app. Run scripts/build-site-data.sh after graphify-run.py to refresh.\n\n"
        f"const GRAPH_NODES = {json.dumps(nodes_js)};\n\n"
        f"const GRAPH_EDGES = {json.dumps(edges_js)};\n",
        encoding="utf-8",
    )
    print(f"graph-data.js: {len(nodes_js)} nodes, {len(edges_js)} edges")

    stats = {
        "node_count": len(nodes_js),
        "edge_count": len(edges_js),
        "skill_count": len(skills),
        "agent_count": len(agents),
        "community_count": len(analysis.get("communities", {})),
        "god_nodes": [
            {"label": g["label"], "degree": g["degree"]}
            for g in analysis.get("gods", [])[:10]
        ],
        "surprising": [
            {"source": s.get("source", ""), "target": s.get("target", ""), "relation": s.get("relation", "")}
            for s in analysis.get("surprises", [])[:10]
        ],
    }
    (WEB / "graph-stats.js").write_text(
        "const GRAPH_STATS = " + json.dumps(stats, indent=2) + ";\n",
        encoding="utf-8",
    )
    print(f"graph-stats.js: stats written")
else:
    _empty_graph_files()

# 3. install-data.js
install_data = {
    "core": "curl -fsSL https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/install.sh | bash",
    "coreProfile": "AF_PROFILE=core curl -fsSL https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/install.sh | bash",
    "fullProfile": "AF_PROFILE=full curl -fsSL https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/install.sh | bash",
    "minimalProfile": "AF_PROFILE=minimal curl -fsSL https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/install.sh | bash",
    "gitClone": "git clone https://github.com/youcisla/Agent-Foundry.git ~/.agent-foundry && cd ~/.agent-foundry && pip install -e .",
    "claudeCode": "/plugin marketplace add youcisla/Agent-Foundry\n/plugin install agent-foundry",
    "npm": "npm i -g agent-foundry",
}
(WEB / "install-data.js").write_text(
    "const INSTALL_COMMANDS = " + json.dumps(install_data, indent=2) + ";\n",
    encoding="utf-8",
)
print(f"install-data.js: written")
print("done.")
