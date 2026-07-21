"""SQLite logging with feedback + instincts schema.

P1: feedback column, instincts table, learn queries.
"""
from __future__ import annotations

import sqlite3
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any
import hashlib

# Engram-style N-gram constants
ENGRAM_STOPWORDS = frozenset({
    "the", "and", "for", "that", "this", "with", "from", "how",
    "what", "when", "why", "where", "which", "your", "have",
    "will", "can", "are", "not", "but", "all", "was", "out", "use",
})
ENGRAM_N = 3  # trigrams

def _ngram_hash(prompt: str) -> str:
    """Engram-style N-gram fingerprint (DeepSeek Engram paper).

    Lowercase, strip punctuation, tokenize, generate N-grams, SHA-1 the
    joined canonical form, return the first 16 hex chars.

    Returns "" if no usable tokens after stopword filtering.
    """
    tokens = [t for t in re.findall(r"[a-z]{3,}", prompt.lower())
              if t not in ENGRAM_STOPWORDS]
    if len(tokens) < ENGRAM_N:
        return ""
    ngrams = [" ".join(tokens[i:i + ENGRAM_N]) for i in range(len(tokens) - ENGRAM_N + 1)]
    canonical = "\n".join(sorted(set(ngrams))).encode("utf-8")
    return hashlib.sha1(canonical).hexdigest()[:16]


def engram_lookup(db_path: Path, prompt: str, min_confidence: float = 0.25) -> dict | None:
    """O(1) Engram-style routing lookup.

    Returns the highest-confidence instinct matching this prompt's
    N-gram fingerprint, or None if no match above min_confidence.

    Default min_confidence=0.25: matches freshly-learned instincts (initial
    confidence 0.3). Bump to 0.5+ for high-stakes routing.

    Caller should fall back to the full plan flow when this returns None.
    """
    init_db(db_path)
    h = _ngram_hash(prompt)
    if not h:
        return None
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        row = conn.execute(
            """SELECT id, source_skill_id, trigger_pattern, confidence, samples
               FROM instincts
               WHERE ngram_hash = ? AND approved = 1 AND confidence >= ?
               ORDER BY confidence DESC, samples DESC
               LIMIT 1""",
            (h, min_confidence),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "skill_id": row[1],
        "trigger_pattern": row[2],
        "confidence": row[3],
        "samples": row[4],
        "matched_via": "engram",
    }

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
    judge_verdict TEXT,
    feedback INTEGER
);
CREATE INDEX IF NOT EXISTS idx_executions_ts ON executions(timestamp);
CREATE INDEX IF NOT EXISTS idx_executions_skill ON executions(skill_id);

CREATE TABLE IF NOT EXISTS instincts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_skill_id TEXT NOT NULL,
    trigger_pattern TEXT NOT NULL,
    ngram_hash TEXT,                  -- Engram-style: SHA-1 hex of normalized prompt N-grams
    confidence REAL NOT NULL DEFAULT 0.0,
    samples INTEGER NOT NULL DEFAULT 1,
    created DATETIME NOT NULL,
    last_seen DATETIME NOT NULL,
    approved INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_instincts_skill ON instincts(source_skill_id);
