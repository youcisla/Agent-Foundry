#!/usr/bin/env python3
"""
indexer.py — Walk every SKILL.md, extract frontmatter, emit skills/index.json

Output format:
{
  "generated_at": "ISO-8601 timestamp",
  "total_skills": 30,
  "skills": [
    {<manifest object>},
    ...
  ]
}

Usage:
  ./scripts/indexer.py                # build skills/index.json
  ./scripts/indexer.py --validate     # also run JSON Schema validation
  ./scripts/indexer.py --pretty       # pretty-print output
"""

import re
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
SCHEMAS_DIR = REPO_ROOT / "schemas"
OUTPUT_FILE = SKILLS_DIR / "index.json"
SCHEMA_FILE = SCHEMAS_DIR / "skill-manifest.schema.json"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)

DEFAULT_TOKEN_COST = {"input": 200, "output": 300}
DEFAULT_TIME_SECONDS = 3
VALID_CATEGORIES = {"core", "optional"}


def parse_frontmatter(text):
    """Extract YAML frontmatter between --- markers.

    Supports flat key:value, lists via '- item', nested dicts via indentation.
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    raw = m.group(1)

    result = {}
    # Stack tracks (indent_level, parent_dict) so we know where to insert nested items
    stack = [(-1, result)]

    def parent():
        return stack[-1][1]

    lines = raw.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line.strip() or line.strip().startswith("#"):
            continue

        indent = len(line) - len(line.lstrip(" "))
        content = line.strip()

        # Pop stack to current indent level
        while stack and stack[-1][0] >= indent and len(stack) > 1:
            stack.pop()

        # List item
        if content.startswith("- "):
            item_value = content[2:].strip().strip('"').strip("'")
            # Find the most recently added key in parent that is a list (or None)
            p = parent()
            list_key = None
            for k in reversed(list(p.keys())):
                if isinstance(p[k], list):
                    list_key = k
                    break
            if list_key is not None:
                p[list_key].append(item_value)
            continue

        # key: value
        if ":" not in content:
            continue
        key, _, value = content.partition(":")
        key = key.strip()
        value = value.strip()

        # Inline list [a, b, c]
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            parent()[key] = ([s.strip().strip('"').strip("'") for s in inner.split(",")] if inner else [])
            continue

        # Nested block: figure out if next non-empty line is a list or a dict
        if value == "":
            # peek ahead
            nxt = ""
            for j in range(i, len(lines)):
                if lines[j].strip():
                    nxt = lines[j].lstrip(" ")
                    break
            if nxt.startswith("- "):
                parent()[key] = []
            else:
                parent()[key] = {}
                stack.append((indent, parent()[key]))
            continue

        # Scalar
        parent()[key] = value.strip('"').strip("'")

    return result


def derive_triggers(description):
    """Extract trigger patterns from a skill's description."""
    if not description:
        return []
    triggers = []

    # "Use when ... " clauses
    m = re.search(r"Use when\s+(.+?)(?:\.\s*$|[?.])", description, re.IGNORECASE | re.DOTALL)
    if m:
        clause = m.group(1).strip()
        for piece in re.split(r",\s*|;\s*|\bor\b", clause):
            piece = piece.strip().rstrip('.').strip()
            if 3 < len(piece) < 80:
                pat = r"\b" + re.escape(piece.lower())
                triggers.append(pat)

    # First 3 words as a fallback
    words = description.lower().split()[:5]
    if words:
        base = r"\b" + r"\s+".join(re.escape(w) for w in words[:3])
        triggers.append(base)

    # Dedup and limit
    seen = set()
    out = []
    for t in triggers:
        if t not in seen and len(out) < 6:
            out.append(t)
            seen.add(t)
    return out


def derive_id(name, location):
    """Use dir name (e.g. skills/core/anti-slop/SKILL.md -> 'anti-slop')."""
    parts = Path(location).parts
    if len(parts) >= 2:
        return parts[-2]
    return name.lower().replace(" ", "-")


def derive_category(location):
    """core vs optional from path."""
    if "/core/" in location:
        return "core"
    if "/optional/" in location:
        return "optional"
    return "core"


def estimate_cost(name, description):
    """Heuristic cost estimate based on skill name and description length."""
    desc_len = len(description or "")
    name_lower = (name or "").lower()

    # Cheap: quick audits/checks
    if any(w in name_lower for w in ["check", "audit", "verify", "review"]):
        return {"input": 100, "output": 150}

    # Heavy: workflows/designs/strategies
    if any(w in name_lower for w in ["design", "strategy", "decompose", "plan"]):
        return {"input": 350, "output": 500}

    # Default
    return {"input": 200 + min(desc_len * 2, 400),
            "output": 300 + min(desc_len, 600)}


