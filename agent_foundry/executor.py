"""Executor: run a skill (prompt + body) via LiteLLM."""
from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any

from .indexer import GENERIC_REASONING_ID, GENERIC_REASONING_SYSTEM_PROMPT
from .models import (
    ExecuteRequest,
    ExecuteResponse,
    TokenEstimate,
)


# API response cap. Full output is always stored in the log DB.
OUTPUT_MAX_CHARS = 8000


def estimate_prompt_tokens(prompt: str) -> int:
    return max(1, len(prompt) // 4)


def find_skill_path(skill_paths: dict[str, str], skill_id: str) -> str | None:
    return skill_paths.get(skill_id)


def _verify_integrity(path: Path, expected_sha256: str | None) -> None:
    """Refuse a skill file whose bytes changed since indexing."""
    if not expected_sha256:
        return
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected_sha256:
        raise ValueError(
            f"skill integrity check failed for {path.name}: "
            f"expected {expected_sha256[:12]}, got {actual[:12]}. Re-run `agent-foundry index`."
        )


def build_messages(skill_id: str, prompt: str, skill_paths: dict[str, str],
                   fallback_prompt: str | None = None,
                   expected_sha256: str | None = None) -> tuple[list[dict], bool]:
    """Return (messages, is_fallback). Raises ValueError on integrity mismatch."""
    path = find_skill_path(skill_paths, skill_id)
    if skill_id == GENERIC_REASONING_ID or not path or path.startswith("__virtual__:"):
        system = fallback_prompt or GENERIC_REASONING_SYSTEM_PROMPT
        return ([{"role": "system", "content": system},
                 {"role": "user", "content": prompt}], True)

    file_path = Path(path)
    _verify_integrity(file_path, expected_sha256)
    try:
        system = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return ([{"role": "system", "content": f"(failed to load skill: {e})"},
                 {"role": "user", "content": prompt}], False)
    return ([{"role": "system", "content": system},
             {"role": "user", "content": prompt}], False)


def complete(messages: list[dict], *, model: str, timeout_seconds: int = 120,
             max_tokens: int = 0, retries: int = 2) -> tuple[str, int, float]:
    """Run one completion. Returns (full_text, tokens_used, cost_usd)."""
    import litellm

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "timeout": timeout_seconds,
        "num_retries": retries,
    }
    if max_tokens and max_tokens > 0:
        kwargs["max_tokens"] = max_tokens

    resp = litellm.completion(**kwargs)

    try:
        text = resp.choices[0].message.content or ""
    except Exception:
        text = ""
    if not isinstance(text, str):
        text = str(text)

    usage: dict[str, Any] = {}
    try:
        usage = resp.usage.model_dump() if hasattr(resp.usage, "model_dump") else dict(resp.usage or {})
    except Exception:
        pass
    tokens_used = int(usage.get("total_tokens") or 0)
    if tokens_used == 0:
        pt = int(usage.get("prompt_tokens") or 0)
        ct = int(usage.get("completion_tokens") or 0)
        tokens_used = pt + ct

    cost_usd = 0.0
    try:
        cost_usd = float(litellm.completion_cost(completion_response=resp) or 0.0)
    except Exception:
        pass
    return text, tokens_used, cost_usd


def execute(request: ExecuteRequest, *, model: str, skill_paths: dict[str, str],
            db_path: Path | None = None, planner_score: float | None = None,
            fallback_prompt: str | None = None,
            skill_hashes: dict[str, str] | None = None,
            timeout_seconds: int = 120, max_tokens: int = 0,
            retries: int = 2) -> ExecuteResponse:
    """Run the skill via LiteLLM. Optionally log to SQLite."""
    t0 = time.time()
    was_fallback = False
    try:
        was_fallback = request.skill_id == GENERIC_REASONING_ID
        messages, was_fallback = build_messages(
            request.skill_id, request.prompt, skill_paths,
            fallback_prompt=fallback_prompt,
            expected_sha256=(skill_hashes or {}).get(request.skill_id),
        )
        text, tokens_used, cost_usd = complete(
            messages, model=model, timeout_seconds=timeout_seconds,
            max_tokens=max_tokens, retries=retries,
        )
    except Exception as exc:
        err = str(exc)
        dur = time.time() - t0
        if db_path is not None:
            from .logging_db import log_execution
            log_execution(db_path, skill_id=request.skill_id, prompt=request.prompt,
                          output="", tokens_used=0, duration_seconds=dur,
                          success=False, error=err[:1000],
                          planner_score=planner_score, was_fallback=was_fallback)
        return ExecuteResponse(
            skill_id=request.skill_id,
            output="",
            tokens_used=0,
            duration_seconds=dur,
            success=False,
            error=err[:1000],
            was_fallback=was_fallback,
        )

    dur = time.time() - t0
    if db_path is not None:
        from .logging_db import log_execution
        log_execution(db_path, skill_id=request.skill_id, prompt=request.prompt,
                      output=text, tokens_used=tokens_used,
                      duration_seconds=dur, success=True,
                      planner_score=planner_score, was_fallback=was_fallback)

    return ExecuteResponse(
        skill_id=request.skill_id,
        output=text[:OUTPUT_MAX_CHARS],
        tokens_used=tokens_used,
        duration_seconds=dur,
        success=True,
        was_fallback=was_fallback,
        cost_usd=cost_usd,
    )
