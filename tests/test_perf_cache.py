import tempfile
import time
import unittest
from pathlib import Path

from agent_foundry.logging_db import init_db
from agent_foundry.perf_cache import estimate, load_bucket, record_sample


class PerfCacheTests(unittest.TestCase):
    def test_load_buckets(self):
        self.assertEqual(load_bucket(0), "1")
        self.assertEqual(load_bucket(1), "1")
        self.assertEqual(load_bucket(2), "2-4")
        self.assertEqual(load_bucket(8), "5-8")
        self.assertEqual(load_bucket(9), "9+")

    def test_running_mean_and_failure_split(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "log.db"
            for ms in (100, 200, 300):
                record_sample(db, model="m", skill_id="s", queue_depth=1,
                              duration_ms=ms, success=True,
                              prompt_tokens=10, completion_tokens=5)
            record_sample(db, model="m", skill_id="s", queue_depth=1,
                          duration_ms=900, success=False)
            est = estimate(db, model="m", skill_id="s", queue_depth=1)
            self.assertIsNotNone(est)
            self.assertAlmostEqual(est["avg_ms_ok"], 200.0)
            self.assertAlmostEqual(est["avg_ms_fail"], 900.0)
            self.assertEqual(est["samples_ok"], 3)
            self.assertEqual(est["samples_fail"], 1)

    def test_load_bucket_separates_estimates(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "log.db"
            record_sample(db, model="m", skill_id="s", queue_depth=1,
                          duration_ms=100, success=True)
            record_sample(db, model="m", skill_id="s", queue_depth=6,
                          duration_ms=500, success=True)
            low = estimate(db, model="m", skill_id="s", queue_depth=1)
            high = estimate(db, model="m", skill_id="s", queue_depth=6)
            self.assertNotEqual(low["avg_ms_ok"], high["avg_ms_ok"])

    def test_ttl_expiry(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "log.db"
            record_sample(db, model="m", skill_id="s", queue_depth=0,
                          duration_ms=100, success=True)
            self.assertIsNone(estimate(db, model="m", skill_id="s", ttl_seconds=-1))

    def test_disabled_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "log.db"
            record_sample(db, model="m", skill_id="s", queue_depth=0,
                          duration_ms=100, success=True, enabled=False)
            init_db(db)
            self.assertIsNone(estimate(db, model="m", skill_id="s"))
