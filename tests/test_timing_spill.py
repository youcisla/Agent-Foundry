import tempfile
import time
import unittest
from pathlib import Path

from agent_foundry.spill import preview, read_output, save_output
from agent_foundry.timing import PhaseTimer


class TimingTests(unittest.TestCase):
    def test_phases_record(self):
        timer = PhaseTimer()
        with timer.phase("a"):
            time.sleep(0.001)
        with timer.phase("b"):
            pass
        self.assertIn("a", timer.phases)
        self.assertIn("b", timer.phases)
        self.assertGreater(timer.phases["a"], 0)


class SpillTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            ref = save_output(Path(d), session_id=7, execution_id=1,
                              text="full output")
            self.assertIsNotNone(ref)
            self.assertEqual(read_output(ref), "full output")

    def test_empty_text_skips(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(save_output(Path(d), session_id=1,
                                          execution_id=1, text=""))

    def test_missing_ref_returns_none(self):
        self.assertIsNone(read_output(None))
        self.assertIsNone(read_output("/does/not/exist"))

    def test_preview(self):
        self.assertEqual(preview("abcdef", 3), "abc")
        self.assertEqual(preview("abcdef", 0), "abcdef")
