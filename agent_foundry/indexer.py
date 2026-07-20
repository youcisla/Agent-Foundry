"""Indexer: scan skills/*/SKILL.md, build SkillIndex."""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import SkillIndex, SkillManifest


FRONTMATTER_RE = re.compile(r"^---[\r\n]+(.*?)[\r\n]+---", re.DOTALL)
ID_RE = re.compile(r"^[a-z0-9-]+$")

# Virtual fallback skill — injected by the indexer, not loaded from disk.
GENERIC_REASONING_ID = "generic-reasoning"
GENERIC_REASONING_SYSTEM_PROMPT = (
    "You are a helpful assistant. The user\'s prompt didn\'t match any specific "
    "skill. Respond thoughtfully and thoroughly."
)
GENERIC_REASONING_MANIFEST: dict[str, Any] = {
    "id": GENERIC_REASONING_ID,
    "name": "Generic Reasoning",
    "description": "Fallback skill for prompts that match no specific skill.",
    "trigger_patterns": [],
    "estimated_token_cost": {"input": 500, "output": 1500},
    "estimated_time_seconds": 5,
    "version": "0.1.0",
    "license": "MIT",
    "category": "core",
    "location": "__virtual__:generic-reasoning",
    "tags": ["fallback", "builtin"],
    "is_fallback": True,
}


def _parse_simple_frontmatter(body: str) -> dict:
    """Parse frontmatter body without depending on PyYAML.

    Handles:
    - 'key: value' lines
    - '  - list item' under the most-recent key
    - Quoted values (single or double quotes)
    - Both \\n and \\r\\n newlines
    - Continuation lines (multi-line values appended with a space)
    """
    result: dict[str, object] = {}
    current_key: str | None = None

    # Normalize to \n so split behaves identically
    body = body.replace("\r\n", "\n").replace("\r", "\n")

    for raw_line in body.split("\n"):
        if not raw_line.strip():
            continue

        # Top-level "key: value"
        if ":" in raw_line and not raw_line.startswith((" ", "\t")) and not raw_line.startswith("-"):
            key, _, value = raw_line.partition(":")
            key = key.strip()
            value = value.strip()
            # Strip matching surrounding quotes
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            result[key] = value
            current_key = key
            continue

        # List item under current key
        stripped = raw_line.lstrip()
        if stripped.startswith("- ") and current_key:
            item = stripped[2:].strip()
            if len(item) >= 2 and item[0] == item[-1] and item[0] in ('"', "'"):
                item = item[1:-1]
            existing = result.get(current_key)
            if not isinstance(existing, list):
                result[current_key] = [existing] if existing is not None else []
            if isinstance(result[current_key], list):
                result[current_key].append(item)
            continue

        # Continuation of current value (best-effort)
        if current_key and isinstance(result.get(current_key), str):
            result[current_key] = str(result[current_key]) + " " + raw_line.strip()

    return result


