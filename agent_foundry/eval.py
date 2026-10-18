"""Paired skill evaluation: same task with and without a skill.

Task file format (JSON array):
  [{"id": "t1", "prompt": "...", "skill": "api-design", "verify": "grep -qi ok"}]

`verify` is an optional shell command. It receives the model output on stdin
and passes when the exit code is 0. Without a verifier the run is recorded as
unscored.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .config import Config, LOG_DB_PATH
from .executor import execute
from .indexer import GENERIC_REASONING_ID, get_index_cached
from .models import ExecuteRequest


def _verify(command: str, output: str) -> bool | None:
    if not command:
        return None
    try:
        proc = subprocess.run(
            command, shell=True, input=output, text=True,
            capture_output=True, timeout=60,
        )
        return proc.returncode == 0
    except Exception:
        return False


def run_eval(tasks_path: Path, *, cfg: Config, model: str | None = None,
             db_path: Path | None = None) -> dict[str, Any]:
    idx = get_index_cached(Path(cfg.core.index_path).expanduser(),
                           ttl_seconds=cfg.core.index_cache_ttl_seconds)
    if idx is None:
        raise RuntimeError("No skill index. Run `agent-foundry index` first.")
    tasks = json.loads(Path(tasks_path).read_text(encoding="utf-8"))
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("task file must be a non-empty JSON array")

    model_name = model or cfg.core.default_llm
    hashes = {s.id: s.sha256 for s in idx.skills}
    results = []
    for task in tasks:
        prompt = str(task["prompt"])
        skill_id = str(task.get("skill") or GENERIC_REASONING_ID)
        verify = str(task.get("verify") or "")

        with_resp = execute(
            ExecuteRequest(skill_id=skill_id, prompt=prompt, force=True),
            model=model_name, skill_paths=idx.skill_paths,
            db_path=db_path, skill_hashes=hashes,
            timeout_seconds=cfg.core.executor_timeout_seconds,
            max_tokens=cfg.core.executor_max_tokens,
            retries=cfg.core.executor_retries,
        )
        no_resp = execute(
            ExecuteRequest(skill_id=GENERIC_REASONING_ID, prompt=prompt, force=True),
            model=model_name, skill_paths=idx.skill_paths,
            db_path=db_path, skill_hashes=hashes,
            timeout_seconds=cfg.core.executor_timeout_seconds,
            max_tokens=cfg.core.executor_max_tokens,
            retries=cfg.core.executor_retries,
        )

        with_pass = _verify(verify, with_resp.output) if with_resp.success else False
        no_pass = _verify(verify, no_resp.output) if no_resp.success else False
        results.append({
            "id": task.get("id", prompt[:40]),
            "skill": skill_id,
            "with_skill_pass": with_pass,
            "no_skill_pass": no_pass,
            "with_skill_cost_usd": with_resp.cost_usd,
            "no_skill_cost_usd": no_resp.cost_usd,
        })

    scored = [r for r in results if r["with_skill_pass"] is not None]
    with_rate = (sum(1 for r in scored if r["with_skill_pass"]) / len(scored)) if scored else 0.0
    no_rate = (sum(1 for r in scored if r["no_skill_pass"]) / len(scored)) if scored else 0.0
    return {
        "tasks": results,
        "scored": len(scored),
        "with_skill_pass_rate": round(with_rate, 3),
        "no_skill_pass_rate": round(no_rate, 3),
        "skill_lift": round(with_rate - no_rate, 3),
        "total_cost_usd": round(sum(r["with_skill_cost_usd"] + r["no_skill_cost_usd"]
                                   for r in results), 4),
    }
