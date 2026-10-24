import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_foundry.config import Config
from agent_foundry.executor import execute
from agent_foundry.judge import _extract_json_object, judge_output
from agent_foundry.logging_db import (
    _ngram_hashes,
    create_loop_session,
    list_instincts,
    log_execution,
    prune_db,
    repair_stale_sessions,
    start_attempt,
    finish_attempt,
    update_skill_weights,
    get_skill_weights,
)
from agent_foundry.loop import _compact_history
from agent_foundry.models import ExecuteRequest
from agent_foundry.verifiers import run


class EngramContractTests(unittest.TestCase):
    def test_order_sensitivity(self):
        a = _ngram_hashes("delete backup database")
        b = _ngram_hashes("backup database delete")
        self.assertNotEqual(a[0], b[0])
        self.assertTrue(all(a))

    def test_non_latin_prompt_hashes(self):
        self.assertTrue(_ngram_hashes("supprime la base de données"))
        self.assertTrue(_ngram_hashes("احذف قاعدة البيانات الآن"))

    def test_legacy_single_head_row_still_matches(self):
        import sqlite3
        from agent_foundry.logging_db import _legacy_hash, engram_lookup, init_db
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "log.db"
            init_db(db)
            prompt = "design rest api pagination cursor"
            conn = sqlite3.connect(str(db))
            conn.execute(
                """INSERT INTO instincts
                   (source_skill_id, trigger_pattern, ngram_hash, confidence,
                    samples, created, last_seen, approved)
                   VALUES ('api-design', 'pagination', ?, 0.9, 5, '', '', 1)""",
                (_legacy_hash(prompt),),
            )
            conn.commit()
            conn.close()
            hit = engram_lookup(db, prompt, min_confidence=0.1)
            self.assertIsNotNone(hit)
            self.assertEqual(hit["skill_id"], "api-design")


class JudgeContractTests(unittest.TestCase):
    def _fake_litellm(self, **completion_kwargs):
        import sys
        import types
        from unittest.mock import Mock
        module = types.ModuleType("litellm")
        module.completion = Mock(**completion_kwargs)
        return patch.dict(sys.modules, {"litellm": module})

    def test_call_failure_is_visible(self):
        with self._fake_litellm(side_effect=RuntimeError("boom")):
            result = judge_output("t", "o", model="m", retries=0)
        self.assertEqual(result.status, "call_failed")
        self.assertIsNone(result.scores)

    def test_unparseable_is_not_zero(self):
        class Resp:
            class Choice:
                class Msg:
                    content = "no json here"
                message = Msg()
            choices = [Choice()]
        with self._fake_litellm(return_value=Resp()):
            result = judge_output("t", "o", model="m", retries=0)
        self.assertEqual(result.status, "unparseable")
        self.assertIsNone(result.scores)

    def test_nested_json_parses(self):
        parsed = _extract_json_object(
            'text {"correctness": 8, "detail": {"a": [1, 2]}} tail'
        )
        self.assertEqual(parsed["correctness"], 8)
        self.assertEqual(parsed["detail"]["a"], [1, 2])


class ExecutionContractTests(unittest.TestCase):
    def test_provider_failure_kind(self):
        with patch("agent_foundry.executor.complete",
                   side_effect=RuntimeError("down")):
            resp = execute(ExecuteRequest(skill_id="x", prompt="p"),
                           model="m", skill_paths={},
                           options={"spill_enabled": False})
        self.assertFalse(resp.success)
        self.assertEqual(resp.failure_kind, "provider")

    def test_schema_failure_kind_and_repairs(self):
        schema = {"type": "object", "required": ["a"],
                  "properties": {"a": {"type": "string"}}}
        with patch("agent_foundry.executor.complete",
                   return_value=("not json", 5, 0.0)):
            resp = execute(
                ExecuteRequest(skill_id="x", prompt="p", output_schema=schema),
                model="m", skill_paths={},
                options={"spill_enabled": False},
            )
        self.assertFalse(resp.success)
        self.assertEqual(resp.failure_kind, "schema")
        self.assertEqual(resp.repairs, 1)


class CompactionTests(unittest.TestCase):
    def test_drops_oldest_but_keeps_tail(self):
        history = [{"user": "u" * 400, "assistant": "a" * 400}
                   for _ in range(5)]
        compacted, dropped, dropped_tokens = _compact_history(
            history, max_tokens=220, keep_turns=2,
        )
        self.assertEqual(len(compacted), 2)
        self.assertEqual(dropped, 3)
        self.assertGreater(dropped_tokens, 0)


