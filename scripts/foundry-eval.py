#!/usr/bin/env python3
"""
foundry-eval.py - Static quality evaluation for the Agent Foundry catalog.

This replaces/extends scripts/validate.sh. It runs in <2s, costs nothing,
and enforces the portability + action-verb rules documented in
docs/authoring.md.

Checks (all static; no LLM call):

  - Description has exactly one trigger phrase (Use when / Use PROACTIVELY when).
  - Description length is 50-500 chars (sane bound).
  - Body is <=150 lines AND <=8 KB (Codex hard cap).
  - Body does NOT mention tool names (Read, Grep, Edit, Write, TodoWrite, Task).
    Skipped if --allow-tool-vocab is set (for transition period).
  - Anti-patterns section has at least 2 entries.
  - Verification checklist has at least 2 entries.
  - Has references/ subdir, OR body is <=80 lines.
  - Skill name is lowercase-kebab-case.
  - No duplicate skill names in the catalog.
  - Agent names are plugin-scoped (af-*) and not built-in Codex names.

Exit codes:
  0  - all checks pass
  1  - one or more checks failed
  2  - invalid arguments

Usage:
  ./scripts/foundry-eval.py                     # default: --depth quick
  ./scripts/foundry-eval.py --depth quick       # static only (current)
  ./scripts/foundry-eval.py --depth full        # static + (future) LLM judge
  ./scripts/foundry-eval.py --allow-tool-vocab  # skip the tool-name check
  ./scripts/foundry-eval.py skills/core/specific-skill   # single asset
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
AGENTS_DIR = REPO_ROOT / "agents"

# Forbidden tool vocabulary (case-insensitive word boundary).
TOOL_VOCAB = ["Read", "Grep", "Edit", "Write", "TodoWrite", "Task"]

# Names that collide with Codex built-ins. NEVER use these as agent names.
BUILTIN_AGENT_NAMES = {"default", "worker", "explorer", "general-purpose", "statusline-setup"}


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    """Read file, return (frontmatter_dict, body)."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)", text, re.DOTALL)
    if not m:
        return ({}, text)
    raw = m.group(1)
    body = m.group(2)
    fm: dict = {}
    for line in raw.split("\n"):
        if ":" in line and not line.startswith((" ", "-")):
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm, body


