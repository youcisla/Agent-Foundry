"""Minimal MCP stdio server exposing plan/execute/list_skills/get_skill.

Implements JSON-RPC 2.0 over stdin/stdout with no extra dependencies.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .config import Config, LOG_DB_PATH
from .executor import execute as execute_skill
from .indexer import get_index_cached
from .models import ExecuteRequest
from .planner import rank_skills

PROTOCOL_VERSION = "2025-06-18"
SERVER_VERSION = __version__

TOOLS = [
    {
        "name": "plan",
        "description": "Rank Agent Foundry skills for a prompt.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "max_results": {"type": "integer", "default": 5},
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "execute",
        "description": "Run one skill against a prompt via the configured LLM.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "skill_id": {"type": "string"},
                "prompt": {"type": "string"},
                "model": {"type": "string"},
            },
            "required": ["skill_id", "prompt"],
        },
    },
    {
        "name": "list_skills",
        "description": "List indexed skills with category and description.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_skill",
        "description": "Return the full SKILL.md body for one skill.",
        "inputSchema": {
            "type": "object",
            "properties": {"skill_id": {"type": "string"}},
            "required": ["skill_id"],
        },
    },
]


class McpServer:
    def __init__(self, cfg: Config | None = None, db_path: Path | None = None):
        self.cfg = cfg or Config.load()
        self.db_path = db_path or LOG_DB_PATH

    def _index(self):
        idx = get_index_cached(Path(self.cfg.core.index_path).expanduser(),
                               ttl_seconds=self.cfg.core.index_cache_ttl_seconds)
        if idx is None:
            raise RuntimeError("No skill index. Run `agent-foundry index` first.")
        return idx

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "plan":
            idx = self._index()
            prompt = str(arguments.get("prompt", ""))
            max_results = int(arguments.get("max_results", 5))
            ranked = rank_skills(prompt, idx, self.cfg.planner,
                                 weights=_weights(self.db_path),
                                 rerank_model=(self.cfg.core.default_llm
                                               if self.cfg.planner.rerank_enabled else None))
            result = {
                "prompt": prompt,
                "results": [r.model_dump() for r in ranked[:max_results]],
                "total_available": len(idx.skills),
            }
            return _text(result)

        if name == "execute":
            idx = self._index()
            req = ExecuteRequest(
                skill_id=str(arguments["skill_id"]),
                prompt=str(arguments["prompt"]),
                model=arguments.get("model"),
            )
            resp = execute_skill(
                req, model=req.model or self.cfg.core.default_llm,
                skill_paths=idx.skill_paths,
                db_path=self.db_path,
                skill_hashes={s.id: s.sha256 for s in idx.skills},
                timeout_seconds=self.cfg.core.executor_timeout_seconds,
                max_tokens=self.cfg.core.executor_max_tokens,
                retries=self.cfg.core.executor_retries,
            )
            return _text(resp.model_dump())

        if name == "list_skills":
            idx = self._index()
            skills = [
                {"id": s.id, "name": s.name, "category": s.category,
                 "description": s.description}
                for s in idx.skills if not s.is_fallback
            ]
            return _text({"skills": skills, "count": len(skills)})

        if name == "get_skill":
            idx = self._index()
            skill_id = str(arguments["skill_id"])
            path = idx.skill_paths.get(skill_id)
            if not path or path.startswith("__virtual__:"):
                raise RuntimeError(f"unknown skill: {skill_id}")
            return _text({"skill_id": skill_id,
                          "content": Path(path).read_text(encoding="utf-8")})

        raise RuntimeError(f"unknown tool: {name}")

    def handle(self, msg: dict[str, Any]) -> dict[str, Any] | None:
        method = msg.get("method")
        msg_id = msg.get("id")

        if method == "initialize":
            return _result(msg_id, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "agent-foundry", "version": SERVER_VERSION},
            })
        if method in ("notifications/initialized", "initialized"):
            return None
        if method == "ping":
            return _result(msg_id, {})
        if method == "tools/list":
            return _result(msg_id, {"tools": TOOLS})
        if method == "tools/call":
            params = msg.get("params") or {}
            try:
                payload = self.call_tool(params.get("name", ""), params.get("arguments") or {})
                return _result(msg_id, payload)
            except Exception as exc:
                return _result(msg_id, {"content": [{"type": "text", "text": str(exc)}],
                                        "isError": True})
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"method not found: {method}"},
        }


def _weights(db_path: Path) -> dict[str, float]:
    try:
        from .logging_db import get_skill_weights
        return get_skill_weights(db_path)
    except Exception:
        return {}


def _text(value: Any) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False)}]}


def _result(msg_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def run_stdio(cfg: Config | None = None) -> None:
    """Serve MCP over stdin/stdout until EOF."""
    server = McpServer(cfg)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = server.handle(msg)
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()