class WeightDenominatorTests(unittest.TestCase):
    def test_feedback_uses_feedback_rows_only(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "log.db"
            for _ in range(10):
                log_execution(db, skill_id="s", prompt="p", output="o",
                              tokens_used=1, duration_seconds=0.1,
                              success=True, judge_corr=10,
                              judge_slop=10, judge_scope=10)
            log_execution(db, skill_id="s", prompt="p", output="o",
                          tokens_used=1, duration_seconds=0.1, success=True)
            conn = sqlite3.connect(str(db))
            conn.execute("UPDATE executions SET feedback=1 WHERE id=11")
            conn.commit()
            conn.close()
            update_skill_weights(db)
            self.assertAlmostEqual(get_skill_weights(db)["s"], 1.25, places=3)


class RetentionTests(unittest.TestCase):
    def test_prune_dry_run_and_delete(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "log.db"
            log_execution(db, skill_id="s", prompt="p", output="o",
                          tokens_used=1, duration_seconds=0.1, success=True)
            conn = sqlite3.connect(str(db))
            conn.execute("UPDATE executions SET timestamp='2000-01-01T00:00:00+00:00'")
            conn.commit()
            conn.close()
            dry = prune_db(db, older_than_days=30, dry_run=True)
            self.assertEqual(dry["executions"], 1)
            real = prune_db(db, older_than_days=30)
            self.assertEqual(real["executions"], 1)

    def test_stale_session_repair(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "log.db"
            sid = create_loop_session(db, "p", "s")
            conn = sqlite3.connect(str(db))
            conn.execute("UPDATE loop_sessions SET updated='2000-01-01T00:00:00+00:00'")
            conn.commit()
            conn.close()
            self.assertEqual(repair_stale_sessions(db, older_than_hours=1), 1)


class AttemptTests(unittest.TestCase):
    def test_attempt_lifecycle(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "log.db"
            aid = start_attempt(db, skill_id="s", model="m",
                                dedupe_hash="h", session_id=1)
            self.assertTrue(finish_attempt(db, aid, "ok"))


class VerifierTests(unittest.TestCase):
    def test_schema_verifier(self):
        spec = {"schema": {"type": "object", "required": ["a"],
                           "properties": {"a": {"type": "string"}}}}
        self.assertEqual(run("json_schema", {"a": "x"}, spec), "pass")
        self.assertEqual(run("json_schema", {"a": 1}, spec), "fail")
        self.assertEqual(run("missing", {}, spec), "unknown")

    def test_executor_verifier_wiring(self):
        schema = {"type": "object", "required": ["a"],
                  "properties": {"a": {"type": "string"}}}
        verifier = {"kind": "json_schema", "spec": {"schema": schema}}
        with patch("agent_foundry.executor.complete",
                   return_value=('{"a": "ok"}', 5, 0.0)):
            resp = execute(
                ExecuteRequest(skill_id="x", prompt="p", verifier=verifier),
                model="m", skill_paths={},
                options={"spill_enabled": False},
            )
        self.assertEqual(resp.verifier_verdict, "pass")
        self.assertTrue(resp.schema_valid)


class CalibrationTests(unittest.TestCase):
    def test_calibration_bins(self):
        import sqlite3
        from agent_foundry.calibration import calibration_report
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "log.db"
            log_execution(db, skill_id="s", prompt="p", output="o",
                          tokens_used=1, duration_seconds=0.1, success=True,
                          judge_corr=9)
            conn = sqlite3.connect(str(db))
            conn.execute("UPDATE executions SET feedback=1 WHERE id=1")
            conn.commit()
            conn.close()
            report = calibration_report(db, bins=5)
            self.assertEqual(report["samples"], 1)
            self.assertEqual(sum(b["samples"] for b in report["bins"]), 1)


class RetentionClassTests(unittest.TestCase):
    def test_class_override(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "log.db"
            log_execution(db, skill_id="s", prompt="p", output="o",
                          tokens_used=1, duration_seconds=0.1, success=True)
            conn = sqlite3.connect(str(db))
            conn.execute("UPDATE executions SET timestamp='2000-01-01T00:00:00+00:00'")
            conn.commit()
            conn.close()
            counts = prune_db(db, older_than_days=1,
                              class_days={"executions": 10000},
                              dry_run=True)
            self.assertEqual(counts["executions"], 0)


class CacheRootTests(unittest.TestCase):
    def test_env_precedence(self):
        from unittest.mock import patch
        from agent_foundry.spill import default_spill_root
        with patch.dict("os.environ", {"AF_SPILL_DIR": "/tmp/spill"}, clear=False):
            self.assertEqual(default_spill_root(), Path("/tmp/spill"))
        with patch.dict("os.environ", {"AF_CACHE_DIR": "/tmp/cache"}, clear=False):
            import os
            os.environ.pop("AF_SPILL_DIR", None)
            self.assertEqual(default_spill_root(), Path("/tmp/cache") / "artifacts")


class ConfigStrictTests(unittest.TestCase):
    def test_invalid_policy_mode_raises_in_strict_mode(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "config.toml"
            path.write_text("[core]\npolicy_mode = \"bogus\"\nstrict_config = true\n")
            with self.assertRaises(ValueError):
                Config.load(path)
