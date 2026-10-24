"""Loop: plan -> budget guard -> execute -> return."""
from __future__ import annotations

import time
import uuid
from pathlib import Path

from .config import Config
from .executor import (
    _model_chain,
    _unpack_chain_result,
    build_messages,
    complete_chain,
    estimate_prompt_tokens,
    policy_check,
    record_observation,
)
from .indexer import GENERIC_REASONING_ID, get_index_cached
from .judge import JudgeResult, judge_output
from .models import (
    LoopRequest,
    LoopResumeRequest,
    LoopResponse,
    PlanRequest,
    PlanResult,
    TokenEstimate,
)
from .planner import rank_skills
from .replay import request_metadata, trace_digest
from .timing import PhaseTimer


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


def _run_options(cfg: Config, *, queue_depth: int = 0,
                 session_id: int | None = None) -> dict:
    return {
        "perf_cache_enabled": cfg.core.perf_cache_enabled,
        "perf_cache_ttl_seconds": cfg.core.perf_cache_ttl_seconds,
        "adaptive_retries": cfg.core.adaptive_retries,
        "adaptive_retries_min_samples": cfg.core.adaptive_retries_min_samples,
        "adaptive_retries_min_queue_depth": cfg.core.adaptive_retries_min_queue_depth,
        "max_attempts": cfg.core.max_attempts,
        "spill_enabled": cfg.core.spill_enabled,
        "spill_root": cfg.core.spill_root or None,
        "output_preview_chars": cfg.core.output_preview_chars,
        "queue_depth": queue_depth,
        "session_id": session_id,
    }


def _estimate_total(req, idx, chosen_skill_id: str, cfg: Config | None = None,
                    db_path=None, queue_depth: int = 0) -> TokenEstimate:
    """Estimate total tokens. Measured completion tokens win when enabled."""
    skill = next((s for s in idx.skills if s.id == chosen_skill_id), None)
    in_tok = int(skill.estimated_token_cost.get("input", 0)) if skill else 500
    out_tok = int(skill.estimated_token_cost.get("output", 0)) if skill else 1500
    in_tok += estimate_prompt_tokens(req.prompt)
    if cfg is not None and cfg.core.perf_cache_enabled and db_path is not None:
        try:
            from .perf_cache import estimate as perf_estimate
            measured = perf_estimate(
                db_path, model=cfg.core.default_llm, skill_id=chosen_skill_id,
                queue_depth=queue_depth,
                ttl_seconds=cfg.core.perf_cache_ttl_seconds,
                enabled=True,
            )
            if measured and measured.get("avg_completion_tokens"):
                out_tok = max(1, int(round(measured["avg_completion_tokens"])))
        except Exception:
            pass
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


def _history_messages(history: list) -> list[dict]:
    messages: list[dict] = []
    for turn in history:
        if not isinstance(turn, dict):
            continue
        user = turn.get("user")
        assistant = turn.get("assistant")
        if user:
            messages.append({"role": "user", "content": str(user)})
        if assistant:
            messages.append({"role": "assistant", "content": str(assistant)})
    return messages


def _compact_history(history: list, max_tokens: int,
                     keep_turns: int) -> tuple[list, int, int]:
    """Drop oldest turns until the estimate fits. Newest `keep_turns` stay."""
    if max_tokens <= 0 or not history:
        return list(history), 0, 0

    def tokens(items: list) -> int:
        return sum(
            estimate_prompt_tokens(str(t.get("user", "")))
            + estimate_prompt_tokens(str(t.get("assistant", "")))
            for t in items
        )

    compacted = list(history)
    dropped_turns = 0
    dropped_tokens = 0
    while len(compacted) > max(0, keep_turns) and tokens(compacted) > max_tokens:
        removed = compacted.pop(0)
        dropped_turns += 1
        dropped_tokens += (
            estimate_prompt_tokens(str(removed.get("user", "")))
            + estimate_prompt_tokens(str(removed.get("assistant", "")))
        )
    return compacted, dropped_turns, dropped_tokens


