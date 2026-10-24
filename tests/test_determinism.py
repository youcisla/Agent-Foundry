import json
import tempfile
import unittest
from pathlib import Path

from agent_foundry.indexer import build_index
from agent_foundry.models import ExecuteRequest
from agent_foundry.executor import execute
from agent_foundry.replay import trace_digest
from tests.provider_stub import CompletionStub

ROOT = Path(__file__).resolve().parent.parent


class DeterminismTests(unittest.TestCase):
    def test_serial_and_concurrent_digests_match(self):
        import concurrent.futures
        from unittest.mock import patch

        stub = CompletionStub()
        request = ExecuteRequest(skill_id="api-design", prompt="design an API",
                                 seed=7, temperature=0.0)
        skills = ROOT / "skills"

        def run_once():
            return execute(request, model="test-model",
                           skill_paths={"api-design": str(
                               next(skills.rglob("api-design/SKILL.md")))},
                           options={"spill_enabled": False})

        with patch("agent_foundry.executor.complete", stub):
            serial = [run_once().trace_digest for _ in range(4)]
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                concurrent_digests = list(
                    pool.map(lambda _: run_once().trace_digest, range(4))
                )
        self.assertEqual(len(set(serial + concurrent_digests)), 1)

    def test_digest_changes_with_output_and_skill_hash(self):
        base = dict(skill_id="s", skill_sha256="a" * 64, models=["m"],
                    messages=[{"role": "user", "content": "p"}], output="o")
        self.assertNotEqual(trace_digest(**base),
                            trace_digest(**{**base, "output": "o2"}))
        self.assertNotEqual(trace_digest(**base),
                            trace_digest(**{**base, "skill_sha256": "b" * 64}))

    def test_digest_ignores_provider_only_keys(self):
        base = dict(skill_id="s", skill_sha256="a" * 64, models=["m"],
                    output="o")
        a = trace_digest(**base, messages=[{"role": "user", "content": "p"}])
        b = trace_digest(**base, messages=[{"role": "user", "content": "p",
                                            "cache_control": {"x": 1}}])
        self.assertEqual(a, b)
