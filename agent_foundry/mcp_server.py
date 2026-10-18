"""Minimal MCP stdio server exposing ten tools: plan, execute, catalogue,
verification, policy, runtime status, history, and models.

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

def _annotations(title: str, *, read_only: bool = True, idempotent: bool = True,
                 open_world: bool = False) -> dict[str, Any]:
    """Standard MCP tool hints. Destructive is always false for this server."""
    return {
        "title": title,
        "readOnlyHint": read_only,
        "destructiveHint": False,
        "idempotentHint": idempotent,
        "openWorldHint": open_world,
    }


TOOLS = [
    {
        "name": "plan",
        "description": "Rank Agent Foundry skills for a prompt.",
        "annotations": _annotations("Plan skills"),
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
        "annotations": _annotations("Execute skill", read_only=False,
                                    idempotent=False, open_world=True),
        "inputSchema": {
            "type": "object",
            "properties": {
                "skill_id": {"type": "string"},
                "prompt": {"type": "string"},
                "model": {"type": "string"},
                "fallback_models": {"type": "array", "items": {"type": "string"}},
                "output_schema": {"type": "object"},
            },
            "required": ["skill_id", "prompt"],
        },
    },
    {
        "name": "list_skills",
        "description": "List indexed skills with category and description.",
        "annotations": _annotations("List skills"),
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "search_skills",
        "description": "Search skills by id, name, description, or tag.",
        "annotations": _annotations("Search skills"),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "category": {"type": "string", "enum": ["core", "optional"]},
                "limit": {"type": "integer", "default": 20},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_skill",
        "description": "Return the full SKILL.md body for one skill.",
        "annotations": _annotations("Get skill"),
        "inputSchema": {
            "type": "object",
            "properties": {"skill_id": {"type": "string"}},
            "required": ["skill_id"],
        },
    },
    {
        "name": "verify_skills",
        "description": "Verify the installed skill manifest, signature, and file hashes.",
        "annotations": _annotations("Verify skills"),
        "inputSchema": {
            "type": "object",
            "properties": {
                "root": {"type": "string"},
                "strict": {"type": "boolean", "default": False},
            },
        },
    },
    {
        "name": "check_action",
        "description": "Classify a shell, file, text, or network action against local policy.",
        "annotations": _annotations("Check action"),
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": ["shell", "file_write", "text", "network"]},
                "value": {"type": "string"},
                "context": {"type": "object"},
            },
            "required": ["kind", "value"],
        },
    },
    {
        "name": "runtime_status",
        "description": "Report runtime configuration, index state, and model routing.",
        "annotations": _annotations("Runtime status"),
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "execution_history",
        "description": "Read recent execution records without full output bodies.",
        "annotations": _annotations("Execution history"),
        "inputSchema": {
            "type": "object",
            "properties": {
                "skill_id": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
                "offset": {"type": "integer", "default": 0},
            },
        },
    },
    {
        "name": "list_models",
        "description": "List the model catalog and the configured default.",
        "annotations": _annotations("List models"),
        "inputSchema": {"type": "object", "properties": {}},
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
                fallback_models=arguments.get("fallback_models"),
                output_schema=arguments.get("output_schema"),
            )
            resp = execute_skill(
                req, model=req.model or self.cfg.core.default_llm,
                skill_paths=idx.skill_paths,
                db_path=self.db_path,
                skill_hashes={s.id: s.sha256 for s in idx.skills},
                timeout_seconds=self.cfg.core.executor_timeout_seconds,
                max_tokens=self.cfg.core.executor_max_tokens,
                retries=self.cfg.core.executor_retries,
                policy_mode=self.cfg.core.policy_mode,
                fallback_models=self.cfg.core.fallback_llms,
                attest_manifest=Path(self.cfg.core.skills_dir).expanduser()
                / ".agent-foundry-installed.json",
                attest_key_path=Path(self.cfg.core.attest_key_path).expanduser(),
                attest_strict=self.cfg.core.attest_strict,
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

        if name == "search_skills":
            idx = self._index()
            query = str(arguments.get("query", "")).lower().strip()
            category = arguments.get("category")
            limit = max(1, min(int(arguments.get("limit", 20)), 100))
            matches = []
            for s in idx.skills:
                if s.is_fallback or (category and s.category != category):
                    continue
                haystack = " ".join([s.id, s.name, s.description, *s.tags]).lower()
                if query in haystack:
                    matches.append({"id": s.id, "name": s.name,
                                    "category": s.category,
                                    "description": s.description, "tags": s.tags})
            return _text({"query": query, "skills": matches[:limit],
                          "count": len(matches[:limit]), "total_matches": len(matches)})

        if name == "get_skill":
            idx = self._index()
            skill_id = str(arguments["skill_id"])
            path = idx.skill_paths.get(skill_id)
            if not path or path.startswith("__virtual__:"):
                raise RuntimeError(f"unknown skill: {skill_id}")
            return _text({"skill_id": skill_id,
                          "content": Path(path).read_text(encoding="utf-8")})

        if name == "verify_skills":
            from .attest import MANIFEST_NAME, verify_manifest
            root = Path(arguments.get("root") or self.cfg.core.skills_dir).expanduser()
            result = verify_manifest(
                root / MANIFEST_NAME,
                Path(self.cfg.core.attest_key_path).expanduser(),
                root=root,
            )
            return _text(result.to_dict())

        if name == "check_action":
            from .policy import PolicyAction, evaluate
            action = PolicyAction(
                kind=str(arguments["kind"]),
                value=str(arguments["value"]),
                context=arguments.get("context") or {},
            )
            return _text(evaluate(action).to_dict())

        if name == "runtime_status":
            from .model_catalog import list_models as catalog
            index_path = Path(self.cfg.core.index_path).expanduser()
            skill_count = 0
            index_error = None
            try:
                skill_count = len([s for s in self._index().skills if not s.is_fallback])
            except Exception as exc:
                index_error = str(exc)
            return _text({
                "version": SERVER_VERSION,
                "config_path": str(self.cfg.config_path),
                "skills_dir": self.cfg.core.skills_dir,
                "index_path": str(index_path),
                "index_present": index_path.exists(),
                "index_error": index_error,
                "skill_count": skill_count,
                "default_model": self.cfg.core.default_llm,
                "fallback_models": self.cfg.core.fallback_llms,
                "model_catalog": catalog(),
                "policy_mode": self.cfg.core.policy_mode,
                "attest_strict": self.cfg.core.attest_strict,
                "daemon_port": self.cfg.core.daemon_port,
                "log_db": str(self.db_path),
            })

        if name == "execution_history":
            from .logging_db import list_executions
            rows = list_executions(
                self.db_path,
                skill_id=arguments.get("skill_id"),
                limit=int(arguments.get("limit", 20)),
                offset=int(arguments.get("offset", 0)),
            )
            return _text({"executions": rows, "count": len(rows)})

        if name == "list_models":
            from .model_catalog import list_models as catalog
            return _text({"models": catalog(),
                          "default": self.cfg.core.default_llm,
                          "fallbacks": self.cfg.core.fallback_llms})

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
