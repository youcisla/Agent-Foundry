"""Generate the compact SessionStart skill index (~<=800 tokens).

Run after editing skills:  python scripts/gen-skill-index.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent_foundry.indexer import parse_frontmatter  # noqa: E402


def main() -> int:
    lines = []
    for path in sorted((ROOT / "skills").rglob("SKILL.md")):
        fm = parse_frontmatter(path.read_text(encoding="utf-8")) or {}
        name = path.parent.name
        desc = str(fm.get("description") or "").split(". ")[0].strip()
        lines.append(f"- {name}: {desc[:65].rstrip()}")
    out = ROOT / "hooks" / "skill-index.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(lines)} skills, ~{len(' '.join(lines)) // 4} tokens)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
