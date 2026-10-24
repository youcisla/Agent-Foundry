#!/usr/bin/env python3
"""Benchmark gate over measured perf_stats.

Regression requires BOTH a ratio above 1.05 and an absolute delta of at least
0.8 ms, so noise on fast calls cannot fail the gate.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

RATIO_THRESHOLD = 1.05
DELTA_THRESHOLD_MS = 0.8


def load_rows(db: Path) -> dict[str, dict]:
    if not db.exists():
        return {}
    conn = sqlite3.connect(str(db))
    try:
        rows = conn.execute(
            """SELECT model, skill_id, load_bucket, samples_ok, avg_ms_ok,
                      avg_ms_fail, avg_cost_usd, updated
               FROM perf_stats WHERE samples_ok > 0"""
        ).fetchall()
    finally:
        conn.close()
    out = {}
    for model, skill, bucket, n, ms, ms_fail, cost, updated in rows:
        key = f"{model}|{skill}|{bucket}"
        out[key] = {
            "model": model, "skill_id": skill, "load_bucket": bucket,
            "samples_ok": n, "avg_ms_ok": ms, "avg_ms_fail": ms_fail,
            "avg_cost_usd": cost, "updated": updated,
        }
    return out


def compare(current: dict[str, dict], baseline: dict[str, dict]) -> list[dict]:
    regressions = []
    for key, cur in current.items():
        old = baseline.get(key)
        if not old:
            continue
        before = float(old.get("avg_ms_ok") or 0)
        after = float(cur.get("avg_ms_ok") or 0)
        if before <= 0:
            continue
        ratio = after / before
        delta = after - before
        if ratio > RATIO_THRESHOLD and delta >= DELTA_THRESHOLD_MS:
            regressions.append({
                "key": key, "baseline_ms": before, "current_ms": after,
                "ratio": round(ratio, 4), "delta_ms": round(delta, 3),
            })
    return regressions


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent Foundry benchmark gate")
    parser.add_argument("--db", default=str(Path.home() / ".config" / "agent-foundry" / "executions.db"))
    parser.add_argument("--baseline", default="tests/perf_baseline.json")
    parser.add_argument("--jsonl", default=None, help="Write current rows as JSONL")
    parser.add_argument("--refresh-baseline", action="store_true")
    parser.add_argument("--fail-mode", choices=("exit", "warn", "ignore"), default="exit")
    args = parser.parse_args()

    db = Path(args.db).expanduser()
    baseline_path = Path(args.baseline)
    current = load_rows(db)

    if args.jsonl:
        out = Path(args.jsonl)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as handle:
            for row in current.values():
                handle.write(json.dumps(row, sort_keys=True) + "\n")

    if args.refresh_baseline:
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
        print(f"baseline written: {baseline_path} ({len(current)} rows)")
        return 0

    baseline = {}
    if baseline_path.exists():
        try:
            baseline = json.loads(baseline_path.read_text())
        except json.JSONDecodeError:
            baseline = {}

    regressions = compare(current, baseline)
    print(json.dumps({"rows": len(current), "regressions": regressions}, indent=2))
    if not regressions:
        return 0
    if args.fail_mode == "exit":
        return 1
    if args.fail_mode == "warn":
        print("WARN: benchmark regressions detected", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
