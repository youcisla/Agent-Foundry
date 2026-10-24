"""SQLite logging with feedback + instincts schema.

P1: feedback column, instincts table, learn queries.
"""
from __future__ import annotations

import json
import os
import sqlite3
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import hashlib
import math
import unicodedata

# Engram-style N-gram constants
ENGRAM_STOPWORDS = frozenset({
    "the", "and", "for", "that", "this", "with", "from", "how",
    "what", "when", "why", "where", "which", "your", "have",
    "will", "can", "are", "not", "but", "all", "was", "out", "use",
})
ENGRAM_N = 3  # trigrams
ENGRAM_HEADS = 3


def _normalize_text(prompt: str) -> str:
    """Canonicalize before hashing: NFKC, casefold, strip accents, collapse space."""
    text = unicodedata.normalize("NFKC", prompt or "").casefold()
    text = "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if not unicodedata.combining(ch)
    )
    return " ".join(text.split())


def _ngram_tokens(prompt: str) -> list[str]:
    """Unicode-aware tokens. Non-Latin prompts must not hash to an empty string."""
    tokens = re.findall(r"[^\W_]+", _normalize_text(prompt), flags=re.UNICODE)
    return [t for t in tokens if len(t) >= 3 and t not in ENGRAM_STOPWORDS]


def _ngram_hashes(prompt: str) -> tuple[str, str, str]:
    """Ordered trigram fingerprints under three independent salts.

    Ordered: repetition and sequence matter. Empty tuple when the prompt has
    fewer than N usable tokens.
    """
    tokens = _ngram_tokens(prompt)
    if len(tokens) < ENGRAM_N:
        return ("", "", "")
    ngrams = [
        " ".join(tokens[i:i + ENGRAM_N])
        for i in range(len(tokens) - ENGRAM_N + 1)
    ]
    canonical = "\n".join(ngrams).encode("utf-8")
    return tuple(
        hashlib.sha1(str(head).encode("ascii") + b"|" + canonical).hexdigest()[:16]
        for head in range(ENGRAM_HEADS)
    )


def _ngram_hash(prompt: str) -> str:
    """Legacy head-0 fingerprint. Prefer `_ngram_hashes`."""
    return _ngram_hashes(prompt)[0]


def _legacy_hash(prompt: str) -> str:
    """Pre-v7 fingerprint: ASCII tokens, sorted set of trigrams."""
    tokens = [
        t for t in re.findall(r"[a-z]{3,}", (prompt or "").lower())
        if t not in ENGRAM_STOPWORDS
    ]
    if len(tokens) < ENGRAM_N:
        return ""
    ngrams = [
        " ".join(tokens[i:i + ENGRAM_N])
        for i in range(len(tokens) - ENGRAM_N + 1)
    ]
    canonical = "\n".join(sorted(set(ngrams))).encode("utf-8")
    return hashlib.sha1(canonical).hexdigest()[:16]


def _match_count(stored: tuple[str | None, ...], heads: tuple[str, str, str]) -> int:
    return sum(1 for a, b in zip(stored, heads) if a and b and a == b)


def _is_legacy_single_head(stored: tuple[str | None, ...]) -> bool:
    return bool(stored[0]) and not stored[1] and not stored[2]


def _gate_score(prompt: str, pattern: str) -> float:
    """Keyword overlap gate in [0,1]; a hash hit alone is not a routing decision."""
    prompt_tokens = set(_ngram_tokens(prompt))
    pattern_tokens = {
        t for t in re.findall(r"[^\W_]+", _normalize_text(pattern), flags=re.UNICODE)
        if len(t) >= 3
    }
    if not pattern_tokens:
        return 0.0
    overlap = len(prompt_tokens & pattern_tokens) / len(pattern_tokens)
    return round(1.0 / (1.0 + math.exp(-6.0 * (overlap - 0.3))), 4)