CREATE INDEX IF NOT EXISTS idx_instincts_ngram ON instincts(ngram_hash);
"""

MIGRATIONS = [
    "ALTER TABLE executions ADD COLUMN feedback INTEGER",
    "CREATE TABLE IF NOT EXISTS instincts ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT,"
    "source_skill_id TEXT NOT NULL,"
    "trigger_pattern TEXT NOT NULL,"
    "confidence REAL NOT NULL DEFAULT 0.0,"
    "samples INTEGER NOT NULL DEFAULT 1,"
    "created DATETIME NOT NULL,"
    "last_seen DATETIME NOT NULL,"
    "approved INTEGER NOT NULL DEFAULT 0"
    ")",
    "CREATE INDEX IF NOT EXISTS idx_instincts_skill ON instincts(source_skill_id)",
    # v3 -> v4: Engram-style N-gram hash column on instincts
    "ALTER TABLE instincts ADD COLUMN ngram_hash TEXT",
    "CREATE INDEX IF NOT EXISTS idx_instincts_ngram ON instincts(ngram_hash)",
]

def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), isolation_level=None)  # autocommit
    try:
        conn.executescript(SCHEMA)
        # Apply migrations (safe to re-run)
        for mig in MIGRATIONS:
            try:
                conn.execute(mig)
            except sqlite3.OperationalError:
                pass  # column already exists / table already exists
    finally:
        conn.close()

def log_execution(db_path: Path, *, skill_id: str, prompt: str, output: str,
                  tokens_used: int, duration_seconds: float, success: bool,
                  error: str | None = None, planner_score: float | None = None,
                  was_fallback: bool = False,
                  judge_corr: float | None = None,
                  judge_slop: float | None = None,
                  judge_scope: float | None = None,
                  judge_verdict: str | None = None) -> int:
    init_db(db_path)
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        cur = conn.execute(
            """INSERT INTO executions
            (timestamp, skill_id, prompt, output, tokens_used, duration_seconds,
             success, error, planner_score, was_fallback,
             judge_corr, judge_slop, judge_scope, judge_verdict)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.utcnow().isoformat(),
                skill_id, prompt, output, int(tokens_used), float(duration_seconds),
                1 if success else 0, error, planner_score,
                1 if was_fallback else 0,
                judge_corr, judge_slop, judge_scope, judge_verdict,
            ),
        )
        return int(cur.lastrowid)
    finally:
        conn.close()

def set_feedback(db_path: Path, execution_id: int, feedback: int) -> bool:
    """feedback: 1 = thumbs_up, -1 = thumbs_down."""
    if feedback not in (1, -1):
        return False
    init_db(db_path)
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        cur = conn.execute("UPDATE executions SET feedback = ? WHERE id = ?", (feedback, execution_id))
        return cur.rowcount > 0
    finally:
        conn.close()

def count_executions(db_path: Path) -> int:
    if not db_path.exists():
        return 0
    with sqlite3.connect(str(db_path)) as conn:
        cur = conn.execute("SELECT COUNT(*) FROM executions")
        return int(cur.fetchone()[0])

def get_stats(db_path: Path) -> dict:
    init_db(db_path)
    stats = {"total_executions": 0, "successful": 0, "failed": 0,
             "fallback_count": 0, "avg_tokens": 0, "avg_duration": 0,
             "thumbs_up": 0, "thumbs_down": 0, "instincts_count": 0}
    try:
        with sqlite3.connect(str(db_path)) as conn:
            row = conn.execute("SELECT COUNT(*) FROM executions").fetchone()
            stats["total_executions"] = row[0] if row else 0
            row = conn.execute("SELECT COUNT(*) FROM executions WHERE success = 1").fetchone()
            stats["successful"] = row[0] if row else 0
            stats["failed"] = stats["total_executions"] - stats["successful"]
            row = conn.execute("SELECT COUNT(*) FROM executions WHERE was_fallback = 1").fetchone()
            stats["fallback_count"] = row[0] if row else 0
            row = conn.execute("SELECT AVG(tokens_used) FROM executions WHERE success = 1").fetchone()
            stats["avg_tokens"] = round(row[0]) if row and row[0] else 0
            row = conn.execute("SELECT AVG(duration_seconds) FROM executions WHERE success = 1").fetchone()
            stats["avg_duration"] = round(row[0], 2) if row and row[0] else 0
            row = conn.execute("SELECT COUNT(*) FROM executions WHERE feedback = 1").fetchone()
            stats["thumbs_up"] = row[0] if row else 0
            row = conn.execute("SELECT COUNT(*) FROM executions WHERE feedback = -1").fetchone()
            stats["thumbs_down"] = row[0] if row else 0
            row = conn.execute("SELECT COUNT(*) FROM instincts").fetchone()
            stats["instincts_count"] = row[0] if row else 0
    except Exception:
        pass
    return stats

