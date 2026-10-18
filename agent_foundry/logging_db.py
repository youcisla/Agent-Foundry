"""SQLite logging with feedback + instincts schema.

P1: feedback column, instincts table, learn queries.
"""
from __future__ import annotations

import json
import os
import sqlite3
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
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


def engram_lookup(db_path: Path, prompt: str, min_confidence: float = 0.25,
                  project_id: str | None = None) -> dict | None:
    """O(1) Engram-style routing lookup.

    Returns the highest-confidence instinct matching this prompt's
    N-gram fingerprint, or None if no match above min_confidence.

    Default min_confidence=0.25: matches freshly-learned instincts (initial
    confidence 0.3). Bump to 0.5+ for high-stakes routing. When project_id is
    supplied, project-scoped rows outrank global rows for the same fingerprint.

    Caller should fall back to the full plan flow when this returns None.
    """
    init_db(db_path)
    h = _ngram_hash(prompt)
    if not h:
        return None
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        if project_id:
            row = conn.execute(
                """SELECT id, source_skill_id, trigger_pattern, confidence, samples, scope
                   FROM instincts
                   WHERE ngram_hash = ? AND approved = 1 AND confidence >= ?
                     AND (scope = 'global' OR project_id = ?)
                   ORDER BY CASE WHEN scope = 'project' THEN 0 ELSE 1 END,
                            confidence DESC, samples DESC
                   LIMIT 1""",
                (h, min_confidence, project_id),
            ).fetchone()
        else:
            row = conn.execute(
                """SELECT id, source_skill_id, trigger_pattern, confidence, samples, scope
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
        "scope": row[5],
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
    feedback INTEGER,
    cost_usd REAL NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_executions_ts ON executions(timestamp);
CREATE INDEX IF NOT EXISTS idx_executions_skill ON executions(skill_id);

CREATE TABLE IF NOT EXISTS skill_weights (
    skill_id TEXT PRIMARY KEY,
    weight REAL NOT NULL DEFAULT 1.0,
    samples INTEGER NOT NULL DEFAULT 0,
    updated DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS loop_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    turns INTEGER NOT NULL DEFAULT 0,
    output TEXT,
    created DATETIME NOT NULL,
    updated DATETIME NOT NULL
);

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

CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    project_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,
    prompt_excerpt TEXT NOT NULL,
    plan_json TEXT,
    outcome TEXT NOT NULL,
    judge_corr REAL,
    judge_slop REAL,
    judge_scope REAL,
    judge_verdict TEXT,
    cost_usd REAL NOT NULL DEFAULT 0,
    latency_ms INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_observations_project ON observations(project_id);
CREATE INDEX IF NOT EXISTS idx_observations_skill ON observations(skill_id);

CREATE TABLE IF NOT EXISTS policy_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    action_kind TEXT NOT NULL,
    decision TEXT NOT NULL,
    rule_id TEXT,
    detail TEXT,
    receipt_hash TEXT
);
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
    # v5: cost tracking
    "ALTER TABLE executions ADD COLUMN cost_usd REAL NOT NULL DEFAULT 0",
    # v6: scoped instinct ledger
    "ALTER TABLE instincts ADD COLUMN scope TEXT NOT NULL DEFAULT 'global'",
    "ALTER TABLE instincts ADD COLUMN project_id TEXT",
    "ALTER TABLE instincts ADD COLUMN successes INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE instincts ADD COLUMN failures INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE instincts ADD COLUMN evidence_count INTEGER NOT NULL DEFAULT 1",
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
                  judge_verdict: str | None = None,
                  cost_usd: float = 0.0) -> int:
    init_db(db_path)
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        cur = conn.execute(
            """INSERT INTO executions
            (timestamp, skill_id, prompt, output, tokens_used, duration_seconds,
             success, error, planner_score, was_fallback,
             judge_corr, judge_slop, judge_scope, judge_verdict, cost_usd)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                skill_id, prompt, output, int(tokens_used), float(duration_seconds),
                1 if success else 0, error, planner_score,
                1 if was_fallback else 0,
                judge_corr, judge_slop, judge_scope, judge_verdict,
                float(cost_usd),
            ),
        )
        return int(cur.lastrowid)
    finally:
        conn.close()