def engram_lookup(db_path: Path, prompt: str, min_confidence: float = 0.25,
                  project_id: str | None = None,
                  min_project_samples: int = 3) -> dict | None:
    """Multi-head Engram lookup. Returns the best approved instinct or None.

    A row matches when at least two heads agree. Legacy rows with only head 0
    match on head 0 alone until they are relearned. Project rows outrank global
    rows only once they have `min_project_samples` evidence.
    """
    init_db(db_path)
    heads = _ngram_hashes(prompt)
    legacy = _legacy_hash(prompt)
    if not heads[0]:
        return None
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        rows = conn.execute(
            """SELECT id, source_skill_id, trigger_pattern, confidence, samples,
                      scope, project_id, ngram_hash, ngram_hash2, ngram_hash3
               FROM instincts
               WHERE approved = 1 AND confidence >= ?
                 AND (ngram_hash = ? OR ngram_hash2 = ? OR ngram_hash3 = ?)""",
            (min_confidence, heads[0], heads[1], heads[2]),
        ).fetchall()
        if legacy and legacy not in heads:
            rows += conn.execute(
                """SELECT id, source_skill_id, trigger_pattern, confidence, samples,
                          scope, project_id, ngram_hash, ngram_hash2, ngram_hash3
                   FROM instincts
                   WHERE approved = 1 AND confidence >= ?
                     AND ngram_hash = ? AND ngram_hash2 IS NULL""",
                (min_confidence, legacy),
            ).fetchall()
    finally:
        conn.close()

    candidates = []
    for row in rows:
        stored = (row[7], row[8], row[9])
        matched = _match_count(stored, heads)
        legacy_match = bool(legacy and stored[0] == legacy and _is_legacy_single_head(stored))
        if matched < 2 and not (matched == 1 and _is_legacy_single_head(stored)) \
                and not legacy_match:
            continue
        project_ok = bool(
            project_id and row[5] == "project" and row[6] == project_id
            and (row[4] or 0) >= min_project_samples
        )
        candidates.append((project_ok, row[3], row[4], row))

    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    row = candidates[0][3]
    return {
        "id": row[0],
        "skill_id": row[1],
        "trigger_pattern": row[2],
        "confidence": row[3],
        "samples": row[4],
        "scope": row[5],
        "gate_score": _gate_score(prompt, row[2]),
        "matched_via": "engram",
    }

SCHEMA_VERSION = 7

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

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
    cost_usd REAL NOT NULL DEFAULT 0,
    model TEXT,
    trace_digest TEXT,
    phases_json TEXT,
    repairs INTEGER NOT NULL DEFAULT 0,
    output_ref TEXT,
    judge_status TEXT,
    failure_kind TEXT,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    cached_tokens INTEGER NOT NULL DEFAULT 0,
    request_meta_json TEXT,
    run_config_json TEXT
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
    history_json TEXT,
    created DATETIME NOT NULL,
    updated DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS instincts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_skill_id TEXT NOT NULL,
    trigger_pattern TEXT NOT NULL,
    ngram_hash TEXT,                  -- head 0; kept for legacy matches
    ngram_hash2 TEXT,
    ngram_hash3 TEXT,
    confidence REAL NOT NULL DEFAULT 0.0,
    samples INTEGER NOT NULL DEFAULT 1,
    created DATETIME NOT NULL,
    last_seen DATETIME NOT NULL,
    approved INTEGER NOT NULL DEFAULT 0,
    scope TEXT NOT NULL DEFAULT 'global',
    project_id TEXT,
    successes INTEGER NOT NULL DEFAULT 0,
    failures INTEGER NOT NULL DEFAULT 0,
    evidence_count INTEGER NOT NULL DEFAULT 1
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
    receipt_hash TEXT,
    binding_info TEXT
);