def learn(db_path: Path) -> dict:
    """Analyze execution log, extract trigger word patterns, write instincts.

    Each instinct also gets an Engram-style N-gram hash so future lookups can
    be O(1) via `engram_lookup()`.

    Returns summary of what was learned.
    """
    init_db(db_path)
    results = {"new_instincts": 0, "updated_instincts": 0, "patterns_found": []}

    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute(
            """SELECT skill_id, prompt, feedback, id FROM executions
               WHERE feedback IS NOT NULL AND success = 1
               ORDER BY id DESC LIMIT 200"""
        ).fetchall()

    if not rows:
        return results

    # Group by skill: collect keywords from successful + positive-feedback prompts
    skill_keywords: dict[str, Counter] = defaultdict(Counter)
    skill_prompts: dict[str, list[str]] = defaultdict(list)
    for skill_id, prompt, feedback, _eid in rows:
        if feedback != 1:
            continue
        words = re.findall(r'[a-z]{3,}', prompt.lower())
        skill_keywords[skill_id].update(w for w in words if w not in
            {'the', 'and', 'for', 'that', 'this', 'with', 'from', 'how',
             'what', 'when', 'why', 'where', 'which', 'your', 'have',
             'will', 'can', 'are', 'not', 'but', 'all', 'was', 'out', 'use'})
        skill_prompts[skill_id].append(prompt)

    now = datetime.utcnow().isoformat()
    for skill_id, counter in skill_keywords.items():
        top = counter.most_common(5)
        tokens = [w for w, _c in top]
        pattern = " or ".join(tokens) if tokens else ""
        if not pattern:
            continue
        # Engram hash from the union of positive prompts for this skill
        ngram_hash = ""
        for prompt in skill_prompts[skill_id]:
            h = _ngram_hash(prompt)
            if h:
                ngram_hash = h
                break

        with sqlite3.connect(str(db_path)) as conn:
            existing = conn.execute(
                "SELECT id, confidence, samples FROM instincts WHERE source_skill_id = ? AND trigger_pattern = ?",
                (skill_id, pattern)
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE instincts SET confidence = ?, samples = samples + 1, last_seen = ? WHERE id = ?",
                    (min(1.0, existing[1] + 0.1), now, existing[0])
                )
                results["updated_instincts"] += 1
            else:
                conn.execute(
                    "INSERT INTO instincts (source_skill_id, trigger_pattern, ngram_hash, confidence, samples, created, last_seen, approved) VALUES (?, ?, ?, ?, ?, ?, ?, 0)",
                    (skill_id, pattern, ngram_hash, 0.3, 1, now, now)
                )
                results["new_instincts"] += 1
                results["patterns_found"].append({"skill": skill_id, "pattern": pattern, "ngram_hash": ngram_hash})
        conn.commit()

    return results

def list_instincts(db_path: Path, approved_only: bool = False) -> list[dict]:
    """Return instincts as dicts."""
    init_db(db_path)
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        if approved_only:
            rows = conn.execute("SELECT id, source_skill_id, trigger_pattern, confidence, samples, approved FROM instincts WHERE approved = 1 ORDER BY confidence DESC").fetchall()
        else:
            rows = conn.execute("SELECT id, source_skill_id, trigger_pattern, confidence, samples, approved FROM instincts ORDER BY confidence DESC").fetchall()
    finally:
        conn.close()
    return [{"id": r[0], "skill": r[1], "pattern": r[2], "confidence": r[3], "samples": r[4], "approved": bool(r[5])} for r in rows]

def approve_instinct(db_path: Path, instinct_id: int) -> bool:
    init_db(db_path)
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        cur = conn.execute("UPDATE instincts SET approved = 1 WHERE id = ?", (instinct_id,))
        return cur.rowcount > 0
    finally:
        conn.close()
