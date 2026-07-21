#!/usr/bin/env python3
"""
graphify-run.py - Full graphify pipeline runner.

Strips PYTHONPATH so graphifyy uses its own site-packages. Runs detect, AST
extraction, semantic extraction (via host agent), merge, build, cluster,
label, and writes graph.json.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

env = os.environ.copy()
env.pop("PYTHONPATH", None)

PY = r"C:\Users\Y.CHEHBOUB\AppData\Roaming\uv\tools\graphifyy\Scripts\python.exe"
REPO = Path(".").resolve()
OUT = REPO / "graphify-out"
OUT.mkdir(exist_ok=True)
(OUT / ".graphify_root").write_text(str(REPO), encoding="utf-8")

# Cross-platform Python discovery — used if `uv tool install` is unavailable.
#   1. AGENT_FOUNDRY_PY env var (preferred override)
#   2. .venv in the repo (created by 'uv venv' or 'python -m venv')
#   3. system python / python3 on PATH
def _discover_python() -> str:
    import shutil
    venv = REPO / ".venv"
    candidates = [
        os.environ.get("AGENT_FOUNDRY_PY"),
        str(venv / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")),
        shutil.which("python3"),
        shutil.which("python"),
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    raise SystemExit("No python interpreter found. Set AGENT_FOUNDRY_PY or install Python 3.11+.")

# Validate the hardcoded Windows path; fall back to discovery if missing.
if not Path(PY).exists():
    print(f"Default python ({PY}) not found; running cross-platform discovery...")
    PY = _discover_python()

(OUT / ".graphify_python").write_text(PY, encoding="utf-8")
print(f"Using Python: {PY}")

# Load gitignore patterns to filter out untracked files
_GITIGNORE_PATTERNS: list[str] | None = None
def _load_gitignore() -> list[str]:
    global _GITIGNORE_PATTERNS
    if _GITIGNORE_PATTERNS is not None:
        return _GITIGNORE_PATTERNS
    patterns = []
    gi = REPO / ".gitignore"
    if gi.exists():
        for line in gi.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    _GITIGNORE_PATTERNS = patterns
    return patterns

def _is_gitignored(path: Path) -> bool:
    """Check if a path matches a .gitignore pattern."""
    try:
        rel = str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return False
    for pat in _load_gitignore():
        # Strip leading / for matching
        p = pat.lstrip("/")
        # Directory patterns ending in /
        if p.endswith("/"):
            if p.rstrip("/") in rel.split("/"):
                return True
            continue
        # Exact file match or glob
        if "*" in p:
            import fnmatch
            if fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(rel.split("/")[-1], p):
                return True
        elif p in rel or rel.startswith(p + "/") or rel == p:
            return True
        # Pattern with leading /
        if pat.startswith("/"):
            if rel.startswith(pat.lstrip("/")):
                return True
    return False

PY = r"C:\Users\Y.CHEHBOUB\AppData\Roaming\uv\tools\graphifyy\Scripts\python.exe"
REPO = Path(".").resolve()
OUT = REPO / "graphify-out"
OUT.mkdir(exist_ok=True)
(OUT / ".graphify_python").write_text(PY, encoding="utf-8")
(OUT / ".graphify_root").write_text(str(REPO), encoding="utf-8")


def run(*args, label=None, check=True, cwd=None):
    if label:
        print(f"--- {label} ---")
    r = subprocess.run([PY, *args], cwd=cwd or REPO, env=env, capture_output=True, text=True)
    if r.returncode != 0 and check:
        print("STDOUT:", r.stdout[-2000:])
        print("STDERR:", r.stderr[-2000:])
        sys.exit(1)
    if r.stdout:
        print(r.stdout.strip())
    return r


# Step 2: detect
print("=== Step 2: Detect ===")
r = run("-c", """
import json
from graphify.detect import detect
from pathlib import Path
result = detect(Path('.'))
print(json.dumps(result, ensure_ascii=False))
""", label="detect")
(OUT / ".graphify_detect.json").write_text(r.stdout, encoding="utf-8")
d = json.loads(r.stdout)
print(f"  total: {d['total_files']} files, ~{d['total_words']} words")
# Filter out gitignored files from the detect output
for cat in list(d["files"].keys()):
    d["files"][cat] = [f for f in d["files"][cat] if not _is_gitignored(Path(f))]
d["total_files"] = sum(len(v) for v in d["files"].values())
(OUT / ".graphify_detect.json").write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"  after gitignore filter: {d['total_files']} files")
for cat in ("code", "document", "paper", "image", "video"):
    n = len(d["files"].get(cat, []))
    if n:
        print(f"  {cat:10} {n} files")

# Step 3 Part A: AST
print("\n=== Step 3 Part A: AST extraction ===")
r = run("-c", """
import sys, json
from graphify.extract import collect_files, extract
from pathlib import Path

