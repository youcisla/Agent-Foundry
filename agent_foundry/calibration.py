"""Judge calibration: compare stored judge scores with human feedback."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from .logging_db import init_db


def calibration_report(db_path: Path, *, bins: int = 5) -> dict:
    """Bin judge correctness against thumbs up/down.

    Returns counts and mean feedback per score bin. Rows without both a judge
    score and feedback are excluded; they cannot calibrate anything.
    """
    if not db_path.exists():
        return {"bins": [], "samples": 0}
    init_db(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            """SELECT judge_corr, feedback FROM executions
               WHERE judge_corr IS NOT NULL AND feedback IS NOT NULL"""
        ).fetchall()
    finally:
        conn.close()
    if not rows:
        return {"bins": [], "samples": 0}
    width = 10.0 / max(1, bins)
    buckets: list[dict] = []
    for index in range(max(1, bins)):
        low = index * width
        high = low + width
        values = [
            float(feedback) for score, feedback in rows
            if low <= float(score) < high or (index == bins - 1 and float(score) == 10.0)
        ]
        buckets.append({
            "low": round(low, 2),
            "high": round(high, 2),
            "samples": len(values),
            "mean_feedback": round(sum(values) / len(values), 4) if values else None,
        })
    return {"bins": buckets, "samples": len(rows)}