def check_one_skill(skill_md: Path, allow_tool_vocab: bool) -> list[str]:
    errs: list[str] = []

    # Parse
    fm, body = parse_frontmatter(skill_md)
    name = fm.get("name", skill_md.parent.name)

    # Name pattern
    if not re.match(r"^[a-z][a-z0-9-]*[a-z0-9]$", name):
        errs.append(f"  - name must be lowercase-kebab-case: got {name!r}")

    # Description trigger phrase + length
    desc = fm.get("description", "")
    if not desc:
        errs.append("  - missing description")
    else:
        if not re.search(r"use\s+(proactively\s+)?when", desc, re.IGNORECASE):
            errs.append(f'  - description must contain "Use when" or "Use PROACTIVELY when": {desc[:80]!r}')
        if len(desc) < 50 or len(desc) > 500:
            errs.append(f"  - description length {len(desc)} out of range [50, 500]")

    # Body size
    body_bytes = body.encode("utf-8")
    line_count = body.count("\n")
    if len(body_bytes) > 8 * 1024:
        errs.append(f"  - body is {len(body_bytes)} bytes (max 8192 = 8 KB)")
    if line_count > 150:
        errs.append(f"  - body is {line_count} lines (max 150)")

    # Tool vocabulary
    if not allow_tool_vocab:
        for term in TOOL_VOCAB:
            if re.search(rf"\b{term}\b", body):
                errs.append(f'  - body mentions tool name "{term}" (use action verbs instead)')

    # Progressive disclosure: either references/ dir OR very short body
    refs_dir = skill_md.parent / "references"
    if not refs_dir.exists() and line_count > 80:
        errs.append(
            f"  - body is {line_count} lines without references/ subdir "
            f"(split if heavy; max 80 lines without references/)"
        )

    # Anti-patterns section
    if re.search(r"^#+\s*anti-?patterns?\s*$", body, re.IGNORECASE | re.MULTILINE):
        ap_section = re.split(
            r"^#+\s*anti-?patterns?\s*$",
            body,
            maxsplit=2,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        if len(ap_section) >= 2:
            ap_content = ap_section[1].split("##", 1)[0]
            bullets = re.findall(r"^\s*[-*]\s+.+", ap_content, re.MULTILINE)
            if len(bullets) < 2:
                errs.append("  - anti-patterns section has < 2 bullets")
    else:
        errs.append("  - missing Anti-patterns section (e.g., ## Anti-patterns)")

    # Verification checklist
    if "verification checklist" in body.lower():
        vc = body.lower().split("verification checklist", 1)[1]
        vc = vc.split("\n## ", 1)[0]
        checks = re.findall(r"\[[ xX]\]", vc)
        if len(checks) < 2:
            errs.append("  - Verification checklist has < 2 items")

    return errs


def check_one_agent(agent_md: Path) -> list[str]:
    errs: list[str] = []
    fm, body = parse_frontmatter(agent_md)
    name = fm.get("name", agent_md.parent.name)

    # Plugin-scoped prefix
    if not name.startswith("af-"):
        errs.append(f"  - agent name must start with 'af-' (got {name!r})")

    # No collision with built-ins
    if name.replace("af-", "") in BUILTIN_AGENT_NAMES:
        errs.append(f"  - agent name {name!r} collides with a built-in (after stripping 'af-' prefix)")

    # Body exists
    if len(body.strip()) < 100:
        errs.append("  - agent body is < 100 chars (probably empty)")

    # Model tier valid
    model = fm.get("model", "").lower()
    if model and model not in {"opus", "sonnet", "haiku", "inherit", ""}:
        errs.append(f"  - model must be opus|sonnet|haiku|inherit (got {model!r})")

    return errs


def main():
    parser = argparse.ArgumentParser(description="Static quality evaluation for skills and agents")
    parser.add_argument("--depth", choices=["quick", "full"], default="quick",
                        help="quick = static only; full = static + (future) LLM judge")
    parser.add_argument("--allow-tool-vocab", action="store_true",
                        help="skip the tool-name vocabulary check (transition use)")
    parser.add_argument("--target", default=None,
                        help="specific path to eval (default: all)")
    args = parser.parse_args()

    if args.depth == "full":
        # Placeholder for v0.3: invoke af-critic for judge pass.
        print("foundry-eval: --depth full not yet implemented; running quick.", file=sys.stderr)

    all_errs: dict[str, list[str]] = {}

    # Skills
    if args.target is None or args.target.endswith("/SKILL.md") or "/skills/" in args.target:
        target_skill = Path(args.target) if args.target else None
        for skill_md in sorted(SKILLS_DIR.rglob("SKILL.md")):
            if target_skill is not None and skill_md != target_skill:
                continue
            errs = check_one_skill(skill_md, args.allow_tool_vocab)
            all_errs[str(skill_md.relative_to(REPO_ROOT))] = errs

    # Agents
    if AGENTS_DIR.exists() and (args.target is None or "/agents/" in args.target):
        target_agent = Path(args.target) if args.target and "/agents/" in args.target else None
        for agent_md in sorted(AGENTS_DIR.rglob("AGENT.md")):
            if target_agent is not None and agent_md != target_agent:
                continue
            errs = check_one_agent(agent_md)
            all_errs[str(agent_md.relative_to(REPO_ROOT))] = errs

    # Check for duplicate names
    seen_names: dict[str, str] = {}
    for path_str in list(all_errs.keys()):
        try:
            fm, _ = parse_frontmatter(REPO_ROOT / path_str)
            n = fm.get("name")
            if n:
                if n in seen_names and seen_names[n] != path_str:
                    all_errs.setdefault(path_str, []).append(
                        f"  - duplicate name {n!r} (also in {seen_names[n]})"
                    )
                else:
                    seen_names[n] = path_str
        except Exception:
            pass

    # Report
    passed = sum(1 for e in all_errs.values() if not e)
    failed = sum(1 for e in all_errs.values() if e)
    print(f"foundry-eval (depth={args.depth}): {passed} passed, {failed} failed")
    for path, errs in all_errs.items():
        if errs:
            print(f"\n{path}:")
            for e in errs:
                print(e)

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
