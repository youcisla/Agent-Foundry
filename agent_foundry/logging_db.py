"""SQLite logging."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    skill_id TEXT NOT NULL,
    prompt TEXT NOT NULL,
    output TEXT,
    tokens_used INTEGER NOT NULL DEFAULT 0,
    duration_seconds REAL NOT NULL DEFAULT 0,
    success INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    planner_score REAL,
    was_fallback INTEGER NOT NULL DEFAULT 0,
    judge_corr REAL,
    judge_slop REAL,
    judge_scope REAL,
    judge_verdict TEXT
);
CREATE INDEX IF NOT EXISTS idx_executions_ts ON executions(timestamp);
CREATE INDEX IF NOT EXISTS idx_executions_skill ON executions(skill_id);
"""


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(db_path)) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def log_execution(db_path: Path, *, skill_id: str, prompt: str, output: str,
                  tokens_used: int, duration_seconds: float, success: bool,
                  error: str | None = None, planner_score: float | None = None,
                  was_fallback: bool = False,
                  judge_corr: float | None = None,
                  judge_slop: float | None = None,
                  judge_scope: float | None = None,
                  judge_verdict: str | None = None) -> int:
    init_db(db_path)
    with sqlite3.connect(str(db_path)) as conn:
        cur = conn.execute(
            """INSERT INTO executions
            (timestamp, skill_id, prompt, output, tokens_used, duration_seconds,
             success, error, planner_score, was_fallback)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.utcnow().isoformat(),
                skill_id,
                prompt,
                output,
                int(tokens_used),
                float(duration_seconds),
                1 if success else 0,
                error,
                planner_score,
                1 if was_fallback else 0,
                judge_corr, judge_slop, judge_scope, judge_verdict,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def count_executions(db_path: Path) -> int:
    if not db_path.exists():
        return 0
    with sqlite3.connect(str(db_path)) as conn:
        cur = conn.execute("SELECT COUNT(*) FROM executions")
        return int(cur.fetchone()[0])
