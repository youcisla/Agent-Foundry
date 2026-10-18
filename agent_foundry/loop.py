"""Loop: plan -> budget guard -> execute -> return."""
from __future__ import annotations

import time
from pathlib import Path

from .config import Config

from .executor import (
    _model_chain,
    build_messages,
    complete_chain,
    estimate_prompt_tokens,
    policy_check,
    record_observation,
)
from .indexer import GENERIC_REASONING_ID, get_index_cached
from .models import (
    LoopRequest,
    LoopResumeRequest,
    LoopResponse,
    PlanRequest,
    PlanResult,
    TokenEstimate,
)
from .planner import rank_skills


def _attest_error(cfg: Config) -> str | None:
    """Return an error string when strict attestation fails."""
    if not cfg.core.attest_strict:
        return None
    from .attest import MANIFEST_NAME, verify_manifest
    manifest = Path(cfg.core.skills_dir).expanduser() / MANIFEST_NAME
    result = verify_manifest(manifest, Path(cfg.core.attest_key_path).expanduser())
    if result.ok:
        return None
    detail = (result.errors or result.mismatched or result.missing)[:3]
    return f"skill attestation failed: {detail}"


def _policy_block(text: str, direction: str, cfg: Config, db_path):
    """Return a blocking decision in enforce mode, else None."""
    decision = policy_check(text, direction, cfg.core.policy_mode, db_path)
    if decision is None or cfg.core.policy_mode != "enforce":
        return None
    if decision.decision in ("deny", "confirm"):
        return decision
    return None


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


def _pick_skill(prompt: str, idx, cfg: Config,
                weights: dict[str, float] | None = None) -> tuple[str | None, list[PlanResult], float | None]:
    """Pick the best skill. Return (skill_id, plan, planner_score).
    If nothing matches, use the generic-reasoning fallback."""
    rerank = cfg.core.default_llm if cfg.planner.rerank_enabled else None
    ranked = rank_skills(prompt, idx, cfg.planner, weights=weights, rerank_model=rerank)
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

    attest_err = _attest_error(cfg)
    if attest_err:
        return LoopResponse(success=False, error=attest_err, was_fallback=False)

    inbound = _policy_block(req.prompt, "inbound", cfg, db_path)
    if inbound is not None:
        return LoopResponse(success=False,
                            error=f"policy {inbound.decision}: {inbound.rule_id}",
                            requires_confirmation=inbound.decision == "confirm",
                            was_fallback=False)

    from .logging_db import get_skill_weights

    skill_id, plan_list, planner_score = _pick_skill(
        req.prompt, idx, cfg, weights=get_skill_weights(db_path))
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

    # Execute via the shared completion path so timeout/retries/limits apply.
    from .logging_db import log_execution

    model = model_override or cfg.core.default_llm
    messages_chain = _model_chain(model, cfg.core.fallback_llms)
    fallback_prompt = cfg.fallback_system_prompt
    skill_hash = next((s.sha256 for s in idx.skills if s.id == skill_id), "")
    from .logging_db import create_loop_session, update_loop_session
    session_id = create_loop_session(db_path, req.prompt, skill_id)

    t0 = time.time()
    try:
        messages, _ = build_messages(skill_id, req.prompt, idx.skill_paths,
                                     fallback_prompt=fallback_prompt,
                                     expected_sha256=skill_hash)
        text, tokens_used, cost_usd, _ = complete_chain(
            messages, models=messages_chain,
            timeout_seconds=cfg.core.executor_timeout_seconds,
            max_tokens=cfg.core.executor_max_tokens,
            retries=cfg.core.executor_retries,
        )
    except Exception as exc:
        dur = time.time() - t0
        log_execution(db_path, skill_id=skill_id, prompt=req.prompt, output="",
                      tokens_used=0, duration_seconds=dur, success=False,
                      error=str(exc)[:1000], planner_score=planner_score,
                      was_fallback=was_fallback)
        update_loop_session(db_path, session_id, status="failed", output="")
        record_observation(db_path, None, skill_id, req.prompt, "error",
                           latency_ms=int(dur * 1000), plan=plan_list)
        return LoopResponse(plan=plan_list, skill_id=skill_id, success=False,
                            error=str(exc)[:1000], duration_seconds=dur,
                            was_fallback=was_fallback, session_id=session_id)

    dur = time.time() - t0
    truncated = text[:8000]
    outbound = _policy_block(text, "outbound", cfg, db_path)
    if outbound is not None:
        err = f"policy {outbound.decision}: {outbound.rule_id}"
        update_loop_session(db_path, session_id, status="failed", output="")
        log_execution(db_path, skill_id=skill_id, prompt=req.prompt, output="",
                      tokens_used=tokens_used, duration_seconds=dur,
                      success=False, error=err, planner_score=planner_score,
                      was_fallback=was_fallback, cost_usd=cost_usd)
        record_observation(db_path, None, skill_id, req.prompt, "error",
                           cost_usd=cost_usd, latency_ms=int(dur * 1000),
                           plan=plan_list)
        return LoopResponse(plan=plan_list, skill_id=skill_id, success=False,
                            error=err, tokens_used=tokens_used,
                            duration_seconds=dur, was_fallback=was_fallback,
                            cost_usd=cost_usd, session_id=session_id)

    update_loop_session(db_path, session_id, status="completed", output=text,
                        increment_turn=True)

    judge_payload = None
    judged_flag = False
    if getattr(req, "judge", False):
        from .judge import judge_output
        judge_payload = judge_output(
            task=req.prompt,
            output=truncated,
            model=model,
            skill_paths=idx.skill_paths,
            fallback_prompt=fallback_prompt,
        )
        judged_flag = judge_payload is not None

    log_execution(
        db_path,
        skill_id=skill_id,
        prompt=req.prompt,
        output=truncated,
        tokens_used=tokens_used,
        duration_seconds=dur,
        success=True,
        planner_score=planner_score,
        was_fallback=was_fallback,
        judge_corr=judge_payload.get("correctness") if judge_payload else None,
        judge_slop=judge_payload.get("slop") if judge_payload else None,
        judge_scope=judge_payload.get("scope") if judge_payload else None,
        judge_verdict=judge_payload.get("verdict") if judge_payload else None,
        cost_usd=cost_usd,
    )
    record_observation(db_path, None, skill_id, req.prompt, "success",
                       judge=judge_payload, cost_usd=cost_usd,
                       latency_ms=int(dur * 1000), plan=plan_list)

    return LoopResponse(
        plan=plan_list,
        skill_id=skill_id,
        output=truncated,
        tokens_used=tokens_used,
        duration_seconds=dur,
        success=True,
        was_fallback=was_fallback,
        judge_score=judge_payload,
        judged=judged_flag,
        cost_usd=cost_usd,
        session_id=session_id,
    )