CREATE TABLE IF NOT EXISTS perf_stats (
    model TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    load_bucket TEXT NOT NULL,
    format_version INTEGER NOT NULL,
    samples INTEGER NOT NULL DEFAULT 0,
    samples_ok INTEGER NOT NULL DEFAULT 0,
    samples_fail INTEGER NOT NULL DEFAULT 0,
    avg_ms_ok REAL NOT NULL DEFAULT 0,
    avg_ms_fail REAL NOT NULL DEFAULT 0,
    avg_prompt_tokens REAL NOT NULL DEFAULT 0,
    avg_completion_tokens REAL NOT NULL DEFAULT 0,
    avg_cached_tokens REAL NOT NULL DEFAULT 0,
    avg_cost_usd REAL NOT NULL DEFAULT 0,
    updated DATETIME NOT NULL,
    PRIMARY KEY (model, skill_id, load_bucket, format_version)
);

CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    skill_id TEXT NOT NULL,
    model TEXT,
    dedupe_hash TEXT NOT NULL,
    parent_id INTEGER,
    round_idx INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    created DATETIME NOT NULL,
    updated DATETIME NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_attempts_dedupe ON attempts(dedupe_hash);
"""

# Numbered, append-only. Never edit or reorder an applied entry.
MIGRATIONS: list[tuple[int, str]] = [
    (1, "ALTER TABLE executions ADD COLUMN feedback INTEGER"),
    (2, "CREATE TABLE IF NOT EXISTS instincts ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "source_skill_id TEXT NOT NULL,"
        "trigger_pattern TEXT NOT NULL,"
        "confidence REAL NOT NULL DEFAULT 0.0,"
        "samples INTEGER NOT NULL DEFAULT 1,"
        "created DATETIME NOT NULL,"
        "last_seen DATETIME NOT NULL,"
        "approved INTEGER NOT NULL DEFAULT 0"
        ")"),
    (3, "ALTER TABLE instincts ADD COLUMN ngram_hash TEXT"),
    (4, "ALTER TABLE executions ADD COLUMN cost_usd REAL NOT NULL DEFAULT 0"),
    (5, "ALTER TABLE instincts ADD COLUMN scope TEXT NOT NULL DEFAULT 'global'"),
    (5, "ALTER TABLE instincts ADD COLUMN project_id TEXT"),
    (5, "ALTER TABLE instincts ADD COLUMN successes INTEGER NOT NULL DEFAULT 0"),
    (5, "ALTER TABLE instincts ADD COLUMN failures INTEGER NOT NULL DEFAULT 0"),
    (5, "ALTER TABLE instincts ADD COLUMN evidence_count INTEGER NOT NULL DEFAULT 1"),
    (6, "ALTER TABLE executions ADD COLUMN model TEXT"),
    (6, "ALTER TABLE executions ADD COLUMN trace_digest TEXT"),
    (6, "ALTER TABLE executions ADD COLUMN phases_json TEXT"),
    (6, "ALTER TABLE executions ADD COLUMN repairs INTEGER NOT NULL DEFAULT 0"),
    (6, "ALTER TABLE executions ADD COLUMN output_ref TEXT"),
    (6, "ALTER TABLE executions ADD COLUMN judge_status TEXT"),
    (6, "ALTER TABLE executions ADD COLUMN failure_kind TEXT"),
    (6, "ALTER TABLE executions ADD COLUMN prompt_tokens INTEGER NOT NULL DEFAULT 0"),
    (6, "ALTER TABLE executions ADD COLUMN completion_tokens INTEGER NOT NULL DEFAULT 0"),
    (6, "ALTER TABLE executions ADD COLUMN cached_tokens INTEGER NOT NULL DEFAULT 0"),
    (6, "ALTER TABLE executions ADD COLUMN request_meta_json TEXT"),
    (6, "ALTER TABLE executions ADD COLUMN run_config_json TEXT"),
    (6, "ALTER TABLE loop_sessions ADD COLUMN history_json TEXT"),
    (6, "ALTER TABLE policy_decisions ADD COLUMN binding_info TEXT"),
    (6, "ALTER TABLE instincts ADD COLUMN ngram_hash2 TEXT"),
    (6, "ALTER TABLE instincts ADD COLUMN ngram_hash3 TEXT"),
    (6, "CREATE INDEX IF NOT EXISTS idx_executions_digest ON executions(trace_digest)"),
    (6, "CREATE INDEX IF NOT EXISTS idx_instincts_ngram2 ON instincts(ngram_hash2)"),
    (6, "CREATE INDEX IF NOT EXISTS idx_instincts_ngram3 ON instincts(ngram_hash3)"),
    (7, "CREATE TABLE IF NOT EXISTS perf_stats ("
        "model TEXT NOT NULL, skill_id TEXT NOT NULL, load_bucket TEXT NOT NULL,"
        "format_version INTEGER NOT NULL, samples INTEGER NOT NULL DEFAULT 0,"
        "samples_ok INTEGER NOT NULL DEFAULT 0, samples_fail INTEGER NOT NULL DEFAULT 0,"
        "avg_ms_ok REAL NOT NULL DEFAULT 0, avg_ms_fail REAL NOT NULL DEFAULT 0,"
        "avg_prompt_tokens REAL NOT NULL DEFAULT 0, avg_completion_tokens REAL NOT NULL DEFAULT 0,"
        "avg_cached_tokens REAL NOT NULL DEFAULT 0, avg_cost_usd REAL NOT NULL DEFAULT 0,"
        "updated DATETIME NOT NULL, PRIMARY KEY (model, skill_id, load_bucket, format_version))"),
    (7, "CREATE TABLE IF NOT EXISTS attempts ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER, skill_id TEXT NOT NULL,"
        "model TEXT, dedupe_hash TEXT NOT NULL, parent_id INTEGER,"
        "round_idx INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'pending',"
        "created DATETIME NOT NULL, updated DATETIME NOT NULL)"),
    (7, "CREATE INDEX IF NOT EXISTS idx_attempts_dedupe ON attempts(dedupe_hash)"),
]


def _stored_version(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT value FROM schema_meta WHERE key = 'schema_version'"
    ).fetchone()
    return int(row[0]) if row else 0


def _set_version(conn: sqlite3.Connection, version: int) -> None:
    conn.execute(
        "INSERT INTO schema_meta(key, value) VALUES ('schema_version', ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (str(version),),
    )


def init_db(db_path: Path) -> None:
    """Create or migrate the database. Additive only; refuses future versions."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        conn.executescript(SCHEMA)
        stored = _stored_version(conn)
        if stored > SCHEMA_VERSION:
            raise RuntimeError(
                f"database schema version {stored} is newer than supported "
                f"{SCHEMA_VERSION}; upgrade agent-foundry"
            )
        if stored == 0:
            # No version marker: either a fresh DB (SCHEMA already complete) or
            # an old DB. Run every migration; duplicate-column errors are the
            # expected no-op for the fresh case.
            pass
        latest = stored
        for version, sql in MIGRATIONS:
            try:
                conn.execute(sql)
            except sqlite3.OperationalError as exc:
                message = str(exc).lower()
                if "duplicate column name" not in message and "already exists" not in message:
                    raise
            latest = version
            _set_version(conn, latest)
        if latest != SCHEMA_VERSION:
            _set_version(conn, SCHEMA_VERSION)
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
                  cost_usd: float = 0.0,
                  model: str | None = None,
                  trace_digest: str | None = None,
                  phases: dict | None = None,
                  repairs: int = 0,
                  output_ref: str | None = None,
                  judge_status: str | None = None,
                  failure_kind: str | None = None,
                  prompt_tokens: int = 0,
                  completion_tokens: int = 0,
                  cached_tokens: int = 0,
                  request_meta: dict | None = None,
                  run_config: dict | None = None) -> int:
    init_db(db_path)
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        cur = conn.execute(
            """INSERT INTO executions
            (timestamp, skill_id, prompt, output, tokens_used, duration_seconds,
             success, error, planner_score, was_fallback,
             judge_corr, judge_slop, judge_scope, judge_verdict, cost_usd,
             model, trace_digest, phases_json, repairs, output_ref, judge_status,
             failure_kind, prompt_tokens, completion_tokens, cached_tokens,
             request_meta_json, run_config_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                skill_id, prompt, output, int(tokens_used), float(duration_seconds),
                1 if success else 0, error, planner_score,
                1 if was_fallback else 0,
                judge_corr, judge_slop, judge_scope, judge_verdict,
                float(cost_usd),
                model, trace_digest,
                json.dumps(phases, sort_keys=True) if phases is not None else None,
                int(repairs), output_ref, judge_status, failure_kind,
                int(prompt_tokens), int(completion_tokens), int(cached_tokens),
                json.dumps(_jsonable(request_meta), sort_keys=True) if request_meta is not None else None,
                json.dumps(_jsonable(run_config), sort_keys=True) if run_config is not None else None,
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
                    judge_corr, judge_slop, judge_scope, judge_verdict,
                    model, trace_digest, judge_status, failure_kind, output_ref,
                    repairs, prompt_tokens, completion_tokens, cached_tokens
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
            "judge_corr", "judge_slop", "judge_scope", "judge_verdict",
            "model", "trace_digest", "judge_status", "failure_kind", "output_ref",
            "repairs", "prompt_tokens", "completion_tokens", "cached_tokens")
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
                        receipt_hash: str = "",
                        binding_info: dict | None = None) -> int:
    """Record one policy decision for later audit."""
    init_db(db_path)
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        cur = conn.execute(
            """INSERT INTO policy_decisions
            (timestamp, action_kind, decision, rule_id, detail, receipt_hash, binding_info)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (datetime.now(timezone.utc).isoformat(), action_kind, decision,
             rule_id, detail, receipt_hash,
             json.dumps(binding_info, sort_keys=True) if binding_info is not None else None),
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


def create_loop_session(db_path: Path, prompt: str, skill_id: str,
                        history: list | None = None) -> int:
    init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        cur = conn.execute(
            """INSERT INTO loop_sessions
               (prompt, skill_id, status, turns, history_json, created, updated)
               VALUES (?, ?, 'running', 0, ?, ?, ?)""",
            (prompt, skill_id,
             json.dumps(history, ensure_ascii=False) if history is not None else None,
             now, now),
        )
        return int(cur.lastrowid)
    finally:
        conn.close()


def update_loop_session(db_path: Path, session_id: int, *, status: str | None = None,
                        output: str | None = None, increment_turn: bool = False,
                        history: list | None = None) -> None:
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
        if history is not None:
            conn.execute("UPDATE loop_sessions SET history_json = ?, updated = ? WHERE id = ?",
                         (json.dumps(history, ensure_ascii=False), now, session_id))
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
            """SELECT id, prompt, skill_id, status, turns, output, history_json,
                      created, updated
               FROM loop_sessions WHERE id = ?""",
            (session_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    try:
        history = json.loads(row[6]) if row[6] else []
    except (TypeError, ValueError):
        history = []
    return {"id": row[0], "prompt": row[1], "skill_id": row[2], "status": row[3],
            "turns": row[4], "output": row[5], "history": history,
            "created": row[7], "updated": row[8]}


def get_execution(db_path: Path, execution_id: int) -> dict | None:
    """Full execution row, including output_ref and request metadata."""
    init_db(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM executions WHERE id = ?", (execution_id,)).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def update_execution_judge(db_path: Path, execution_id: int, *,
                           scores: dict | None, status: str,
                           model: str = "") -> bool:
    scores = scores or {}
    init_db(db_path)
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        cur = conn.execute(
            """UPDATE executions
               SET judge_corr = ?, judge_slop = ?, judge_scope = ?,
                   judge_verdict = ?, judge_status = ?, model = COALESCE(NULLIF(?, ''), model)
               WHERE id = ?""",
            (scores.get("correctness"), scores.get("slop"), scores.get("scope"),
             scores.get("verdict"), status, model, execution_id),
        )
        return cur.rowcount > 0
    finally:
        conn.close()


def get_model_success_counts(db_path: Path, skill_id: str | None = None) -> list[dict]:
    init_db(db_path)
    sql = """SELECT skill_id, COALESCE(model, ''), SUM(success), COUNT(*)
             FROM executions
             WHERE model IS NOT NULL"""
    params: list[Any] = []
    if skill_id:
        sql += " AND skill_id = ?"
        params.append(skill_id)
    sql += " GROUP BY skill_id, model"
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    return [
        {"skill_id": r[0], "model": r[1], "successes": int(r[2] or 0),
         "failures": int(r[3] or 0) - int(r[2] or 0)}
        for r in rows
    ]


def repair_stale_sessions(db_path: Path, older_than_hours: int = 24) -> int:
    """Mark abandoned `running` sessions as failed. Returns rows changed."""
    if not db_path.exists():
        return 0
    init_db(db_path)
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=max(1, older_than_hours))).isoformat()
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        cur = conn.execute(
            """UPDATE loop_sessions SET status = 'failed', updated = ?
               WHERE status = 'running' AND updated < ?""",
            (datetime.now(timezone.utc).isoformat(), cutoff),
        )
        return cur.rowcount
    finally:
        conn.close()


