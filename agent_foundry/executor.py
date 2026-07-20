"""Executor: run a skill (prompt + body) via LiteLLM."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .indexer import GENERIC_REASONING_ID, GENERIC_REASONING_SYSTEM_PROMPT
from .models import (
    ExecuteRequest,
    ExecuteResponse,
    TokenEstimate,
)


# Prompt size threshold for extracting from the LLM response.
OUTPUT_MAX_CHARS = 8000


def estimate_prompt_tokens(prompt: str) -> int:
    return max(1, len(prompt) // 4)


def find_skill_path(skill_paths: dict[str, str], skill_id: str) -> str | None:
    return skill_paths.get(skill_id)


def build_messages(skill_id: str, prompt: str, skill_paths: dict[str, str],
                   fallback_prompt: str | None = None) -> tuple[list[dict], bool]:
    """Return (messages, is_fallback)."""
    path = find_skill_path(skill_paths, skill_id)
    if skill_id == GENERIC_REASONING_ID or not path or path.startswith("__virtual__:"):
        system = fallback_prompt or GENERIC_REASONING_SYSTEM_PROMPT
        return ([{"role": "system", "content": system},
                 {"role": "user", "content": prompt}], True)

    # Read SKILL.md content as system prompt
    file_path = Path(path)
    try:
        system = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return ([{"role": "system", "content": f"(failed to load skill: {e})"},
                 {"role": "user", "content": prompt}], False)
    return ([{"role": "system", "content": system},
             {"role": "user", "content": prompt}], False)


def execute(request: ExecuteRequest, *, model: str, skill_paths: dict[str, str],
            db_path: Path | None = None, planner_score: float | None = None,
            fallback_prompt: str | None = None) -> ExecuteResponse:
    """Run the skill via LiteLLM. Optionally log to SQLite."""
    import litellm

    messages, was_fallback = build_messages(request.skill_id, request.prompt, skill_paths,
                                            fallback_prompt=fallback_prompt)

    t0 = time.time()
    try:
        resp = litellm.completion(
            model=model,
            messages=messages,
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
    # Extract text
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
        # Fallback: sum prompt + completion tokens if present
        pt = int(usage.get("prompt_tokens") or 0)
        ct = int(usage.get("completion_tokens") or 0)
        tokens_used = pt + ct

    truncated = text[:OUTPUT_MAX_CHARS]

    if db_path is not None:
        from .logging_db import log_execution
        log_execution(db_path, skill_id=request.skill_id, prompt=request.prompt,
                      output=truncated, tokens_used=tokens_used,
                      duration_seconds=dur, success=True,
                      planner_score=planner_score, was_fallback=was_fallback)

    return ExecuteResponse(
        skill_id=request.skill_id,
        output=truncated,
        tokens_used=tokens_used,
        duration_seconds=dur,
        success=True,
        was_fallback=was_fallback,
    )
