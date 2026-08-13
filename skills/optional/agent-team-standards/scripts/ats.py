#!/usr/bin/env python3
"""agent-team-standards: lock and apply per-project agent toolchains."""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

SKILLS_ROOT = Path(os.environ.get("HERMES_SKILLS_ROOT", str(Path.home() / "AppData/Local/hermes/skills")))


def list_installed_skills():
    """Walk skills/ dir, return [{name, category, version, path, installed}]."""
    out = []
    if not SKILLS_ROOT.exists():
        return out
    for category_dir in SKILLS_ROOT.iterdir():
        if not category_dir.is_dir() or category_dir.name.startswith("."):
            continue
        for skill_dir in category_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            name = skill_dir.name
            category = category_dir.name
            version = "unknown"
            try:
                with open(skill_md, encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith("version:"):
                            version = line.split(":", 1)[1].strip().strip('"').strip("'")
                            break
            except Exception:
                pass
            out.append({
                "name": name,
                "category": category,
                "version": version,
                "path": str(skill_dir.relative_to(SKILLS_ROOT)),
                "installed": True,
            })
    return sorted(out, key=lambda x: (x["category"], x["name"]))


def cmd_lock(args):
    skills = list_installed_skills()
    manifest = {
        "schema_version": "1.0",
        "project": args.project_dir,
        "generated_at": datetime.now().isoformat() + "Z",
        "skills": skills,
        "config_fragments": {},
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2))
    print("[ats] Locked " + str(len(skills)) + " skills to " + str(out))
    print("[ats] Categories: " + ", ".join(sorted(set(s["category"] for s in skills))))


def cmd_apply(args):
    if not Path(args.manifest).exists():
        print("ERROR: manifest not found: " + args.manifest)
        sys.exit(1)
    with open(args.manifest, encoding="utf-8") as f:
        manifest = json.load(f)
    skills = manifest.get("skills", [])
    installed = list_installed_skills()
    installed_keys = set((s["name"], s["category"]) for s in installed)
    missing = [s for s in skills if (s["name"], s["category"]) not in installed_keys]
    out_of_date = [s for s in skills if (s["name"], s["category"]) in installed_keys and any(
        i["name"] == s["name"] and i["version"] != s["version"] for i in installed
    )]
    print("[ats] Manifest: " + args.manifest)
    print("[ats] Skills:   " + str(len(skills)))
    print("[ats] Installed: " + str(len(installed)))
    if missing:
        print("[ats] MISSING " + str(len(missing)) + ":")
        for s in missing:
            print("  - " + s["category"] + "/" + s["name"] + " v" + s["version"])
    if out_of_date:
        print("[ats] OUT-OF-DATE " + str(len(out_of_date)) + ":")
        for s in out_of_date:
            cur = next((i["version"] for i in installed if i["name"] == s["name"]), "?")
            print("  - " + s["category"] + "/" + s["name"] + " manifest=" + s["version"] + " current=" + cur)
    if not missing and not out_of_date:
        print("[ats] All skills match manifest - apply is a no-op (would install missing ones in real mode)")


def cmd_diff(args):
    if not Path(args.manifest).exists():
        print("ERROR: manifest not found: " + args.manifest)
        sys.exit(1)
    with open(args.manifest, encoding="utf-8") as f:
        manifest = json.load(f)
    installed = list_installed_skills()
    inst_map = {(i["name"], i["category"]): i for i in installed}
    man_set = {(s["name"], s["category"]) for s in manifest.get("skills", [])}
    print("\n## Diff vs manifest\n")
    added = [k for k in inst_map.keys() if k not in man_set]
    removed = [k for k in man_set if k not in inst_map]
    same_version = []
    diff_version = []
    for s in manifest.get("skills", []):
        key = (s["name"], s["category"])
        if key in inst_map:
            if inst_map[key]["version"] == s["version"]:
                same_version.append(key)
            else:
                diff_version.append((key, s["version"], inst_map[key]["version"]))
    print("In manifest + installed (matching): " + str(len(same_version)))
    print("In manifest + installed (mismatched): " + str(len(diff_version)))
    for k, m, c in diff_version:
        print("  " + k[0] + " (manifest=" + m + " current=" + c + ")")
    print("Installed but not in manifest: " + str(len(added)))
    for k in added:
        print("  + " + k[0])
    print("In manifest but not installed: " + str(len(removed)))
    for k in removed:
        print("  - " + k[0])


def cmd_validate(args):
    if not Path(args.manifest).exists():
        print("ERROR: manifest not found: " + args.manifest)
        sys.exit(1)
    with open(args.manifest, encoding="utf-8") as f:
        try:
            m = json.load(f)
        except json.JSONDecodeError as e:
            print("INVALID JSON: " + str(e))
            sys.exit(1)
    if "schema_version" not in m:
        print("ERROR: missing schema_version")
        sys.exit(1)
    if "skills" not in m or not isinstance(m["skills"], list):
        print("ERROR: missing or invalid skills array")
        sys.exit(1)
    seen = set()
    for s in m["skills"]:
        for k in ("name", "category", "version"):
            if k not in s:
                print("ERROR: skill missing field " + k + ": " + str(s))
                sys.exit(1)
        key = (s["name"], s["category"])
        if key in seen:
            print("ERROR: duplicate " + str(key))
            sys.exit(1)
        seen.add(key)
    print("[ats] Manifest valid - " + str(len(m["skills"])) + " skills, schema " + m["schema_version"])


def main():
    p = argparse.ArgumentParser(description="Per-project locked agent toolchain")
    sub = p.add_subparsers(dest="cmd", required=True)
    lock = sub.add_parser("lock")
    lock.add_argument("--project-dir", default=".")
    lock.add_argument("--output", required=True)
    apply = sub.add_parser("apply")
    apply.add_argument("--manifest", required=True)
    diff = sub.add_parser("diff")
    diff.add_argument("--manifest", required=True)
    val = sub.add_parser("validate")
    val.add_argument("--manifest", required=True)
    args = p.parse_args()

    if args.cmd == "lock":
        cmd_lock(args)
    elif args.cmd == "apply":
        cmd_apply(args)
    elif args.cmd == "diff":
        cmd_diff(args)
    elif args.cmd == "validate":
        cmd_validate(args)


if __name__ == "__main__":
    main()