def prune_db(db_path: Path, *, older_than_days: int, dry_run: bool = False,
             class_days: dict[str, int] | None = None) -> dict:
    """Delete rows older than the cutoff from append-only tables.

    `class_days` overrides the default cutoff per table, mirroring retention
    classes: executions, observations, policy_decisions, perf_stats.
    """
    if older_than_days <= 0:
        raise ValueError("older_than_days must be > 0")
    if not db_path.exists():
        return {"executions": 0, "observations": 0, "policy_decisions": 0, "perf_stats": 0}
    init_db(db_path)
    tables = {
        "executions": ("timestamp", "executions"),
        "observations": ("timestamp", "observations"),
        "policy_decisions": ("timestamp", "policy_decisions"),
        "perf_stats": ("updated", "perf_stats"),
    }
    overrides = class_days or {}
    counts: dict[str, int] = {}
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        for name, (column, table) in tables.items():
            days = int(overrides.get(name, older_than_days))
            if days <= 0:
                counts[name] = 0
                continue
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            count = conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE {column} < ?", (cutoff,)
            ).fetchone()[0]
            counts[name] = int(count or 0)
            if not dry_run and count:
                conn.execute(f"DELETE FROM {table} WHERE {column} < ?", (cutoff,))
    finally:
        conn.close()
    return counts