def list_executions(db_path: Path, skill_id: str | None = None,
                    limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
    """Newest-first execution history without full output bodies."""
    init_db(db_path)
    limit = max(1, min(int(limit), 100))
    offset = max(0, int(offset))
    sql = """SELECT id, timestamp, skill_id, tokens_used, duration_seconds,
                    success, error, was_fallback, cost_usd, feedback,
                    judge_corr, judge_slop, judge_scope, judge_verdict
             FROM executions"""
    params: list[Any] = []
    if skill_id:
        sql += " WHERE skill_id = ?"
        params.append(skill_id)
    sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    keys = ("id", "timestamp", "skill_id", "tokens_used", "duration_seconds",
            "success", "error", "was_fallback", "cost_usd", "feedback",
            "judge_corr", "judge_slop", "judge_scope", "judge_verdict")
    return [dict(zip(keys, row)) for row in rows]


def current_project_id(explicit: str | None = None) -> str:
    """Stable project key: explicit override, env var, or cwd digest."""
    if explicit:
        return explicit
    env = os.environ.get("AGENT_FOUNDRY_PROJECT_ID")
    if env:
        return env
    return hashlib.sha256(str(Path.cwd()).encode("utf-8")).hexdigest()[:12]


def _jsonable(value: Any) -> Any:
    """Convert Pydantic models and containers into JSON-safe values."""
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def log_observation(db_path: Path, *, project_id: str, skill_id: str,
                    prompt: str, outcome: str,
                    judge: dict | None = None,
                    cost_usd: float = 0.0, latency_ms: int = 0,
                    plan: list | None = None) -> int:
    """Record one execution observation without persisting the full prompt."""
    init_db(db_path)
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    judge = judge or {}
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        cur = conn.execute(
            """INSERT INTO observations
            (timestamp, project_id, skill_id, prompt_hash, prompt_excerpt,
             plan_json, outcome, judge_corr, judge_slop, judge_scope,
             judge_verdict, cost_usd, latency_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                project_id, skill_id, prompt_hash, prompt[:160],
                json.dumps(_jsonable(plan), ensure_ascii=False) if plan is not None else None,
                outcome,
                judge.get("correctness"), judge.get("slop"), judge.get("scope"),
                judge.get("verdict"), float(cost_usd), int(latency_ms),
            ),
        )
        return int(cur.lastrowid)
    finally:
        conn.close()


def log_policy_decision(db_path: Path, *, action_kind: str, decision: str,
                        rule_id: str | None = None, detail: str = "",
                        receipt_hash: str = "") -> int:
    """Record one policy decision for later audit."""
    init_db(db_path)
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        cur = conn.execute(
            """INSERT INTO policy_decisions
            (timestamp, action_kind, decision, rule_id, detail, receipt_hash)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (datetime.now(timezone.utc).isoformat(), action_kind, decision,
             rule_id, detail, receipt_hash),
        )
        return int(cur.lastrowid)
    finally:
        conn.close()


def get_skill_weights(db_path: Path) -> dict[str, float]:
    """Learned per-skill multipliers from judge scores and feedback."""
    if not db_path.exists():
        return {}
    init_db(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute("SELECT skill_id, weight FROM skill_weights").fetchall()
    finally:
        conn.close()
    return {r[0]: float(r[1]) for r in rows}


def create_loop_session(db_path: Path, prompt: str, skill_id: str) -> int:
    init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        cur = conn.execute(
            """INSERT INTO loop_sessions (prompt, skill_id, status, turns, created, updated)
               VALUES (?, ?, 'running', 0, ?, ?)""",
            (prompt, skill_id, now, now),
        )
        return int(cur.lastrowid)
    finally:
        conn.close()


def update_loop_session(db_path: Path, session_id: int, *, status: str | None = None,
                        output: str | None = None, increment_turn: bool = False) -> None:
    init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        if status is not None:
            conn.execute("UPDATE loop_sessions SET status = ?, updated = ? WHERE id = ?",
                         (status, now, session_id))
        if output is not None:
            conn.execute("UPDATE loop_sessions SET output = ?, updated = ? WHERE id = ?",
                         (output, now, session_id))
        if increment_turn:
            conn.execute("UPDATE loop_sessions SET turns = turns + 1, updated = ? WHERE id = ?",
                         (now, session_id))
    finally:
        conn.close()


def get_loop_session(db_path: Path, session_id: int) -> dict | None:
    if not db_path.exists():
        return None
    init_db(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            """SELECT id, prompt, skill_id, status, turns, output, created, updated
               FROM loop_sessions WHERE id = ?""",
            (session_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    return {"id": row[0], "prompt": row[1], "skill_id": row[2], "status": row[3],
            "turns": row[4], "output": row[5], "created": row[6], "updated": row[7]}


def update_skill_weights(db_path: Path) -> int:
    """Recompute weights: judge mean plus feedback, clipped to [0.6, 1.4]."""
    init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    updated = 0
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        rows = conn.execute(
            """SELECT skill_id,
                      AVG((judge_corr + judge_slop + judge_scope) / 3.0),
                      SUM(CASE feedback WHEN 1 THEN 1 WHEN -1 THEN -1 ELSE 0 END),
                      COUNT(*)
               FROM executions
               WHERE judge_corr IS NOT NULL OR feedback IS NOT NULL
               GROUP BY skill_id"""
        ).fetchall()
        for skill_id, judge_mean, feedback_sum, samples in rows:
            base = (judge_mean / 10.0) if judge_mean is not None else 0.5
            weight = 0.8 + 0.4 * base + 0.05 * float(feedback_sum or 0) / max(1, samples)
            weight = max(0.6, min(1.4, weight))
            conn.execute(
                """INSERT INTO skill_weights (skill_id, weight, samples, updated)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(skill_id) DO UPDATE SET
                     weight=excluded.weight, samples=excluded.samples, updated=excluded.updated""",
                (skill_id, weight, samples, now),
            )
            updated += 1
    finally:
        conn.close()
    return updated

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
    results = {"new_instincts": 0, "updated_instincts": 0, "patterns_found": [],
               "weights_updated": update_skill_weights(db_path)}

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

    now = datetime.now(timezone.utc).isoformat()
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


def learn_scoped(db_path: Path, *, scope: str = "project",
                 project_id: str | None = None) -> dict:
    """Derive evidence-weighted instincts from the observation ledger.

    Confidence is the Beta(1,1) posterior mean:
    (successes + 1) / (successes + failures + 2).
    """
    if scope not in ("project", "global"):
        raise ValueError("scope must be 'project' or 'global'")
    init_db(db_path)
    pid = current_project_id(project_id) if scope == "project" else None
    results = {"new_instincts": 0, "updated_instincts": 0, "patterns_found": [],
               "scope": scope, "project_id": pid}

    conn = sqlite3.connect(str(db_path))
    try:
        if scope == "project":
            rows = conn.execute(
                """SELECT skill_id, prompt_excerpt, outcome, judge_verdict
                   FROM observations WHERE project_id = ?
                   ORDER BY id DESC LIMIT 500""",
                (pid,),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT skill_id, prompt_excerpt, outcome, judge_verdict
                   FROM observations ORDER BY id DESC LIMIT 500"""
            ).fetchall()
    finally:
        conn.close()

    if not rows:
        return results

    stats: dict[str, dict] = defaultdict(
        lambda: {"successes": 0, "failures": 0, "prompts": [], "verdicts": []}
    )
    for skill_id, excerpt, outcome, verdict in rows:
        bucket = stats[skill_id]
        if outcome == "success":
            bucket["successes"] += 1
        else:
            bucket["failures"] += 1
        bucket["prompts"].append(excerpt or "")
        if verdict:
            bucket["verdicts"].append(verdict)

    now = datetime.now(timezone.utc).isoformat()
    stop = {
        "the", "and", "for", "that", "this", "with", "from", "how",
        "what", "when", "why", "where", "which", "your", "have",
        "will", "can", "are", "not", "but", "all", "was", "out", "use",
    }
    for skill_id, bucket in stats.items():
        counter: Counter = Counter()
        for prompt in bucket["prompts"]:
            counter.update(w for w in re.findall(r"[a-z]{3,}", prompt.lower())
                           if w not in stop)
        tokens = [w for w, _c in counter.most_common(5)]
        pattern = " or ".join(tokens)
        if not pattern:
            continue
        ngram_hash = ""
        for prompt in bucket["prompts"]:
            h = _ngram_hash(prompt)
            if h:
                ngram_hash = h
                break
        successes = bucket["successes"]
        failures = bucket["failures"]
        confidence = (successes + 1.0) / (successes + failures + 2.0)
        evidence = max(1, successes + failures)

        conn = sqlite3.connect(str(db_path), isolation_level=None)
        try:
            if scope == "project":
                existing = conn.execute(
                    """SELECT id FROM instincts
                       WHERE source_skill_id = ? AND trigger_pattern = ?
                         AND scope = 'project' AND project_id = ?""",
                    (skill_id, pattern, pid),
                ).fetchone()
            else:
                existing = conn.execute(
                    """SELECT id FROM instincts
                       WHERE source_skill_id = ? AND trigger_pattern = ?
                         AND scope = 'global' AND project_id IS NULL""",
                    (skill_id, pattern),
                ).fetchone()
            if existing:
                conn.execute(
                    """UPDATE instincts
                       SET confidence = ?, samples = ?, successes = ?, failures = ?,
                           evidence_count = ?, ngram_hash = COALESCE(?, ngram_hash),
                           last_seen = ?
                       WHERE id = ?""",
                    (confidence, evidence, successes, failures, evidence,
                     ngram_hash or None, now, existing[0]),
                )
                results["updated_instincts"] += 1
            else:
                conn.execute(
                    """INSERT INTO instincts
                    (source_skill_id, trigger_pattern, ngram_hash, confidence,
                     samples, created, last_seen, approved, scope, project_id,
                     successes, failures, evidence_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?)""",
                    (skill_id, pattern, ngram_hash or None, confidence, evidence,
                     now, now, scope, pid, successes, failures, evidence),
                )
                results["new_instincts"] += 1
                results["patterns_found"].append({
                    "skill": skill_id, "pattern": pattern, "scope": scope,
                    "confidence": round(confidence, 4),
                    "successes": successes, "failures": failures,
                })
        finally:
            conn.close()

    return results


def explain_instinct(db_path: Path, instinct_id: int) -> dict | None:
    """Return one instinct plus the observations that support it."""
    init_db(db_path)
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        row = conn.execute(
            """SELECT id, source_skill_id, trigger_pattern, confidence, samples,
                      approved, scope, project_id, successes, failures, evidence_count
               FROM instincts WHERE id = ?""",
            (instinct_id,),
        ).fetchone()
        if not row:
            return None
        obs = conn.execute(
            """SELECT id, timestamp, outcome, judge_verdict, cost_usd, prompt_excerpt
               FROM observations WHERE skill_id = ?
               ORDER BY id DESC LIMIT 20""",
            (row[1],),
        ).fetchall()
    finally:
        conn.close()
    return {
        "id": row[0], "skill": row[1], "pattern": row[2], "confidence": row[3],
        "samples": row[4], "approved": bool(row[5]), "scope": row[6],
        "project_id": row[7], "successes": row[8], "failures": row[9],
        "evidence_count": row[10],
        "confidence_formula": "(successes + 1) / (successes + failures + 2)",
        "observations": [
            {"id": o[0], "timestamp": o[1], "outcome": o[2],
             "judge_verdict": o[3], "cost_usd": o[4], "excerpt": o[5]}
            for o in obs
        ],
    }


def _overlap(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def cluster_instincts(db_path: Path, *, min_overlap: float = 0.5,
                      min_shared: int = 2) -> list[dict]:
    """Group instincts whose trigger keywords overlap enough to suggest a skill."""
    init_db(db_path)
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        rows = conn.execute(
            """SELECT id, source_skill_id, trigger_pattern, confidence, samples,
                      scope, successes, failures
               FROM instincts ORDER BY confidence DESC"""
        ).fetchall()
    finally:
        conn.close()

    items = []
    for row in rows:
        words = {w for w in re.split(r"[^a-z0-9]+", row[2].lower()) if len(w) >= 3}
        items.append({"id": row[0], "skill": row[1], "pattern": row[2],
                      "confidence": row[3], "samples": row[4], "scope": row[5],
                      "successes": row[6], "failures": row[7], "words": words})

    parent = list(range(len(items)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri

    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            shared = items[i]["words"] & items[j]["words"]
            if len(shared) >= min_shared and _overlap(items[i]["words"],
                                                      items[j]["words"]) >= min_overlap:
                union(i, j)

    groups: dict[int, list[dict]] = defaultdict(list)
    for i, item in enumerate(items):
        groups[find(i)].append(item)

    out: list[dict] = []
    for members in groups.values():
        if len(members) < 2:
            continue
        shared = set.intersection(*(m["words"] for m in members))
        if not shared:
            shared = set.intersection(*(m["words"] for m in members[:2]))
        keywords = sorted(shared)[:6]
        out.append({
            "suggested_name": "-".join(keywords[:3]) or f"{members[0]['skill']}-cluster",
            "keywords": keywords,
            "members": [{k: v for k, v in m.items() if k != "words"} for m in members],
        })
    return out


def write_proposals(groups: list[dict], out_dir: Path) -> list[str]:
    """Write one reviewable Markdown proposal per cluster. Never writes skills."""
    out_dir = out_dir.expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    for group in groups:
        slug = re.sub(r"[^a-z0-9-]+", "-", group["suggested_name"].lower()).strip("-")
        path = out_dir / f"proposal-{slug or 'cluster'}.md"
        lines = [
            "# Skill Patch Proposal",
            "",
            "Human review required. This file is generated from instincts; it does not modify any skill.",
            "",
            f"- Suggested name: `{group['suggested_name']}`",
            f"- Shared keywords: {', '.join(group['keywords']) or '(none)'}",
            "",
            "| Instinct | Skill | Pattern | Confidence | Evidence |",
            "|---|---|---|---|---|",
        ]
        for m in group["members"]:
            lines.append(
                f"| {m['id']} | {m['skill']} | {m['pattern']} | "
                f"{m['confidence']:.2f} | {m['successes']}+/{m['failures']}- |"
            )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        paths.append(str(path))
    return paths


def list_instincts(db_path: Path, approved_only: bool = False) -> list[dict]:
    """Return instincts as dicts."""
    init_db(db_path)
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        cols = ("id, source_skill_id, trigger_pattern, confidence, samples, "
                "approved, scope, project_id, successes, failures, evidence_count")
        if approved_only:
            rows = conn.execute(f"SELECT {cols} FROM instincts WHERE approved = 1 ORDER BY confidence DESC").fetchall()
        else:
            rows = conn.execute(f"SELECT {cols} FROM instincts ORDER BY confidence DESC").fetchall()
    finally:
        conn.close()
    return [{"id": r[0], "skill": r[1], "pattern": r[2], "confidence": r[3],
             "samples": r[4], "approved": bool(r[5]), "scope": r[6],
             "project_id": r[7], "successes": r[8], "failures": r[9],
             "evidence_count": r[10]} for r in rows]

def approve_instinct(db_path: Path, instinct_id: int) -> bool:
    init_db(db_path)
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        cur = conn.execute("UPDATE instincts SET approved = 1 WHERE id = ?", (instinct_id,))
        return cur.rowcount > 0
    finally:
        conn.close()
