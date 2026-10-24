import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class DbLifecycleTests(unittest.TestCase):
    def test_child_process_open_prune_close(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "log.db"
            code = (
                "from pathlib import Path;"
                "from agent_foundry.logging_db import init_db, prune_db;"
                f"db=Path(r'{db}');"
                "init_db(db); prune_db(db, older_than_days=30, dry_run=True);"
                "init_db(db); print('ok')"
            )
            result = subprocess.run(
                [sys.executable, "-c", code], cwd=ROOT,
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("ok", result.stdout)

    def test_bench_refresh_and_compare(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "log.db"
            baseline = Path(d) / "baseline.json"
            from agent_foundry.logging_db import init_db
            from agent_foundry.perf_cache import record_sample
            init_db(db)
            record_sample(db, model="m", skill_id="s", queue_depth=1,
                          duration_ms=100, success=True)
            refresh = subprocess.run(
                [sys.executable, "scripts/foundry-bench.py", "--db", str(db),
                 "--baseline", str(baseline), "--refresh-baseline"],
                cwd=ROOT, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(refresh.returncode, 0, refresh.stderr)
            data = json.loads(baseline.read_text())
            self.assertIn("m|s|1", data)
            check = subprocess.run(
                [sys.executable, "scripts/foundry-bench.py", "--db", str(db),
                 "--baseline", str(baseline)],
                cwd=ROOT, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(check.returncode, 0, check.stderr)
