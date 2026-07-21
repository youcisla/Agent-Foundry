"""FastAPI daemon: /health, /index, /plan, /execute, /loop, /events (SSE), /site-data."""
from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

# Repo + generated web assets (used by the live-update SSE endpoint for local dev).
_REPO = Path(__file__).resolve().parent.parent
_WEB = _REPO / "web"


def _site_signature() -> str:
    """A cheap fingerprint of the skill/agent sources so the SSE loop can detect edits."""
    parts = []
    for base in ("skills", "agents"):
        d = _REPO / base
        if not d.exists():
            continue
        for f in sorted(d.rglob("*.md")):
            try:
                parts.append(f"{f.relative_to(_REPO)}:{int(f.stat().st_mtime)}")
            except OSError:
                continue
    return "|".join(parts)

from .config import Config, LOG_DB_PATH
from .executor import execute as executor_run
from .indexer import (
    build_index,
    get_index_cached,
    invalidate_cache,
    write_index,
)
from .logging_db import (
    count_executions,
    log_execution,
    set_feedback,
    learn,
    list_instincts,
    approve_instinct,
    get_stats as db_stats,
    engram_lookup,
)
from .loop import run_loop
from .models import (
    ExecuteRequest,
    FeedbackRequest,
    IndexResponse,
    LearnResponse,
    LoopRequest,
    PlanRequest,
)


def create_app(cfg: Config | None = None) -> FastAPI:
    cfg = cfg or Config.load()
    app = FastAPI(title="Agent Foundry", version="0.2.0")
    db_path = LOG_DB_PATH

    # Dev-only: allow the statically served site (different origin) to reach the
    # SSE + site-data endpoints for instant live updates.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return {"status": "ok", "skills_indexed": 0}

    @app.get("/site-data")
    def site_data():
        """Serve the generated data.json consumed by the reactive store (store.js)."""
        f = _WEB / "data.json"
        if not f.exists():
            raise HTTPException(status_code=404, detail="data.json not generated yet — run scripts/gen-site-data.py")
        return JSONResponse(json.loads(f.read_text(encoding="utf-8")))

    @app.get("/events")
    async def events():
        """Server-Sent Events: emit a 'changed' event when skill/agent sources change."""
        async def stream():
            last = _site_signature()
            yield "event: changed\ndata: init\n\n"
            beat = 0
            while True:
                await asyncio.sleep(1.0)
                sig = _site_signature()
                if sig != last:
                    last = sig
                    yield "event: changed\ndata: update\n\n"
                else:
                    beat += 1
                    if beat >= 15:  # heartbeat keeps the connection alive
                        beat = 0
                        yield ": keep-alive\n\n"
        return StreamingResponse(stream(), media_type="text/event-stream")

    @app.post("/index", response_model=IndexResponse)
    def do_index():
        skills_dir = Path(cfg.core.skills_dir).expanduser()
        if not skills_dir.exists():
            raise HTTPException(status_code=400, detail=f"skills_dir does not exist: {skills_dir}")

        t0 = time.time()
        idx = build_index(skills_dir)
        out = Path(cfg.core.index_path).expanduser()
        write_index(idx, out)
        invalidate_cache(out)

        # Refresh /health cache lazily
        return IndexResponse(
            total_skills=len(idx.skills),
            took_ms=(time.time() - t0) * 1000.0,
        )

    @app.post("/plan")
    def do_plan(req: PlanRequest):
        idx = get_index_cached(Path(cfg.core.index_path).expanduser(),
                                ttl_seconds=cfg.core.index_cache_ttl_seconds)
        if idx is None:
            raise HTTPException(status_code=409,
                                detail="No index. POST /index first.")
        # Engram fast-path: if we have a high-confidence cached routing for this
        # prompt's N-gram fingerprint, use it directly. Falls through to planner
        # otherwise.
        eg = engram_lookup(db_path, req.prompt, min_confidence=0.6)
        if eg:
            from .planner import plan as planner_run
            full = planner_run(req, idx, cfg.planner)
            return {**full.model_dump(), "engram_cache_hit": eg}
        from .planner import plan as planner_run
        return planner_run(req, idx, cfg.planner)

    @app.get("/engram")
    def do_engram_lookup(prompt: str):
        """Engram-style O(1) instinct lookup for a prompt."""
        hit = engram_lookup(db_path, prompt, min_confidence=0.5)
        return {"hit": hit}

    @app.post("/execute")
    def do_execute(req: ExecuteRequest):
        idx = get_index_cached(Path(cfg.core.index_path).expanduser(),
                                ttl_seconds=cfg.core.index_cache_ttl_seconds)
        if idx is None:
            raise HTTPException(status_code=409,
                                detail="No index. POST /index first.")
        return executor_run(req, model=cfg.core.default_llm,
                            skill_paths=idx.skill_paths,
                            db_path=db_path)

    @app.post("/loop")
    def do_loop(req: LoopRequest):
        # Resolve model override if any
        model_override = req.model
        # run_loop uses cfg.core.default_llm unless model_override provided
        return run_loop(req, cfg=cfg, db_path=db_path, model_override=model_override)

    @app.get("/stats")
    def stats():
        return {"executions": count_executions(db_path)}

    @app.post("/feedback")
    def do_feedback(req: FeedbackRequest):
        ok = set_feedback(db_path, req.execution_id, req.feedback)
        if not ok:
            raise HTTPException(status_code=404, detail="Execution not found or invalid feedback")
        return {"ok": True}

    @app.post("/learn")
    def do_learn():
        result = learn(db_path)
        return LearnResponse(
            new_instincts=result["new_instincts"],
            updated_instincts=result["updated_instincts"],
            patterns_found=result["patterns_found"],
        )

    @app.get("/instincts")
    def get_instincts(approved: bool = False):
        return {"instincts": list_instincts(db_path, approved_only=approved)}

    @app.post("/instincts/{instinct_id}/approve")
    def approve(instinct_id: int):
        ok = approve_instinct(db_path, instinct_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Instinct not found")
        return {"ok": True}

    return app
