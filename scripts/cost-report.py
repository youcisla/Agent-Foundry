#!/usr/bin/env python3
"""
cost-report.py — Print a cost-per-skill table from skills/index.json

Usage:
  ./scripts/cost-report.py                # all skills, sorted by total cost
  ./scripts/cost-report.py --core         # only core skills
  ./scripts/cost-report.py --optional     # only optional skills
  ./scripts/cost-report.py --id foo       # one skill
  ./scripts/cost-report.py --cheapest N   # top N cheapest
  ./scripts/cost-report.py --sort name    # sort by name (default: total cost)
"""

import sys
import json
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_FILE = REPO_ROOT / "skills" / "index.json"


def load_index() -> dict:
    if not INDEX_FILE.exists():
        print(f"ERROR: {INDEX_FILE} not found. Run ./scripts/indexer.py first.", file=sys.stderr)
        sys.exit(1)
    return json.loads(INDEX_FILE.read_text())


def fmt_row(skill: dict) -> tuple[str, str, str, str]:
    cost = skill["estimated_token_cost"]
    total = cost["input"] + cost["output"]
    return (
        skill["id"][:30],
        f"{cost['input']:>5}",
        f"{cost['output']:>5}",
        f"{total:>6}",
        f"{skill['estimated_time_seconds']:>4}",
    )


def main():
    parser = argparse.ArgumentParser(description="Report skill cost")
    parser.add_argument("--core", action="store_true", help="core skills only")
    parser.add_argument("--optional", action="store_true", help="optional skills only")
    parser.add_argument("--id", help="single skill by id")
    parser.add_argument("--cheapest", type=int, help="top N cheapest by total tokens")
    parser.add_argument("--sort", choices=["total", "input", "output", "time", "name"],
                        default="total", help="sort order (default: total)")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of table")
    args = parser.parse_args()

    idx = load_index()
    skills = idx["skills"]

    # Filter
    if args.core:
        skills = [s for s in skills if s["category"] == "core"]
    if args.optional:
        skills = [s for s in skills if s["category"] == "optional"]
    if args.id:
        matches = [s for s in skills if s["id"] == args.id]
        if not matches:
            print(f"ERROR: no skill with id '{args.id}'", file=sys.stderr)
            sys.exit(1)
        skills = matches

    # Sort
    if args.sort == "total":
        skills = sorted(skills, key=lambda s: s["estimated_token_cost"]["input"] + s["estimated_token_cost"]["output"])
    elif args.sort == "input":
        skills = sorted(skills, key=lambda s: s["estimated_token_cost"]["input"])
    elif args.sort == "output":
        skills = sorted(skills, key=lambda s: s["estimated_token_cost"]["output"])
    elif args.sort == "time":
        skills = sorted(skills, key=lambda s: s["estimated_time_seconds"])
    elif args.sort == "name":
        skills = sorted(skills, key=lambda s: s["name"])

    if args.cheapest:
        skills = skills[:args.cheapest]

    if args.json:
        print(json.dumps(skills, indent=2))
        return

    # Table
    print(f"{'Skill':<32} {'In':>6} {'Out':>6} {'Total':>7} {'Sec':>5}  Cat")
    print(f"{'-'*32} {'-'*6} {'-'*6} {'-'*7} {'-'*5}  {'-'*4}")
    total_in = total_out = total_time = 0
    for s in skills:
        c = s["estimated_token_cost"]
        print(f"{s['id']:<32} {c['input']:>6} {c['output']:>6} "
              f"{c['input']+c['output']:>7} {s['estimated_time_seconds']:>5}  {s['category'][:1]}")
        total_in += c["input"]
        total_out += c["output"]
        total_time += s["estimated_time_seconds"]
    print(f"{'-'*32} {'-'*6} {'-'*6} {'-'*7} {'-'*5}")
    print(f"{'TOTAL (' + str(len(skills)) + ' skills)':<32} {total_in:>6} {total_out:>6} "
          f"{total_in+total_out:>7} {total_time:>5}")


if __name__ == "__main__":
    main()