code_files = []
d = json.loads(open('graphify-out/.graphify_detect.json').read())
for f in d.get('files', {}).get('code', []):
    p = Path(f)
    code_files.extend(collect_files(p) if p.is_dir() else [p])

if code_files:
    result = extract(code_files, cache_root=Path('.'))
    Path('graphify-out/.graphify_ast.json').write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8'
    )
    print(f'AST: {len(result["nodes"])} nodes, {len(result["edges"])} edges')
else:
    Path('graphify-out/.graphify_ast.json').write_text(
        json.dumps({'nodes':[],'edges':[],'input_tokens':0,'output_tokens':0}, ensure_ascii=False),
        encoding='utf-8'
    )
    print('  no code files')
""", label="ast")

# Step 3 Part B: semantic (host agent does this — for now write empty)
print("\n=== Step 3 Part B: semantic extraction (skipped - no LLM key) ===")
run("-c", """
import json
from pathlib import Path
Path('graphify-out/.graphify_semantic.json').write_text(
    json.dumps({'nodes':[],'edges':[],'hyperedges':[],'input_tokens':0,'output_tokens':0}, ensure_ascii=False),
    encoding='utf-8')
print('  empty semantic file (no GEMINI key, host agent not dispatched)')
""", label="semantic (empty)")

# Step 3 Part C: merge
print("\n=== Step 3 Part C: merge AST + semantic ===")
run("-c", """
import json
from pathlib import Path

ast = json.loads(Path('graphify-out/.graphify_ast.json').read_text(encoding='utf-8'))
sem = json.loads(Path('graphify-out/.graphify_semantic.json').read_text(encoding='utf-8'))

seen = {n['id'] for n in ast['nodes']}
merged_nodes = list(ast['nodes'])
for n in sem['nodes']:
    if n['id'] not in seen:
        merged_nodes.append(n)
        seen.add(n['id'])

merged_edges = ast['edges'] + sem['edges']
merged_hyperedges = sem.get('hyperedges', [])
merged = {
    'nodes': merged_nodes,
    'edges': merged_edges,
    'hyperedges': merged_hyperedges,
    'input_tokens': sem.get('input_tokens', 0),
    'output_tokens': sem.get('output_tokens', 0),
}
Path('graphify-out/.graphify_extract.json').write_text(
    json.dumps(merged, indent=2, ensure_ascii=False), encoding='utf-8')
total = len(merged_nodes)
edges = len(merged_edges)
print(f'  merged: {total} nodes, {edges} edges')
""", label="merge")

# Step 4: build + cluster
print("\n=== Step 4: build + cluster ===")
r = run("-c", """
import sys, json
from graphify.build import build_from_json
from graphify.cluster import cluster, score_all
from graphify.analyze import god_nodes, surprising_connections, suggest_questions
from graphify.report import generate
from graphify.export import to_json
from pathlib import Path

extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text(encoding='utf-8'))
detection  = json.loads(Path('graphify-out/.graphify_detect.json').read_text(encoding='utf-8'))

G = build_from_json(extraction, root='.', directed=False)
if G.number_of_nodes() == 0:
    print('ERROR: empty graph')
    raise SystemExit(1)
communities = cluster(G)
cohesion = score_all(G, communities)
tokens = {'input': extraction.get('input_tokens', 0), 'output': extraction.get('output_tokens', 0)}
gods = god_nodes(G)
surprises = surprising_connections(G, communities)
labels = {cid: 'Community ' + str(cid) for cid in communities}
questions = suggest_questions(G, communities, labels)

wrote = to_json(G, communities, 'graphify-out/graph.json')
if not wrote:
    print('ERROR: refused to shrink graph.json')
    raise SystemExit(1)
report = generate(G, communities, cohesion, labels, gods, surprises, detection, tokens, '.', suggested_questions=questions)
Path('graphify-out/GRAPH_REPORT.md').write_text(report, encoding='utf-8')
analysis = {
    'communities': {str(k): v for k, v in communities.items()},
    'cohesion': {str(k): v for k, v in cohesion.items()},
    'gods': gods,
    'surprises': surprises,
    'questions': questions,
}
Path('graphify-out/.graphify_analysis.json').write_text(
    json.dumps(analysis, indent=2, ensure_ascii=False), encoding='utf-8')
print(f'  graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, {len(communities)} communities')
""", label="build+cluster")

# Step 4.5: health
print("\n=== Step 4.5: graph health check ===")
run("-c", """
import json
from pathlib import Path
from graphify.diagnostics import diagnose_extraction, format_diagnostic_report

extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text(encoding='utf-8'))
summary = diagnose_extraction(extraction, directed=False, root='.')
print(format_diagnostic_report(summary))
""", label="health", check=False)

print("\n=== Pipeline complete ===")
print("  outputs in graphify-out/:")
print("    - graph.json     (raw graph)")
print("    - GRAPH_REPORT.md (audit report)")
print("    - .graphify_analysis.json (god nodes, communities, questions)")