def estimate_time(name):
    name_lower = (name or "").lower()
    if any(w in name_lower for w in ["check", "verify", "audit"]):
        return 2
    if any(w in name_lower for w in ["design", "decompose", "strategy"]):
        return 8
    return 3


def build_manifest(skill_md_path):
    """Build a manifest dict for one skill."""
    try:
        text = skill_md_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  ERROR reading {skill_md_path}: {e}", file=sys.stderr)
        return None

    fm = parse_frontmatter(text)
    if not fm:
        print(f"  SKIP (no frontmatter): {skill_md_path.relative_to(REPO_ROOT)}", file=sys.stderr)
        return None

    name = (fm.get("name") or "").strip()
    description = (fm.get("description") or "").strip()
    if not name or not description:
        print(f"  SKIP (missing name/desc): {skill_md_path.relative_to(REPO_ROOT)}", file=sys.stderr)
        return None

    location = str(skill_md_path.relative_to(REPO_ROOT)).replace("\\", "/")
    skill_id = derive_id(name, location)
    category = derive_category(location)

    manifest = {
        "id": skill_id,
        "name": name,
        "description": description,
        "version": fm.get("version", "0.1.0"),
        "license": fm.get("license", "MIT"),
        "location": location,
        "category": category,
        "execution_type": "prompt",  # v0.1: all skills are prompt-driven
        "trigger_patterns": derive_triggers(description),
        "estimated_token_cost": estimate_cost(name, description),
        "estimated_time_seconds": estimate_time(name),
        "dependencies": [],
        "author": fm.get("author", "Agent Foundry Contributors"),
    }
    return manifest


def validate_manifest(m):
    """Return list of errors (empty = valid)."""
    errs = []
    if not re.match(r"^[a-z0-9-]+$", m.get("id", "")):
        errs.append(f"id '{m.get('id')}' must be lowercase-hyphenated")
    if len(m.get("description", "")) > 500:
        errs.append(f"description too long: {len(m['description'])} chars (max 500)")
    if m.get("category") not in VALID_CATEGORIES:
        errs.append(f"category '{m.get('category')}' not in {VALID_CATEGORIES}")
    cost = m.get("estimated_token_cost", {})
    if not isinstance(cost.get("input"), int) or cost["input"] < 0:
        errs.append("estimated_token_cost.input invalid")
    if not isinstance(cost.get("output"), int) or cost["output"] < 0:
        errs.append("estimated_token_cost.output invalid")
    if not isinstance(m.get("estimated_time_seconds"), int) or m["estimated_time_seconds"] < 0:
        errs.append("estimated_time_seconds invalid")
    return errs


def main():
    parser = argparse.ArgumentParser(description="Build Agent-Foundry skill index")
    parser.add_argument("--validate", action="store_true",
                        help="Run JSON Schema validation against the output")
    parser.add_argument("--pretty", action="store_true",
                        help="Pretty-print the output JSON")
    args = parser.parse_args()

    if not SKILLS_DIR.exists():
        print(f"ERROR: {SKILLS_DIR} not found", file=sys.stderr)
        sys.exit(1)

    manifests = []
    errors = []

    for skill_md in sorted(SKILLS_DIR.rglob("SKILL.md")):
        if "/skills/skills/" in str(skill_md):
            continue
        m = build_manifest(skill_md)
        if m is None:
            continue
        merrs = validate_manifest(m)
        if merrs:
            for e in merrs:
                errors.append(f"{m['id']}: {e}")
        manifests.append(m)

    if errors and not args.validate:
        print(f"\n{len(errors)} validation errors:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)

    if args.validate:
        try:
            import jsonschema
            schema = json.loads(SCHEMA_FILE.read_text())
            for m in manifests:
                try:
                    jsonschema.validate(m, schema)
                except jsonschema.ValidationError as e:
                    errors.append(f"jsonschema: {m['id']}: {e.message}")
        except ImportError:
            print("WARNING: jsonschema not installed, skipping schema validation. "
                  "Install with: pip install jsonschema", file=sys.stderr)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": "1",
        "total_skills": len(manifests),
        "skills": manifests,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    if args.pretty:
        OUTPUT_FILE.write_text(json.dumps(output, indent=2))
    else:
        OUTPUT_FILE.write_text(json.dumps(output, separators=(",", ":")))

    print(f"Indexed {len(manifests)} skills -> {OUTPUT_FILE.relative_to(REPO_ROOT)}")
    if errors and args.validate:
        print(f"  {len(errors)} schema errors (see above)", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