def _judge_avg(scores: dict | None) -> float | None:
    if not scores:
        return None
    axes = [float(scores[k]) for k in ("correctness", "slop", "scope")
            if isinstance(scores.get(k), (int, float))]
    return sum(axes) / len(axes) if axes else None


def _log_loop(db_path, *, req, skill_id, text, tokens_used, dur, success,
              error, planner_score, was_fallback, cfg, judged: JudgeResult | None,
              digest, phases, attempts, repairs, output_ref, failure_kind,
              usage, meta, config) -> None:
    if db_path is None:
        return
    from .logging_db import log_execution
    scores = judged.scores if judged and judged.ok else {}
    prompt_tokens = int((usage or {}).get("prompt_tokens") or 0)
    completion_tokens = int((usage or {}).get("completion_tokens") or 0)
    cached = 0
    details = (usage or {}).get("prompt_tokens_details") or {}
    if isinstance(details, dict):
        cached = int(details.get("cached_tokens") or 0)
    log_execution(
        db_path, skill_id=skill_id, prompt=req.prompt, output=text,
        tokens_used=tokens_used, duration_seconds=dur, success=success,
        error=error, planner_score=planner_score, was_fallback=was_fallback,
        judge_corr=scores.get("correctness") if scores else None,
        judge_slop=scores.get("slop") if scores else None,
        judge_scope=scores.get("scope") if scores else None,
        judge_verdict=scores.get("verdict") if scores else None,
        cost_usd=0.0, trace_digest=digest, phases=phases, repairs=repairs,
        output_ref=output_ref, judge_status=judged.status if judged else None,
        failure_kind=failure_kind, prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens, cached_tokens=cached,
        request_meta=meta, run_config=config,
    )


