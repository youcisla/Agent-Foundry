"""Per-model measured latency/token cache in SQLite.

One writer (SQLite) avoids the cross-process file-cache race. Keys carry a
load bucket and a format version, so a changed schema or concurrency regime
never mixes with old rows.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .logging_db import init_db

FORMAT_VERSION = 1


def load_bucket(queue_depth: int | None) -> str:
    depth = max(0, int(queue_depth or 0))
    if depth <= 1:
        return "1"
    if depth <= 4:
        return "2-4"
    if depth <= 8:
        return "5-8"
    return "9+"


def record_sample(
    db_path: Path,
    *,
    model: str,
    skill_id: str,
    queue_depth: int | None,
    duration_ms: int,
    success: bool,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    cached_tokens: int = 0,
    cost_usd: float = 0.0,
    enabled: bool = True,
) -> None:
    if not enabled or not model:
        return
    init_db(db_path)
    bucket = load_bucket(queue_depth)
    now = datetime.now(timezone.utc).isoformat()
    ok = 1 if success else 0
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        conn.execute(
            """INSERT INTO perf_stats
            (model, skill_id, load_bucket, format_version, samples, samples_ok,
             samples_fail, avg_ms_ok, avg_ms_fail, avg_prompt_tokens,
             avg_completion_tokens, avg_cached_tokens, avg_cost_usd, updated)
            VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(model, skill_id, load_bucket, format_version) DO UPDATE SET
              samples = samples + 1,
              samples_ok = samples_ok + excluded.samples_ok,
              samples_fail = samples_fail + excluded.samples_fail,
              avg_ms_ok = CASE WHEN excluded.samples_ok = 1
                THEN (avg_ms_ok * samples_ok + excluded.avg_ms_ok) / (samples_ok + 1)
                ELSE avg_ms_ok END,
              avg_ms_fail = CASE WHEN excluded.samples_fail = 1
                THEN (avg_ms_fail * samples_fail + excluded.avg_ms_fail) / (samples_fail + 1)
                ELSE avg_ms_fail END,
              avg_prompt_tokens = (avg_prompt_tokens * samples + excluded.avg_prompt_tokens) / (samples + 1),
              avg_completion_tokens = (avg_completion_tokens * samples + excluded.avg_completion_tokens) / (samples + 1),
              avg_cached_tokens = (avg_cached_tokens * samples + excluded.avg_cached_tokens) / (samples + 1),
              avg_cost_usd = (avg_cost_usd * samples + excluded.avg_cost_usd) / (samples + 1),
              updated = excluded.updated""",
            (
                model, skill_id, bucket, FORMAT_VERSION,
                ok, 1 - ok,
                float(duration_ms) if ok else 0.0,
                float(duration_ms) if not ok else 0.0,
                float(prompt_tokens), float(completion_tokens),
                float(cached_tokens), float(cost_usd), now,
            ),
        )
    finally:
        conn.close()


def estimate(
    db_path: Path,
    *,
    model: str,
    skill_id: str,
    queue_depth: int | None = None,
    ttl_seconds: int = 3600,
    enabled: bool = True,
) -> dict[str, Any] | None:
    if not enabled or not model or not db_path.exists():
        return None
    init_db(db_path)
    bucket = load_bucket(queue_depth)
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            """SELECT samples, samples_ok, samples_fail, avg_ms_ok, avg_ms_fail,
                      avg_prompt_tokens, avg_completion_tokens, avg_cached_tokens,
                      avg_cost_usd, updated
               FROM perf_stats
               WHERE model = ? AND skill_id = ? AND load_bucket = ?
                 AND format_version = ?""",
            (model, skill_id, bucket, FORMAT_VERSION),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    try:
        updated = datetime.fromisoformat(row[9])
    except (TypeError, ValueError):
        return None
    age = (datetime.now(timezone.utc) - updated).total_seconds()
    if age > ttl_seconds:
        return None
    return {
        "samples": row[0], "samples_ok": row[1], "samples_fail": row[2],
        "avg_ms_ok": round(row[3], 3), "avg_ms_fail": round(row[4], 3),
        "avg_prompt_tokens": round(row[5], 1),
        "avg_completion_tokens": round(row[6], 1),
        "avg_cached_tokens": round(row[7], 1),
        "avg_cost_usd": round(row[8], 6),
        "load_bucket": bucket, "age_seconds": round(age, 1),
    }
