#!/usr/bin/env bash
# build-site-data.sh — Regenerate web/site-data.js from live skill/agent frontmatter
# Run before deploying the web app.
set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Use Python to extract frontmatter
cd "$REPO_ROOT"
python3 -c "
import json, os, re, yaml
from pathlib import Path

def _trunc(s, n=140):
    s = ' '.join((s or '').split())
    if len(s) <= n: return s
    cut = s[:n].rsplit(' ', 1)[0].rstrip(',.;:—- ')
    return cut + '\u2026'

base = Path('.')
skills = []
for sm in sorted((base / 'skills').rglob('SKILL.md')):
    text = sm.read_text(encoding='utf-8')
    m = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
    if not m:
        continue
    try:
        fm = yaml.safe_load(m.group(1))
        rid = sm.parent.name
        rel = str(sm.relative_to(base)).replace('\\\\', '/')
        skills.append({
            'id': rid, 'name': fm.get('name', rid),
            'description': _trunc(fm.get('description', '')),
            'category': 'core' if '/core/' in rel else 'optional',
            'lines': text.count(chr(10))
        })
    except Exception:
        pass

agents = []
for ap in sorted((base / 'agents').rglob('AGENT.md')):
    text = ap.read_text(encoding='utf-8')
    m = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
    if not m:
        continue
    try:
        fm = yaml.safe_load(m.group(1))
        rid = ap.parent.name
        agents.append({
            'id': rid, 'name': fm.get('name', rid),
            'description': _trunc(fm.get('description', '')),
            'model': fm.get('model', 'inherit'),
        })
    except Exception:
        pass

skills.sort(key=lambda s: (0 if s['category'] == 'core' else 1, s['id']))

js = '// Auto-generated — DO NOT EDIT (run scripts/build-site-data.sh to refresh)\n\n'
js += 'const SKILLS = ' + json.dumps(skills, indent=2) + ';\n\n'
js += 'const AGENTS = ' + json.dumps(agents, indent=2) + ';\n\n'
js += f'const SKILL_COUNT = {len(skills)};\n'
js += f'const AGENT_COUNT = {len(agents)};\n'

(base / 'web' / 'site-data.js').write_text(js)
print(f'Regenerated web/site-data.js: {len(skills)} skills, {len(agents)} agents')
"
