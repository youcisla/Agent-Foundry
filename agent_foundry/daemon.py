"""FastAPI daemon: /health, /index, /plan, /execute, /loop."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .config import Config, LOG_DB_PATH
from .executor import execute as executor_run
from .indexer import (
    build_index,
    get_index_cached,
    invalidate_cache,
    write_index,
)
from .logging_db import count_executions
from .loop import run_loop
from .models import (
    ExecuteRequest,
    IndexResponse,
    LoopRequest,
    PlanRequest,
)


def create_app(cfg: Config | None = None) -> FastAPI:
    cfg = cfg or Config.load()
    app = FastAPI(title="Agent Foundry", version="0.2.0")
    db_path = LOG_DB_PATH

    @app.get("/health")
    def health():
        return {"status": "ok", "skills_indexed": 0}

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
        from .planner import plan as planner_run
        return planner_run(req, idx, cfg.planner)

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

    return app
