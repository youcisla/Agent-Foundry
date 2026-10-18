"""One version source: package.json. Sync or check every surfaced version.

Usage:
  python scripts/sync-version.py            # sync all files to package.json version
  python scripts/sync-version.py --check    # exit 1 on drift
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def package_version() -> str:
    return json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["version"]


def file_targets(version: str) -> list[tuple[Path, str, str]]:
    """(path, pattern, replacement) triples."""
    return [
        (ROOT / "agent_foundry" / "__init__.py",
         r'(?m)^__version__\s*=\s*"[^"]+"',
         f'__version__ = "{version}"'),
        (ROOT / "pyproject.toml",
         r'(?m)^version\s*=\s*"[^"]+"',
         f'version = "{version}"'),
        (ROOT / ".claude-plugin" / "plugin.json",
         r'("version"\s*:\s*")[^"]+(")',
         rf'\g<1>{version}\g<2>'),
        (ROOT / "claude_code_plugin.json",
         r'("version"\s*:\s*")[^"]+(")',
         rf'\g<1>{version}\g<2>'),
        (ROOT / ".codex-plugin" / "plugin.json",
         r'("version"\s*:\s*")[^"]+(")',
         rf'\g<1>{version}\g<2>'),
        (ROOT / ".cursor-plugin" / "plugin.json",
         r'("version"\s*:\s*")[^"]+(")',
         rf'\g<1>{version}\g<2>'),
        (ROOT / "README.md",
         r"badge/version-[0-9.]+-",
         f"badge/version-{version}-"),
        (ROOT / "web" / "index.html",
         r"v[0-9]+\.[0-9]+\.[0-9]+,",
         f"v{version},"),
        (ROOT / "web" / "demo" / "af-demo" / "index.html",
         r"v[0-9]+\.[0-9]+\.[0-9]+ · MIT",
         f"v{version} · MIT"),
        (ROOT / "server.json",
         r'("version"\s*:\s*")[^"]+(")',
         rf'\g<1>{version}\g<2>'),
    ]


def main() -> int:
    check = "--check" in sys.argv
    version = package_version()
    drift = []
    for path, pattern, replacement in file_targets(version):
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        new = re.sub(pattern, replacement, text)
        if new == text:
            continue
        if check:
            drift.append(str(path.relative_to(ROOT)))
        else:
            path.write_text(new, encoding="utf-8")
    if check and drift:
        print("version drift: " + ", ".join(drift))
        return 1
    if check:
        print(f"versions ok ({version})")
    else:
        print(f"synced {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