def run_loop(req: LoopRequest, *, cfg: Config, db_path, model_override: str | None = None,
             queue_depth: int = 0) -> LoopResponse:
    timer = PhaseTimer()
    t0 = time.time()

    with timer.phase("index"):
        idx = get_index_cached(Path(cfg.core.index_path).expanduser(),
                               ttl_seconds=cfg.core.index_cache_ttl_seconds)
    if idx is None:
        return LoopResponse(success=False,
                            error="No skill index. Run `agent-foundry init && agent-foundry index`.",
                            was_fallback=False, phases=timer.phases,
                            failure_kind="internal")

    attest_err = _attest_error(cfg)
    if attest_err:
        return LoopResponse(success=False, error=attest_err, was_fallback=False,
                            phases=timer.phases, failure_kind="attest")

    inbound = _policy_block(req.prompt, "inbound", cfg, db_path)
    if inbound is not None:
        return LoopResponse(success=False,
                            error=f"policy {inbound.decision}: {inbound.rule_id}",
                            requires_confirmation=inbound.decision == "confirm",
                            was_fallback=False, phases=timer.phases,
                            failure_kind="policy")

    from .logging_db import get_skill_weights

    with timer.phase("plan"):
        skill_id, plan_list, planner_score = _pick_skill(
            req.prompt, idx, cfg, weights=get_skill_weights(db_path))
    if skill_id is None:
        return LoopResponse(plan=plan_list, success=False,
                            error="No skill could be selected.",
                            was_fallback=False, phases=timer.phases,
                            failure_kind="internal")

    was_fallback = (skill_id == GENERIC_REASONING_ID)
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

    with timer.phase("budget"):
        estimate = _estimate_total(req, idx, skill_id, cfg, db_path, queue_depth)
        budget = req.budget if req.budget is not None else cfg.core.token_budget
        per_call = cfg.core.per_call_token_budget
        over = estimate.total > budget or (per_call > 0 and estimate.total > per_call)
    if over and not req.force:
        return LoopResponse(
            plan=plan_list,
            skill_id=skill_id,
            requires_confirmation=True,
            estimated_cost=estimate,
            was_fallback=was_fallback,
            phases=timer.phases,
            failure_kind="budget",
        )

    from .logging_db import create_loop_session, update_loop_session

    model = model_override or cfg.core.default_llm
    messages_chain = _model_chain(model, cfg.core.fallback_llms)
    fallback_prompt = cfg.fallback_system_prompt
    skill_hash = next((s.sha256 for s in idx.skills if s.id == skill_id), "")
    session_id = create_loop_session(db_path, req.prompt, skill_id, history=[])
    attempt_id = None
    if db_path is not None:
        from .logging_db import start_attempt
        import hashlib
        attempt_id = start_attempt(
            db_path, skill_id=skill_id, model=messages_chain[0],
            dedupe_hash=hashlib.sha256(
                f"{skill_id}|{req.prompt}|{messages_chain[0]}".encode("utf-8")
            ).hexdigest(),
            session_id=session_id,
        )

    history: list = []
    text = ""
    tokens_used = 0
    cost_usd = 0.0
    usage: dict = {}
    attempts = 1
    repairs = 0
    output_ref = None
    judged: JudgeResult | None = None
    failure_kind: str | None = None
    digest = ""
    meta: dict | None = None
    config: dict | None = None

    try:
        with timer.phase("execute"):
            messages, _ = build_messages(
                skill_id, req.prompt, idx.skill_paths,
                fallback_prompt=fallback_prompt, expected_sha256=skill_hash,
                model=messages_chain[0],
            )
            messages = messages[:-1] + _history_messages(history) + [messages[-1]]
            max_models = None
            if cfg.core.adaptive_retries and db_path is not None \
                    and queue_depth >= cfg.core.adaptive_retries_min_queue_depth:
                from .retry_policy import allocate_attempts, success_rate
                rate = success_rate(
                    db_path, skill_id=skill_id, model=messages_chain[0],
                    min_samples=cfg.core.adaptive_retries_min_samples,
                )
                max_models = allocate_attempts(
                    rate, max_attempts=cfg.core.max_attempts,
                )
                attempts = max_models
            result = complete_chain(
                messages, models=messages_chain,
                timeout_seconds=cfg.core.executor_timeout_seconds,
                max_tokens=cfg.core.executor_max_tokens,
                retries=cfg.core.executor_retries,
                seed=req.seed, temperature=req.temperature,
                max_models=max_models,
            )
            text, tokens_used, cost_usd, used_model, attempts, usage = _unpack_chain_result(
                result, messages_chain[0],
            )
    except Exception as exc:
        dur = time.time() - t0
        update_loop_session(db_path, session_id, status="failed", output="")
        if attempt_id is not None:
            from .logging_db import finish_attempt
            finish_attempt(db_path, attempt_id, "failed")
        _log_loop(db_path, req=req, skill_id=skill_id, text="", tokens_used=0,
                  dur=dur, success=False, error=str(exc)[:1000],
                  planner_score=planner_score, was_fallback=was_fallback, cfg=cfg,
                  judged=None, digest="", phases=timer.phases, attempts=attempts,
                  repairs=0, output_ref=None, failure_kind="provider",
                  usage={}, meta=None, config=None)
        record_observation(db_path, None, skill_id, req.prompt, "error",
                           latency_ms=int(dur * 1000), plan=plan_list)
        return LoopResponse(plan=plan_list, skill_id=skill_id, success=False,
                            error=str(exc)[:1000], duration_seconds=dur,
                            was_fallback=was_fallback, session_id=session_id,
                            phases=timer.phases, failure_kind="provider")

    dur = time.time() - t0
    outbound = _policy_block(text, "outbound", cfg, db_path)
    if outbound is not None:
        err = f"policy {outbound.decision}: {outbound.rule_id}"
        update_loop_session(db_path, session_id, status="failed", output="")
        if attempt_id is not None:
            from .logging_db import finish_attempt
            finish_attempt(db_path, attempt_id, "failed")
        _log_loop(db_path, req=req, skill_id=skill_id, text="", tokens_used=tokens_used,
                  dur=dur, success=False, error=err, planner_score=planner_score,
                  was_fallback=was_fallback, cfg=cfg, judged=None, digest="",
                  phases=timer.phases, attempts=attempts, repairs=0,
                  output_ref=None, failure_kind="policy", usage=usage,
                  meta=None, config=None)
        record_observation(db_path, None, skill_id, req.prompt, "error",
                           cost_usd=cost_usd, latency_ms=int(dur * 1000),
                           plan=plan_list)
        return LoopResponse(plan=plan_list, skill_id=skill_id, success=False,
                            error=err, tokens_used=tokens_used,
                            duration_seconds=dur, was_fallback=was_fallback,
                            cost_usd=cost_usd, session_id=session_id,
                            phases=timer.phases, failure_kind="policy")

    digest = trace_digest(
        skill_id=skill_id, skill_sha256=skill_hash, models=messages_chain,
        messages=messages, output=text, schema=None, seed=req.seed,
        temperature=req.temperature,
    )
    meta = request_metadata(
        skill_id=skill_id, skill_sha256=skill_hash, models=messages_chain,
        messages=messages, seed=req.seed, temperature=req.temperature,
    )
    from .replay import run_config
    config = run_config(skill_id=skill_id, models=messages_chain,
                        seed=req.seed, temperature=req.temperature, schema=None)

    if cfg.core.spill_enabled:
        try:
            from .spill import default_spill_root, save_output
            output_ref = save_output(
                Path(cfg.core.spill_root) if cfg.core.spill_root else default_spill_root(),
                session_id=session_id, execution_id=uuid.uuid4().hex, text=text,
            )
        except Exception:
            output_ref = None

    truncated = text[: cfg.core.output_preview_chars]
    update_loop_session(db_path, session_id, status="completed", output=text,
                        increment_turn=True,
                        history=history + [{"user": req.prompt, "assistant": text}])
    if attempt_id is not None:
        from .logging_db import finish_attempt
        finish_attempt(db_path, attempt_id, "ok")

    if getattr(req, "judge", False):
        with timer.phase("judge"):
            judged = judge_output(
                task=req.prompt, output=truncated, model=model,
                skill_paths=idx.skill_paths, fallback_prompt=fallback_prompt,
                timeout_seconds=cfg.core.judge_timeout_seconds,
                retries=cfg.core.judge_retries,
            )
            avg = _judge_avg(judged.scores if judged.ok else None)
            escalation = getattr(cfg.core, "judge_escalation_model", "")
            if (judged.ok and escalation and avg is not None
                    and avg < cfg.core.judge_escalation_threshold):
                judged = judge_output(
                    task=req.prompt, output=truncated, model=escalation,
                    skill_paths=idx.skill_paths, fallback_prompt=fallback_prompt,
                    timeout_seconds=cfg.core.judge_timeout_seconds,
                    retries=cfg.core.judge_retries,
                )

    judged_payload = judged.scores if judged and judged.ok else None
    with timer.phase("persist"):
        _log_loop(db_path, req=req, skill_id=skill_id, text=truncated,
                  tokens_used=tokens_used, dur=dur, success=True, error=None,
                  planner_score=planner_score, was_fallback=was_fallback, cfg=cfg,
                  judged=judged, digest=digest, phases=timer.phases,
                  attempts=attempts, repairs=repairs, output_ref=output_ref,
                  failure_kind=None, usage=usage, meta=meta, config=config)
        record_observation(db_path, None, skill_id, req.prompt, "success",
                           judge=judged_payload, cost_usd=cost_usd,
                           latency_ms=int(dur * 1000), plan=plan_list)
        if cfg.core.perf_cache_enabled and db_path is not None:
            try:
                from .perf_cache import record_sample
                record_sample(
                    db_path, model=used_model, skill_id=skill_id,
                    queue_depth=queue_depth, duration_ms=int(dur * 1000),
                    success=True,
                    prompt_tokens=int(usage.get("prompt_tokens") or 0),
                    completion_tokens=int(usage.get("completion_tokens") or 0),
                    cost_usd=cost_usd, enabled=True,
                )
            except Exception:
                pass

    return LoopResponse(
        plan=plan_list,
        skill_id=skill_id,
        output=truncated,
        tokens_used=tokens_used,
        duration_seconds=dur,
        success=True,
        was_fallback=was_fallback,
        judge_score=judged_payload,
        judged=bool(judged and judged.ok),
        judge_status=judged.status if judged else None,
        cost_usd=cost_usd,
        session_id=session_id,
        trace_digest=digest,
        phases=timer.phases,
        attempts=attempts,
        repairs=repairs,
        output_ref=output_ref,
    )


