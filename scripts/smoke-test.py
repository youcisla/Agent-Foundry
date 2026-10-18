#!/usr/bin/env python3
"""
smoke-test.py - Verify a harness adapter end-to-end.

What "tested" means (see docs/adapters/README.md):
  1. The install path exists and is readable.
  2. The Agent Foundry indexer builds a valid SkillIndex from it.
  3. The index has 35 skills + 1 fallback = 36 total.
  4. Each skill has non-empty frontmatter (name, description).

Usage:
    python scripts/smoke-test.py claude-code
    python scripts/smoke-test.py hermes
    python scripts/smoke-test.py codex       # dry-run check (no install)

Exit codes:
    0 = all checks passed
    1 = install path missing
    2 = indexer failed
    3 = skill count wrong
    4 = malformed skill(s)
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HOME = Path.home()
HERMES = HOME / ".hermes"
if not HERMES.exists():
    HERMES = HOME / "AppData" / "Local" / "hermes"
KIMI = HOME / ".kimi-code" if (HOME / ".kimi-code").exists() else HOME / ".kimi"

ADAPTER_PATHS = {
    "claude-code":  HOME / ".claude" / "skills",
    "hermes":       HERMES / "skills" / "agent-foundry",
    "codex":        HOME / ".agents" / "skills",
    "cursor":       HOME / ".cursor" / "skills",
    "gemini-cli":   HOME / ".gemini" / "skills",
    "opencode":     HOME / ".config" / "opencode" / "skills",
    "antigravity":  HOME / ".gemini" / "config" / "skills",
    "qwen":         HOME / ".qwen" / "skills",
    "kimi":         KIMI / "skills",
    "openclaw":     HOME / ".openclaw" / "skills" / "agent-foundry",
    "zed":          HOME / ".agents" / "skills",
}

EXPECTED_SKILL_COUNT = 35  # +1 generic-reasoning fallback = 36


def load_indexer():
    """Import agent_foundry.indexer without requiring pip install."""
    repo_root = Path(__file__).resolve().parent.parent
    spec = importlib.util.spec_from_file_location(
        "agent_foundry", repo_root / "agent_foundry" / "__init__.py"
    )
    if spec is None:
        return None, None
    # We need to import the indexer module directly
    import sys
    sys.path.insert(0, str(repo_root))
    from agent_foundry.indexer import build_index
    from agent_foundry.models import SkillManifest
    return build_index, SkillManifest


def check_path(label: str, path: Path) -> bool:
    if not path.exists():
        print(f"  [FAIL] {label}: path does not exist: {path}")
        return False
    print(f"  [ OK ] {label}: exists at {path}")
    return True


def check_indexer(label: str, path: Path) -> tuple[bool, int]:
    build_index, _ = load_indexer()
    if build_index is None:
        print(f"  [SKIP] {label}: agent_foundry not importable")
        return True, -1
    try:
        idx = build_index(path)
    except Exception as exc:
        print(f"  [FAIL] {label}: indexer error: {exc}")
        return False, 0
    n = len(idx.skills)
    print(f"  [ OK ] {label}: indexer built {n} skills")
    return True, n


def managed_skills(path: Path) -> set[str] | None:
    marker = path / ".agent-foundry-installed.json"
    if not marker.exists():
        return None
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
        return set(data.get("skills", []))
    except (OSError, ValueError):
        return set()


def check_managed(label: str, path: Path) -> bool | None:
    names = managed_skills(path)
    if names is None:
        return None
    if len(names) != EXPECTED_SKILL_COUNT:
        print(f"  [FAIL] {label}: manifest has {len(names)}/{EXPECTED_SKILL_COUNT} skills")
        return False
    print(f"  [ OK ] {label}: manifest lists {len(names)} managed skills")
    return True


def check_skill_count(label: str, count: int) -> bool:
    # 35 skills + 1 virtual fallback = 36
    if count == -1:
        return True  # skipped
    if count != EXPECTED_SKILL_COUNT + 1:
        print(f"  [FAIL] {label}: expected {EXPECTED_SKILL_COUNT + 1} skills, got {count}")
        return False
    print(f"  [ OK ] {label}: {count} skills = {EXPECTED_SKILL_COUNT} + 1 fallback")
    return True


def check_frontmatter(label: str, path: Path) -> bool:
    """Every managed SKILL.md must have frontmatter with name + description."""
    build_index, SkillManifest = load_indexer()
    if build_index is None:
        return True
    idx = build_index(path)
    only = managed_skills(path)
    broken = []
    for s in idx.skills:
        if s.id == "generic-reasoning":
            continue
        if only is not None and s.name not in only:
            continue
        if not s.name or not s.description:
            broken.append(s.id)
    if broken:
        print(f"  [FAIL] {label}: {len(broken)} skills missing name/description: {broken[:5]}")
        return False
    print(f"  [ OK ] {label}: all skills have name + description")
    return True


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/smoke-test.py <harness>")
        print(f"  harnesses: {', '.join(ADAPTER_PATHS)}")
        return 64

    harness = sys.argv[1]
    if harness not in ADAPTER_PATHS:
        print(f"Unknown harness: {harness}")
        print(f"  supported: {', '.join(ADAPTER_PATHS)}")
        return 64

    path = ADAPTER_PATHS[harness]
    print(f"\n=== Smoke test: {harness} ===")
    print(f"Path: {path}")
    print()

    ok = True
    if not check_path(harness, path):
        return 1
    print()
    ok2, count = check_indexer(harness, path)
    ok = ok and ok2
    print()
    managed = check_managed(harness, path)
    if managed is False:
        return 3
    if managed is None and not check_skill_count(harness, count):
        return 3
    print()
    if not check_frontmatter(harness, path):
        return 4

    print()
    print(f"=== {harness}: PASS ===" if ok else f"=== {harness}: FAIL ===")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())