def start_attempt(db_path: Path, *, skill_id: str, model: str,
                  dedupe_hash: str, session_id: int | None = None,
                  parent_id: int | None = None, round_idx: int = 0) -> int:
    init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        cur = conn.execute(
            """INSERT INTO attempts
               (session_id, skill_id, model, dedupe_hash, parent_id, round_idx,
                status, created, updated)
               VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)""",
            (session_id, skill_id, model, dedupe_hash, parent_id, round_idx, now, now),
        )
        return int(cur.lastrowid)
    finally:
        conn.close()


def finish_attempt(db_path: Path, attempt_id: int, status: str) -> bool:
    if status not in ("ok", "failed", "skipped"):
        raise ValueError("status must be ok, failed, or skipped")
    init_db(db_path)
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        cur = conn.execute(
            "UPDATE attempts SET status = ?, updated = ? WHERE id = ?",
            (status, datetime.now(timezone.utc).isoformat(), attempt_id),
        )
        return cur.rowcount > 0
    finally:
        conn.close()


def update_skill_weights(db_path: Path) -> int:
    """Recompute weights from per-axis sums and denominators.

    Ratios are sum(numerator)/sum(denominator), never an average of per-row
    means. Axes with a zero denominator are excluded instead of nulling the
    result. Feedback is weighted by feedback rows only.
    """
    init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    updated = 0
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        rows = conn.execute(
            """SELECT skill_id,
                      SUM(COALESCE(judge_corr, 0)), COUNT(judge_corr),
                      SUM(COALESCE(judge_slop, 0)), COUNT(judge_slop),
                      SUM(COALESCE(judge_scope, 0)), COUNT(judge_scope),
                      SUM(CASE feedback WHEN 1 THEN 1 WHEN -1 THEN -1 ELSE 0 END),
                      COUNT(feedback)
               FROM executions
               GROUP BY skill_id
               HAVING COUNT(judge_corr) + COUNT(judge_slop) + COUNT(judge_scope)
                    + COUNT(feedback) > 0"""
        ).fetchall()
        for (skill_id, corr_sum, corr_n, slop_sum, slop_n,
             scope_sum, scope_n, feedback_sum, feedback_n) in rows:
            axis_means = [
                axis_sum / axis_n
                for axis_sum, axis_n in (
                    (corr_sum, corr_n), (slop_sum, slop_n), (scope_sum, scope_n),
                )
                if axis_n
            ]
            base = (sum(axis_means) / len(axis_means) / 10.0) if axis_means else 0.5
            feedback_mean = (float(feedback_sum or 0) / feedback_n) if feedback_n else 0.0
            weight = 0.8 + 0.4 * base + 0.05 * feedback_mean
            weight = max(0.6, min(1.4, weight))
            samples = corr_n + slop_n + scope_n + feedback_n
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
        # Engram hashes from the first usable positive prompt for this skill
        hashes = ("", "", "")
        for prompt in skill_prompts[skill_id]:
            candidate = _ngram_hashes(prompt)
            if candidate[0]:
                hashes = candidate
                break

        with sqlite3.connect(str(db_path)) as conn:
            existing = conn.execute(
                "SELECT id, confidence, samples FROM instincts WHERE source_skill_id = ? AND trigger_pattern = ?",
                (skill_id, pattern)
            ).fetchone()
            if existing:
                conn.execute(
                    """UPDATE instincts
                       SET confidence = ?, samples = samples + 1, last_seen = ?,
                           ngram_hash = COALESCE(?, ngram_hash),
                           ngram_hash2 = COALESCE(?, ngram_hash2),
                           ngram_hash3 = COALESCE(?, ngram_hash3)
                       WHERE id = ?""",
                    (min(1.0, existing[1] + 0.1), now,
                     hashes[0] or None, hashes[1] or None, hashes[2] or None,
                     existing[0])
                )
                results["updated_instincts"] += 1
            else:
                conn.execute(
                    """INSERT INTO instincts
                    (source_skill_id, trigger_pattern, ngram_hash, ngram_hash2,
                     ngram_hash3, confidence, samples, created, last_seen, approved)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
                    (skill_id, pattern, hashes[0] or None, hashes[1] or None,
                     hashes[2] or None, 0.3, 1, now, now)
                )
                results["new_instincts"] += 1
                results["patterns_found"].append({
                    "skill": skill_id, "pattern": pattern,
                    "ngram_hash": hashes[0],
                })
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
        hashes = ("", "", "")
        for prompt in bucket["prompts"]:
            candidate = _ngram_hashes(prompt)
            if candidate[0]:
                hashes = candidate
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
                           ngram_hash2 = COALESCE(?, ngram_hash2),
                           ngram_hash3 = COALESCE(?, ngram_hash3),
                           last_seen = ?
                       WHERE id = ?""",
                    (confidence, evidence, successes, failures, evidence,
                     hashes[0] or None, hashes[1] or None, hashes[2] or None,
                     now, existing[0]),
                )
                results["updated_instincts"] += 1
            else:
                conn.execute(
                    """INSERT INTO instincts
                    (source_skill_id, trigger_pattern, ngram_hash, ngram_hash2,
                     ngram_hash3, confidence, samples, created, last_seen, approved,
                     scope, project_id, successes, failures, evidence_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?)""",
                    (skill_id, pattern, hashes[0] or None, hashes[1] or None,
                     hashes[2] or None, confidence, evidence, now, now,
                     scope, pid, successes, failures, evidence),
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