def parse_frontmatter(text: str) -> dict | None:
    """Extract YAML frontmatter between --- markers.

    Uses a simple line-based parser (no PyYAML needed) so descriptions
    with colons, quoted strings, or list items work reliably.
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    return _parse_simple_frontmatter(m.group(1))


def estimate_cost_from_desc(name: str, description: str) -> dict:
    """Heuristic cost estimate."""
    nl = (name or "").lower()
    if any(w in nl for w in ["check", "audit", "verify", "review"]):
        return {"input": 100, "output": 150}
    if any(w in nl for w in ["design", "strategy", "decompose", "plan"]):
        return {"input": 350, "output": 500}
    desc_len = len(description or "")
    return {
        "input": 200 + min(desc_len * 2, 400),
        "output": 300 + min(desc_len, 600),
    }


def estimate_time_from_name(name: str) -> int:
    nl = (name or "").lower()
    if any(w in nl for w in ["check", "verify", "audit"]):
        return 2
    if any(w in nl for w in ["design", "decompose", "strategy"]):
        return 8
    return 3


def derive_triggers(description: str) -> list:
    """Pull regex triggers from the description."""
    if not description:
        return []
    triggers: list = []
    m = re.search(r"Use when\s+(.+?)(?:\\.|\\?|\\Z)", description, re.IGNORECASE | re.DOTALL)
    if m:
        clause = m.group(1).strip()
        for piece in re.split(r",\\s*|;\\s*|\\bor\\b", clause):
            piece = piece.strip().rstrip(".").strip()
            if 3 < len(piece) < 80:
                triggers.append(r"\b" + re.escape(piece.lower()))
    words = (description or "").lower().split()[:5]
    if words:
        triggers.append(r"\b" + r"\s+".join(re.escape(w) for w in words[:3]))
    seen: set = set()
    out: list = []
    for t in triggers:
        if t not in seen and len(out) < 6:
            out.append(t)
            seen.add(t)
    return out


def build_manifest_from_frontmatter(fm: dict, location: Path) -> dict:
    """Construct a manifest dict from parsed frontmatter + heuristics."""
    name = (fm.get("name") or "").strip() or location.parent.name
    description = (fm.get("description") or "").strip()
    skill_id = location.parent.name
    if not ID_RE.match(skill_id):
        skill_id = re.sub(r"[^a-z0-9-]+", "-", skill_id.lower()).strip("-")

    cost = fm.get("estimated_token_cost") or estimate_cost_from_desc(name, description)
    time_s = fm.get("estimated_time_seconds") or estimate_time_from_name(name)

    location_str = str(location).replace("\\\\", "/")
    category = "core" if "/core/" in location_str else ("optional" if "/optional/" in location_str else "core")

    return {
        "id": skill_id,
        "name": name,
        "description": description,
        "version": str(fm.get("version", "0.1.0")),
        "license": str(fm.get("license", "MIT")),
        "category": category,
        "location": location_str,
        "trigger_patterns": fm.get("trigger_patterns") or derive_triggers(description),
        "estimated_token_cost": {
            "input": int(cost.get("input", 200) if isinstance(cost, dict) else 200),
            "output": int(cost.get("output", 300) if isinstance(cost, dict) else 300),
        },
        "estimated_time_seconds": int(time_s),
        "tags": fm.get("tags", []) or [],
        "is_fallback": False,
    }


def build_index(skills_dir: Path) -> SkillIndex:
    """Walk skills_dir for SKILL.md files, build SkillIndex with the virtual fallback injected."""
    skills: list = []
    skill_paths: dict[str, str] = {}

    if skills_dir.exists():
        for path in sorted(skills_dir.rglob("SKILL.md")):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            fm = parse_frontmatter(text)
            if not fm:
                continue
            try:
                m = build_manifest_from_frontmatter(fm, path)
                manifest = SkillManifest(**m)
            except Exception:
                continue
            skills.append(manifest)
            skill_paths[manifest.id] = str(path)

    fallback = SkillManifest(**GENERIC_REASONING_MANIFEST)
    skill_paths[fallback.id] = "__virtual__:" + GENERIC_REASONING_ID
    skills.append(fallback)

    return SkillIndex(
        version="1",
        generated_at=datetime.now(timezone.utc),
        skills=skills,
        skill_paths=skill_paths,
    )


def write_index(index: SkillIndex, out_path: Path) -> Path:
    """Write the index as JSON."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(index.model_dump(mode="json"), indent=2))
    return out_path


def read_index(path: Path) -> SkillIndex | None:
    """Read the index from JSON. None if missing or invalid."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return SkillIndex(**data)
    except Exception:
        return None


# ----- Module-level cache (TTL) -----

_CACHE: dict[str, tuple] = {}


def get_index_cached(index_path: Path, ttl_seconds: int = 60) -> SkillIndex | None:
    """Return cached index if still fresh; else rebuild from disk if present."""
    key = str(index_path.resolve())
    now = time.time()
    if key in _CACHE:
        ts, idx = _CACHE[key]
        if now - ts < ttl_seconds:
            return idx

    idx = read_index(index_path)
    if idx is not None:
        _CACHE[key] = (now, idx)
    return idx


def invalidate_cache(index_path: Path | None = None) -> None:
    if index_path is None:
        _CACHE.clear()
    else:
        _CACHE.pop(str(index_path.resolve()), None)
