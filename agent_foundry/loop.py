"""Loop: plan -> budget guard -> execute -> return."""
from __future__ import annotations

from typing import Any

from .config import Config
from pathlib import Path

from .executor import estimate_prompt_tokens, execute
from .indexer import GENERIC_REASONING_ID, get_index_cached
from .models import (
    LoopRequest,
    LoopResponse,
    PlanRequest,
    PlanResult,
    TokenEstimate,
)
from .planner import rank_skills


def _estimate_total(req: LoopRequest, idx, chosen_skill_id: str) -> TokenEstimate:
    """Estimate total tokens for chosen skill + prompt."""
    # Pull chosen skill cost
    skill = next((s for s in idx.skills if s.id == chosen_skill_id), None)
    if skill is None:
        # Fallback default
        return TokenEstimate(input=500, output=1500)
    in_tok = int(skill.estimated_token_cost.get("input", 0)) + estimate_prompt_tokens(req.prompt)
    out_tok = int(skill.estimated_token_cost.get("output", 0))
    return TokenEstimate(input=in_tok, output=out_tok)


def _pick_skill(prompt: str, idx, cfg: Config) -> tuple[str | None, list[PlanResult], float | None]:
    """Pick the best skill. Return (skill_id, plan, planner_score).
    If nothing matches, use the generic-reasoning fallback."""
    ranked = rank_skills(prompt, idx, cfg.planner)
    if ranked:
        top = ranked[0]
        return (top.skill_id, ranked, top.score)
    return (GENERIC_REASONING_ID, [], None)


def run_loop(req: LoopRequest, *, cfg: Config, db_path, model_override: str | None = None) -> LoopResponse:
    idx = get_index_cached(Path(cfg.core.index_path).expanduser(),
                            ttl_seconds=cfg.core.index_cache_ttl_seconds)
    if idx is None:
        return LoopResponse(success=False,
                            error="No skill index. Run `agent-foundry init && agent-foundry index`.",
                            was_fallback=False)

    skill_id, plan_list, planner_score = _pick_skill(req.prompt, idx, cfg)
    if skill_id is None:
        return LoopResponse(plan=plan_list, success=False,
                            error="No skill could be selected.",
                            was_fallback=False)

    was_fallback = (skill_id == GENERIC_REASONING_ID)
    # If fallback was chosen, surface it in the plan list
    if was_fallback:
        skill = next(s for s in idx.skills if s.id == skill_id)
        plan_list = [PlanResult(
            skill_id=skill_id,
            name=skill.name,
            description=skill.description,
            score=0.0,
            matched_patterns=[],
            estimated_cost=TokenEstimate(
                input=int(skill.estimated_token_cost.get("input", 0)),
                output=int(skill.estimated_token_cost.get("output", 0)),
            ),
            location=skill.location,
        )]

    # Budget guard
    estimate = _estimate_total(req, idx, skill_id)
    budget = req.budget if req.budget is not None else cfg.core.token_budget
    if estimate.total > budget and not req.force:
        return LoopResponse(
            plan=plan_list,
            skill_id=skill_id,
            requires_confirmation=True,
            estimated_cost=estimate,
            was_fallback=was_fallback,
        )

    # Execute (do not log here — executor logs at /execute-level granularity;
    # when invoked via /loop we also log with planner_score + was_fallback)
    model = model_override or cfg.core.default_llm
    fallback_prompt = cfg.fallback_system_prompt

    # We need planner_score + was_fallback to be logged, so we call the
    # executor's lower-level path here rather than /execute. Use the same
    # underlying logic but with logging.
    from .executor import build_messages
    import time
    import litellm

    messages, _ = build_messages(skill_id, req.prompt, idx.skill_paths, fallback_prompt=fallback_prompt)
    t0 = time.time()
    try:
        resp = litellm.completion(model=model, messages=messages)
    except Exception as exc:
        dur = time.time() - t0
        from .logging_db import log_execution
        log_execution(db_path, skill_id=skill_id, prompt=req.prompt, output="",
                      tokens_used=0, duration_seconds=dur, success=False,
                      error=str(exc)[:1000], planner_score=planner_score,
                      was_fallback=was_fallback)
        return LoopResponse(plan=plan_list, skill_id=skill_id, success=False,
                            error=str(exc)[:1000], duration_seconds=dur,
                            was_fallback=was_fallback)

    dur = time.time() - t0
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

    truncated = text[:8000]
    from .logging_db import log_execution
    log_execution(db_path, skill_id=skill_id, prompt=req.prompt, output=truncated,
                  tokens_used=tokens_used, duration_seconds=dur, success=True,
                  planner_score=planner_score, was_fallback=was_fallback)

    return LoopResponse(
        plan=plan_list,
        skill_id=skill_id,
        output=truncated,
        tokens_used=tokens_used,
        duration_seconds=dur,
        success=True,
        was_fallback=was_fallback,
    )
