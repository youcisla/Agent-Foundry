import tempfile
import unittest
from pathlib import Path

from agent_foundry.logging_db import log_execution
from agent_foundry.retry_policy import allocate_attempts, success_rate


class RetryPolicyTests(unittest.TestCase):
    def test_unknown_rate_means_one_attempt(self):
        self.assertEqual(allocate_attempts(None), 1)

    def test_high_probability_stays_at_one(self):
        self.assertEqual(allocate_attempts(0.9), 1)

    def test_mid_probability_adds_attempts(self):
        self.assertEqual(allocate_attempts(0.5), 2)
        self.assertEqual(allocate_attempts(0.2), 2)
        self.assertEqual(allocate_attempts(0.2, marginal_threshold=0.1), 3)

    def test_cap(self):
        self.assertEqual(allocate_attempts(0.2, max_attempts=1), 1)

    def test_success_rate_floor_and_value(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "log.db"
            for _ in range(3):
                log_execution(db, skill_id="s", prompt="p", output="o",
                              tokens_used=1, duration_seconds=0.1,
                              success=True, model="m")
            self.assertIsNone(success_rate(db, skill_id="s", min_samples=10))
            rate = success_rate(db, skill_id="s", min_samples=2)
            self.assertAlmostEqual(rate, 4.0 / 5.0)