def resume_loop(req: LoopResumeRequest, *, cfg: Config, db_path,
                model_override: str | None = None) -> LoopResponse:
    """Continue an existing loop session with a follow-up prompt."""
    from .logging_db import get_loop_session, log_execution, update_loop_session

    session = get_loop_session(db_path, req.session_id)
    if session is None:
        return LoopResponse(success=False,
                            error=f"loop session {req.session_id} not found")

    idx = get_index_cached(Path(cfg.core.index_path).expanduser(),
                            ttl_seconds=cfg.core.index_cache_ttl_seconds)
    if idx is None:
        return LoopResponse(success=False,
                            error="No skill index. Run `agent-foundry init && agent-foundry index`.")

    attest_err = _attest_error(cfg)
    if attest_err:
        return LoopResponse(success=False, error=attest_err)
    inbound = _policy_block(req.prompt, "inbound", cfg, db_path)
    if inbound is not None:
        return LoopResponse(success=False,
                            error=f"policy {inbound.decision}: {inbound.rule_id}",
                            requires_confirmation=inbound.decision == "confirm",
                            session_id=req.session_id)

    skill_id = session["skill_id"]
    skill_hash = next((s.sha256 for s in idx.skills if s.id == skill_id), "")
    model = model_override or cfg.core.default_llm
    messages_chain = _model_chain(model, cfg.core.fallback_llms)
    was_fallback = skill_id == GENERIC_REASONING_ID

    t0 = time.time()
    try:
        messages, _ = build_messages(skill_id, session["prompt"], idx.skill_paths,
                                     fallback_prompt=cfg.fallback_system_prompt,
                                     expected_sha256=skill_hash)
        if session.get("output"):
            messages.append({"role": "assistant", "content": session["output"]})
        messages.append({"role": "user", "content": req.prompt})
        text, tokens_used, cost_usd, _ = complete_chain(
            messages, models=messages_chain,
            timeout_seconds=cfg.core.executor_timeout_seconds,
            max_tokens=cfg.core.executor_max_tokens,
            retries=cfg.core.executor_retries,
        )
    except Exception as exc:
        dur = time.time() - t0
        log_execution(db_path, skill_id=skill_id, prompt=req.prompt, output="",
                      tokens_used=0, duration_seconds=dur, success=False,
                      error=str(exc)[:1000], was_fallback=was_fallback)
        record_observation(db_path, None, skill_id, req.prompt, "error",
                           latency_ms=int(dur * 1000))
        return LoopResponse(skill_id=skill_id, success=False, error=str(exc)[:1000],
                            duration_seconds=dur, was_fallback=was_fallback,
                            session_id=req.session_id)

    dur = time.time() - t0
    truncated = text[:8000]
    outbound = _policy_block(text, "outbound", cfg, db_path)
    if outbound is not None:
        err = f"policy {outbound.decision}: {outbound.rule_id}"
        update_loop_session(db_path, req.session_id, status="failed", output="")
        log_execution(db_path, skill_id=skill_id, prompt=req.prompt, output="",
                      tokens_used=tokens_used, duration_seconds=dur, success=False,
                      error=err, was_fallback=was_fallback, cost_usd=cost_usd)
        record_observation(db_path, None, skill_id, req.prompt, "error",
                           cost_usd=cost_usd, latency_ms=int(dur * 1000))
        return LoopResponse(skill_id=skill_id, success=False, error=err,
                            tokens_used=tokens_used, duration_seconds=dur,
                            was_fallback=was_fallback, cost_usd=cost_usd,
                            session_id=req.session_id)

    update_loop_session(db_path, req.session_id, status="completed", output=text,
                        increment_turn=True)
    log_execution(db_path, skill_id=skill_id, prompt=req.prompt, output=truncated,
                  tokens_used=tokens_used, duration_seconds=dur, success=True,
                  was_fallback=was_fallback, cost_usd=cost_usd)
    record_observation(db_path, None, skill_id, req.prompt, "success",
                       cost_usd=cost_usd, latency_ms=int(dur * 1000))
    return LoopResponse(skill_id=skill_id, output=truncated,
                        tokens_used=tokens_used, duration_seconds=dur,
                        success=True, was_fallback=was_fallback,
                        cost_usd=cost_usd, session_id=req.session_id)