def resume_loop(req: LoopResumeRequest, *, cfg: Config, db_path,
                model_override: str | None = None) -> LoopResponse:
    """Continue an existing loop session with a follow-up prompt."""
    from .logging_db import get_loop_session, update_loop_session

    timer = PhaseTimer()
    session = get_loop_session(db_path, req.session_id)
    if session is None:
        return LoopResponse(success=False,
                            error=f"loop session {req.session_id} not found",
                            phases=timer.phases, failure_kind="internal")

    idx = get_index_cached(Path(cfg.core.index_path).expanduser(),
                           ttl_seconds=cfg.core.index_cache_ttl_seconds)
    if idx is None:
        return LoopResponse(success=False,
                            error="No skill index. Run `agent-foundry init && agent-foundry index`.",
                            phases=timer.phases, failure_kind="internal")

    attest_err = _attest_error(cfg)
    if attest_err:
        return LoopResponse(success=False, error=attest_err,
                            phases=timer.phases, failure_kind="attest")
    inbound = _policy_block(req.prompt, "inbound", cfg, db_path)
    if inbound is not None:
        return LoopResponse(success=False,
                            error=f"policy {inbound.decision}: {inbound.rule_id}",
                            requires_confirmation=inbound.decision == "confirm",
                            session_id=req.session_id, phases=timer.phases,
                            failure_kind="policy")

    skill_id = session["skill_id"]
    skill_hash = next((s.sha256 for s in idx.skills if s.id == skill_id), "")
    model = model_override or cfg.core.default_llm
    messages_chain = _model_chain(model, cfg.core.fallback_llms)
    was_fallback = skill_id == GENERIC_REASONING_ID

    history = session.get("history") or []
    if not history and session.get("output"):
        history = [{"user": session.get("prompt", ""),
                    "assistant": session["output"]}]
    history, compacted_turns, _dropped_tokens = _compact_history(
        history, cfg.core.max_history_tokens, cfg.core.history_keep_turns,
    )

    t0 = time.time()
    try:
        with timer.phase("execute"):
            messages, _ = build_messages(
                skill_id, req.prompt, idx.skill_paths,
                fallback_prompt=cfg.fallback_system_prompt,
                expected_sha256=skill_hash, model=messages_chain[0],
            )
            messages = messages[:-1] + _history_messages(history) + [messages[-1]]
            result = complete_chain(
                messages, models=messages_chain,
                timeout_seconds=cfg.core.executor_timeout_seconds,
                max_tokens=cfg.core.executor_max_tokens,
                retries=cfg.core.executor_retries,
                seed=req.seed, temperature=req.temperature,
            )
            text, tokens_used, cost_usd, used_model, attempts, usage = _unpack_chain_result(
                result, messages_chain[0],
            )
    except Exception as exc:
        dur = time.time() - t0
        update_loop_session(db_path, req.session_id, status="failed", output="")
        _log_loop(db_path, req=req, skill_id=skill_id, text="", tokens_used=0,
                  dur=dur, success=False, error=str(exc)[:1000],
                  planner_score=None, was_fallback=was_fallback, cfg=cfg,
                  judged=None, digest="", phases=timer.phases, attempts=1,
                  repairs=0, output_ref=None, failure_kind="provider",
                  usage={}, meta=None, config=None)
        record_observation(db_path, None, skill_id, req.prompt, "error",
                           latency_ms=int(dur * 1000))
        return LoopResponse(skill_id=skill_id, success=False,
                            error=str(exc)[:1000], duration_seconds=dur,
                            was_fallback=was_fallback,
                            session_id=req.session_id, phases=timer.phases,
                            failure_kind="provider")

    dur = time.time() - t0
    truncated = text[: cfg.core.output_preview_chars]
    outbound = _policy_block(text, "outbound", cfg, db_path)
    if outbound is not None:
        err = f"policy {outbound.decision}: {outbound.rule_id}"
        update_loop_session(db_path, req.session_id, status="failed", output="")
        _log_loop(db_path, req=req, skill_id=skill_id, text="", tokens_used=tokens_used,
                  dur=dur, success=False, error=err, planner_score=None,
                  was_fallback=was_fallback, cfg=cfg, judged=None, digest="",
                  phases=timer.phases, attempts=attempts, repairs=0,
                  output_ref=None, failure_kind="policy", usage=usage,
                  meta=None, config=None)
        record_observation(db_path, None, skill_id, req.prompt, "error",
                           cost_usd=cost_usd, latency_ms=int(dur * 1000))
        return LoopResponse(skill_id=skill_id, success=False, error=err,
                            tokens_used=tokens_used, duration_seconds=dur,
                            was_fallback=was_fallback, cost_usd=cost_usd,
                            session_id=req.session_id, phases=timer.phases,
                            failure_kind="policy")

    digest = trace_digest(
        skill_id=skill_id, skill_sha256=skill_hash, models=messages_chain,
        messages=messages, output=text, schema=None, seed=req.seed,
        temperature=req.temperature,
    )
    meta = request_metadata(
        skill_id=skill_id, skill_sha256=skill_hash, models=messages_chain,
        messages=messages, seed=req.seed, temperature=req.temperature,
    )
    from .replay import run_config
    config = run_config(skill_id=skill_id, models=messages_chain,
                        seed=req.seed, temperature=req.temperature, schema=None)

    output_ref = None
    if cfg.core.spill_enabled:
        try:
            from .spill import default_spill_root, save_output
            output_ref = save_output(
                Path(cfg.core.spill_root) if cfg.core.spill_root else default_spill_root(),
                session_id=req.session_id, execution_id=uuid.uuid4().hex, text=text,
            )
        except Exception:
            output_ref = None

    with timer.phase("persist"):
        update_loop_session(db_path, req.session_id, status="completed", output=text,
                            increment_turn=True,
                            history=history + [{"user": req.prompt, "assistant": text}])
        _log_loop(db_path, req=req, skill_id=skill_id, text=truncated,
                  tokens_used=tokens_used, dur=dur, success=True, error=None,
                  planner_score=None, was_fallback=was_fallback, cfg=cfg,
                  judged=None, digest=digest, phases=timer.phases,
                  attempts=attempts, repairs=0, output_ref=output_ref,
                  failure_kind=None, usage=usage, meta=meta, config=config)
        record_observation(db_path, None, skill_id, req.prompt, "success",
                           cost_usd=cost_usd, latency_ms=int(dur * 1000))
    return LoopResponse(skill_id=skill_id, output=truncated,
                        tokens_used=tokens_used, duration_seconds=dur,
                        success=True, was_fallback=was_fallback,
                        cost_usd=cost_usd, session_id=req.session_id,
                        trace_digest=digest, phases=timer.phases,
                        attempts=attempts, output_ref=output_ref,
                        compacted_turns=compacted_turns)
