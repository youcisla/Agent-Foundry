import json
import tempfile
import unittest
from pathlib import Path

from agent_foundry.config import Config, PlannerConfig
from agent_foundry.executor import _verify_integrity
from agent_foundry.indexer import build_index, parse_frontmatter, write_index
from agent_foundry.logging_db import (
    create_loop_session,
    get_loop_session,
    get_skill_weights,
    log_execution,
    update_loop_session,
    update_skill_weights,
)
from agent_foundry.loop import resume_loop
from agent_foundry.mcp_server import McpServer
from agent_foundry.models import LoopResumeRequest, PlanRequest
from agent_foundry.planner import _safe_graph_path, plan

ROOT = Path(__file__).resolve().parent.parent


class IndexerTests(unittest.TestCase):
    def test_inline_tags_list(self):
        fm = parse_frontmatter("---\nname: x\ndescription: d\ntags: [a, b, c]\n---\n")
        self.assertEqual(fm["tags"], ["a", "b", "c"])

    def test_all_skill_files_indexed(self):
        idx = build_index(ROOT / "skills")
        files = list((ROOT / "skills").rglob("SKILL.md"))
        real = [s for s in idx.skills if not s.is_fallback]
        self.assertEqual(len(real), len(files))
        self.assertTrue(all(s.sha256 for s in real))


class PlannerTests(unittest.TestCase):
    def test_plan_does_not_crash(self):
        idx = build_index(ROOT / "skills")
        resp = plan(PlanRequest(prompt="design a REST API for payments with pagination"),
                    idx, PlannerConfig())
        self.assertGreaterEqual(len(resp.results), 1)

    def test_weights_change_ranking_score(self):
        idx = build_index(ROOT / "skills")
        prompt = "design a REST API for payments with pagination"
        base = plan(PlanRequest(prompt=prompt), idx, PlannerConfig())
        top = base.results[0].skill_id
        weighted = plan(PlanRequest(prompt=prompt), idx, PlannerConfig(),
                        weights={top: 1.4})
        self.assertGreater(weighted.results[0].score, base.results[0].score)

    def test_rerank_skipped_when_disabled(self):
        from unittest.mock import patch
        idx = build_index(ROOT / "skills")
        with patch("agent_foundry.planner._llm_rerank",
                   side_effect=AssertionError("rerank should not run")):
            resp = plan(PlanRequest(prompt="design a REST API for payments"),
                        idx, PlannerConfig(rerank_enabled=False),
                        rerank_model="gpt-4o")
        self.assertGreaterEqual(len(resp.results), 1)

    def test_graph_path_rejects_outside_and_non_json(self):
        with tempfile.TemporaryDirectory() as d:
            evil = Path(d) / "evil.json"
            evil.write_text("{}", encoding="utf-8")
            self.assertIsNone(_safe_graph_path(str(evil)))
            md = Path(d) / "evil.md"
            md.write_text("{}", encoding="utf-8")
            self.assertIsNone(_safe_graph_path(str(md)))
        self.assertIsNone(_safe_graph_path("relative/graph.json"))
        self.assertIsNone(_safe_graph_path(None))


class LoopSessionTests(unittest.TestCase):
    def test_session_lifecycle(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "log.db"
            sid = create_loop_session(db, "first prompt", "api-design")
            session = get_loop_session(db, sid)
            self.assertEqual(session["status"], "running")
            self.assertEqual(session["turns"], 0)
            update_loop_session(db, sid, status="completed", output="answer",
                                increment_turn=True)
            session = get_loop_session(db, sid)
            self.assertEqual(session["status"], "completed")
            self.assertEqual(session["turns"], 1)
            self.assertEqual(session["output"], "answer")
            self.assertIsNone(get_loop_session(db, 9999))

    def test_resume_missing_session_fails(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "log.db"
            resp = resume_loop(LoopResumeRequest(session_id=42, prompt="more"),
                               cfg=Config(), db_path=db)
            self.assertFalse(resp.success)
            self.assertIn("not found", resp.error)

    def test_resume_replays_history(self):
        from unittest.mock import patch
        import dataclasses

        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "log.db"
            index_path = Path(d) / "index.json"
            write_index(build_index(ROOT / "skills"), index_path)
            cfg = dataclasses.replace(
                Config(), core=dataclasses.replace(Config().core, index_path=str(index_path))
            )
            sid = create_loop_session(db, "first", "api-design")
            update_loop_session(db, sid, status="completed", output="prior answer",
                                increment_turn=True)
            captured = {}

            def fake_complete(messages, **kwargs):
                captured["messages"] = messages
                return ("second answer", 10, 0.001)

            with patch("agent_foundry.loop.complete", fake_complete):
                resp = resume_loop(LoopResumeRequest(session_id=sid, prompt="follow up"),
                                   cfg=cfg, db_path=db)
            self.assertTrue(resp.success)
            self.assertEqual(resp.session_id, sid)
            roles = [m["role"] for m in captured["messages"]]
            self.assertEqual(roles, ["system", "user", "assistant", "user"])
            self.assertEqual(captured["messages"][2]["content"], "prior answer")
            self.assertEqual(get_loop_session(db, sid)["turns"], 2)


class IntegrityTests(unittest.TestCase):
    def test_mismatch_raises(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "SKILL.md"
            p.write_text("hello", encoding="utf-8")
            with self.assertRaises(ValueError):
                _verify_integrity(p, "0" * 64)

    def test_empty_hash_skips(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "SKILL.md"
            p.write_text("hello", encoding="utf-8")
            _verify_integrity(p, "")


class WeightsTests(unittest.TestCase):
    def test_judge_scores_update_weights(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "log.db"
            log_execution(db, skill_id="api-design", prompt="p", output="o",
                          tokens_used=1, duration_seconds=0.1, success=True,
                          judge_corr=9, judge_slop=8, judge_scope=9)
            updated = update_skill_weights(db)
            self.assertEqual(updated, 1)
            weights = get_skill_weights(db)
            self.assertGreater(weights["api-design"], 1.0)


class McpTests(unittest.TestCase):
    def test_initialize_and_tools(self):
        server = McpServer(Config())
        init = server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        self.assertEqual(init["result"]["serverInfo"]["name"], "agent-foundry")
        tools = server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        names = {t["name"] for t in tools["result"]["tools"]}
        self.assertEqual(names, {"plan", "execute", "list_skills", "get_skill"})


class DaemonTests(unittest.TestCase):
    def test_plan_endpoint(self):
        from fastapi.testclient import TestClient
        import dataclasses
        from agent_foundry.daemon import create_app

        with tempfile.TemporaryDirectory() as d:
            index_path = Path(d) / "index.json"
            write_index(build_index(ROOT / "skills"), index_path)
            cfg = dataclasses.replace(
                Config(), core=dataclasses.replace(Config().core, index_path=str(index_path))
            )
            client = TestClient(create_app(cfg))
            r = client.post("/plan", json={"prompt": "design a REST API for payments"})
            self.assertEqual(r.status_code, 200)
            self.assertGreaterEqual(len(r.json()["results"]), 1)


class SiteDataTests(unittest.TestCase):
    def test_data_json_matches_skills(self):
        data = json.loads((ROOT / "web" / "data.json").read_text(encoding="utf-8"))
        files = list((ROOT / "skills").rglob("SKILL.md"))
        self.assertEqual(data["skill_count"], len(files))


if __name__ == "__main__":
    unittest.main()
