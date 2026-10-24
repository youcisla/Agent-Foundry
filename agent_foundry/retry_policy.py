"""Attempt allocation from observed success rates.

Attempt k is worth its expected marginal success probability. No dollar value
is invented; the threshold is explicit and configurable.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from .logging_db import init_db


def success_rate(
    db_path: Path,
    *,
    skill_id: str,
    model: str | None = None,
    min_samples: int = 10,
) -> float | None:
    """Laplace-smoothed success rate; None below the sample floor."""
    if not db_path.exists():
        return None
    init_db(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        if model:
            row = conn.execute(
                "SELECT SUM(success), COUNT(*) FROM executions WHERE skill_id = ? AND model = ?",
                (skill_id, model),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT SUM(success), COUNT(*) FROM executions WHERE skill_id = ?",
                (skill_id,),
            ).fetchone()
    finally:
        conn.close()
    successes, total = (row or (0, 0))
    total = int(total or 0)
    if total < min_samples:
        return None
    return (float(successes or 0) + 1.0) / (total + 2.0)


def allocate_attempts(
    p: float | None,
    *,
    max_attempts: int = 3,
    marginal_threshold: float = 0.15,
) -> int:
    """1 when unknown. Otherwise add attempts while marginal gain clears the bar."""
    if p is None:
        return 1
    p = max(0.0, min(1.0, float(p)))
    attempts = 1
    while attempts < max(1, max_attempts):
        marginal = p * ((1.0 - p) ** attempts)
        if marginal < marginal_threshold:
            break
        attempts += 1
    return attempts
