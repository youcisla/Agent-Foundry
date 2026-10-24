import sqlite3
import tempfile
import unittest
from pathlib import Path

from agent_foundry.logging_db import SCHEMA_VERSION, init_db


class MigrationTests(unittest.TestCase):
    def _columns(self, db: Path, table: str) -> set[str]:
        conn = sqlite3.connect(str(db))
        try:
            return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        finally:
            conn.close()

    def test_fresh_database_has_version_and_columns(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "log.db"
            init_db(db)
            conn = sqlite3.connect(str(db))
            version = conn.execute(
                "SELECT value FROM schema_meta WHERE key='schema_version'"
            ).fetchone()[0]
            conn.close()
            self.assertEqual(int(version), SCHEMA_VERSION)
            self.assertIn("trace_digest", self._columns(db, "executions"))
            self.assertIn("history_json", self._columns(db, "loop_sessions"))
            conn = sqlite3.connect(str(db))
            try:
                tables = {r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )}
            finally:
                conn.close()
            self.assertIn("perf_stats", tables)

    def test_repeated_init_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "log.db"
            init_db(db)
            init_db(db)
            init_db(db)

    def test_future_version_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "log.db"
            init_db(db)
            conn = sqlite3.connect(str(db))
            conn.execute("UPDATE schema_meta SET value='999' WHERE key='schema_version'")
            conn.commit()
            conn.close()
            with self.assertRaises(RuntimeError):
                init_db(db)

    def test_old_database_without_meta_is_migrated(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "log.db"
            conn = sqlite3.connect(str(db))
            conn.executescript(
                "CREATE TABLE executions (id INTEGER PRIMARY KEY, timestamp TEXT,"
                " skill_id TEXT, prompt TEXT, output TEXT, tokens_used INTEGER,"
                " duration_seconds REAL, success INTEGER, error TEXT,"
                " planner_score REAL, was_fallback INTEGER);"
            )
            conn.commit()
            conn.close()
            init_db(db)
            self.assertIn("trace_digest", self._columns(db, "executions"))
