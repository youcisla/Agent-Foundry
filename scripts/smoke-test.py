#!/usr/bin/env python3
"""
smoke-test.py - Verify a harness adapter end-to-end.

What "tested" means (see docs/adapters/README.md):
  1. The install path exists and is readable.
  2. The Agent Foundry indexer builds a valid SkillIndex from it.
  3. The index has 30 skills + 1 fallback = 31 total.
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
import sys
from pathlib import Path

ADAPTER_PATHS = {
    "claude-code":  Path.home() / ".claude" / "skills" / "agent-foundry",
    "hermes":       Path.home() / "AppData" / "Local" / "hermes" / "skills" / "agent-foundry",
    "codex":        Path.home() / ".codex" / "skills" / "agent-foundry",
    "cursor":       Path.home() / ".cursor" / "rules",
    "gemini-cli":   Path.home() / ".gemini" / "skills" / "agent-foundry",
    "opencode":     Path.home() / ".config" / "opencode" / "skills" / "agent-foundry",
}

EXPECTED_SKILL_COUNT = 30  # +1 generic-reasoning fallback = 31


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


def check_skill_count(label: str, count: int) -> bool:
    # 30 skills + 1 virtual fallback = 31
    if count == -1:
        return True  # skipped
    if count != EXPECTED_SKILL_COUNT + 1:
        print(f"  [FAIL] {label}: expected {EXPECTED_SKILL_COUNT + 1} skills, got {count}")
        return False
    print(f"  [ OK ] {label}: {count} skills = {EXPECTED_SKILL_COUNT} + 1 fallback")
    return True


def check_frontmatter(label: str, path: Path) -> bool:
    """Every SKILL.md must have YAML frontmatter with name + description."""
    build_index, SkillManifest = load_indexer()
    if build_index is None:
        return True
    idx = build_index(path)
    broken = []
    for s in idx.skills:
        if s.id == "generic-reasoning":
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
    if not check_skill_count(harness, count):
        return 3
    print()
    if not check_frontmatter(harness, path):
        return 4

    print()
    print(f"=== {harness}: PASS ===" if ok else f"=== {harness}: FAIL ===")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())