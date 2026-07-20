#!/usr/bin/env python3
"""
graphify-run.py - Full graphify pipeline runner.

Strips PYTHONPATH (set by Hermes' claude-mem MCP) so graphifyy uses its
own site-packages. Runs detect, AST extraction, semantic extraction (via
host agent), merge, build, cluster, label, and writes graph.json.
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
