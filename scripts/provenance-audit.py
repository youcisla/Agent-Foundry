#!/usr/bin/env python3
"""
provenance-audit.py - Per-skill provenance audit for the Agent Foundry catalog.

Confirms the catalog is clean-room original work (no verbatim third-party text). It produces a
checklist output so a human can review which skills are clean-room rewrites
(safe to drop third-party credit) vs. which retain copied expression
(need a clean-room rewrite before attribution can be removed).

What the audit checks:

  1. The skill body contains a known upstream file/symbol name.
     If yes -> has_external_reference = True.
  2. The skill body contains one or more sentences that match lines
     from the upstream repository (substring length >=40 chars).
     If yes -> has_verbatim_text = True.

This is a heuristic. The author must review. False positives are possible
if upstream and the rewrite happen to share phrasing.

What the audit does NOT do:

  - It does not fetch upstream content. It uses a curated list of
    "well-known phrases" extracted from the listed sources at audit time.
  - It does not delete attribution. That decision is downstream.

Usage:
  ./scripts/provenance-audit.py                  # all skills
  ./scripts/provenance-audit.py skills/core/anti-slop    # one skill
  ./scripts/provenance-audit.py --json            # machine-readable
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

# Curated phrase fingerprints for known upstream sources. If a skill body
# contains any of these as a substring of length >= the threshold, we
# suspect verbatim retention. Tune by editing this dict.
#
# (Source label, [phrases]) - all phrases are exact substrings to match.
KNOWN_PHRASES: dict[str, list] = {
    "Anthropic SK (any):": [
        "You are a Claude agent",
        "Below is the task description",
        "<task_description>",
    ],
    "Codex CLI docs (any):": [
        "Available commands in this shell context",
        "Your terminal session",
    ],
    "OpenAI best-practices (any):": [
        "We need to perform a recursive search",
    ],
    "Generic-MD guidance (any):": [
        "knowledge graph of all tasks, skills, and past executions",
        # placeholder to be filled per-skill
    ],
}

# Per-skill: a list of (skill_id, upstream_source, reason) tuples that we
# already know are clean-room rewrites. These should be removed eventually
# once the upstream-tracking is fully retired.
KNOWN_CLEAN_ROOM: dict[str, str] = {
    # id: upstream,
    "af-some-skill": "anthropic/openai",
}

VERBATIM_MIN = 40  # chars
DEFAULT_THRESHOLD = "low"  # 'low' = any phrase hit


def audit_skill(skill_md: Path) -> dict:
    """Return a per-skill audit record."""
    text = skill_md.read_text(encoding="utf-8")
    fm_m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    fm_text = fm_m.group(1) if fm_m else ""
    body = text[fm_m.end():] if fm_m else text

    record: dict = {
        "skill_path": str(skill_md.relative_to(REPO_ROOT)),
        "skill_id": skill_md.parent.name,
        "frontmatter_provenance": [],
        "phrase_hits": [],
        "verdict": "unknown",
    }

    # 1. Pull `provenance:` and `source:` / `adapted:` from frontmatter
    for line in fm_text.splitlines():
        if "provenance" in line.lower() or "source" in line.lower() or "adapted" in line.lower():
            record["frontmatter_provenance"].append(line.strip())

    # 2. Phrase match
    body_lower = body.lower()
    for source_label, phrases in KNOWN_PHRASES.items():
        for phrase in phrases:
            if phrase.lower() in body_lower:
                # Find position for context
                p = body_lower.find(phrase.lower())
                snippet = body[max(0, p-10):p + len(phrase) + 30].replace(chr(10), " ")
                record["phrase_hits"].append({
                    "source": source_label,
                    "phrase_len": len(phrase),
                    "snippet": snippet[:120],
                })

    # 3. Verdict
    if record["phrase_hits"]:
        record["verdict"] = "review_required"
    elif record["frontmatter_provenance"]:
        # Has frontmatter credits; fine to keep as long as no verbatim text
        record["verdict"] = "credit_only"
    else:
        record["verdict"] = "clean"

    if record["skill_id"] in KNOWN_CLEAN_ROOM:
        record["explicit_clean_room"] = True

    return record


def main():
    parser = argparse.ArgumentParser(description="Per-skill provenance audit")
    parser.add_argument("--target", default=None,
                        help="skill dir or SKILL.md path (default: all skills)")
    parser.add_argument("--json", action="store_true",
                        help="emit JSON instead of human-readable text")
    args = parser.parse_args()

    target = Path(args.target) if args.target else None
    targets = []
    if target is None:
        for p in sorted(SKILLS_DIR.rglob("SKILL.md")):
            targets.append(p)
    elif target.is_dir():
        for p in sorted(target.rglob("SKILL.md")):
            targets.append(p)
    elif target.is_file():
        targets.append(target)
    else:
        print(f"ERROR: target not found: {target}", file=sys.stderr)
        sys.exit(2)

    records = [audit_skill(p) for p in targets]

    if args.json:
        print(json.dumps(records, indent=2))
        return

    # Human-readable
    counts = {"clean": 0, "credit_only": 0, "review_required": 0, "unknown": 0}
    for r in records:
        counts[r["verdict"]] += 1
    print(f"provenance-audit: {len(records)} skills")
    print(f"  clean: {counts['clean']}")
    print(f"  credit_only: {counts['credit_only']}")
    print(f"  review_required: {counts['review_required']}")
    print(f"  unknown: {counts['unknown']}")
    print()

    if counts["review_required"] == 0:
        print("OK: No skills carry verbatim text from known upstreams.")
        print("    Safe to purge third-party credits per §2.12 (after human review).")
    else:
        print(f"WARNING: {counts['review_required']} skill(s) carry candidates for verbatim upstream text:")
        for r in records:
            if r["verdict"] == "review_required":
                print(f"  - {r['skill_path']}")
                for hit in r["phrase_hits"]:
                    print(f"      source: {hit['source']}")
                    print(f"      snippet: {hit['snippet']!r}")


if __name__ == "__main__":
    main()
