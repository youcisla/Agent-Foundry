"""Executor: run a skill (prompt + body) via LiteLLM."""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from pathlib import Path
from typing import Any

from .indexer import GENERIC_REASONING_ID, GENERIC_REASONING_SYSTEM_PROMPT
from .model_catalog import get_model_spec, resolve_model
from .models import ExecuteRequest, ExecuteResponse, TokenEstimate
from .replay import request_metadata, run_config, trace_digest
from .timing import PhaseTimer


def _opt(options: dict | None, key: str, default: Any) -> Any:
    if not options:
        return default
    value = options.get(key, default)
    return default if value is None else value


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
                   expected_sha256: str | None = None,
                   model: str | None = None) -> tuple[list[dict], bool]:
    """Return (messages, is_fallback). Raises ValueError on integrity mismatch.

    When the model does not support a system role, the skill body is folded
    into the user turn instead of being dropped.
    """
    path = find_skill_path(skill_paths, skill_id)
    spec = get_model_spec(model) if model else {}
    supports_system = bool(spec.get("supports_system_prompt", True))
    if skill_id == GENERIC_REASONING_ID or not path or path.startswith("__virtual__:"):
        system = fallback_prompt or GENERIC_REASONING_SYSTEM_PROMPT
        if supports_system:
            return ([{"role": "system", "content": system},
                     {"role": "user", "content": prompt}], True)
        return ([{"role": "user", "content": system + "\n\n" + prompt}], True)

    file_path = Path(path)
    _verify_integrity(file_path, expected_sha256)
    try:
        system = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return ([{"role": "system", "content": f"(failed to load skill: {e})"},
                 {"role": "user", "content": prompt}], False)
    if supports_system:
        return ([{"role": "system", "content": system},
                 {"role": "user", "content": prompt}], False)
    return ([{"role": "user", "content": system + "\n\n" + prompt}], False)


def complete(messages: list[dict], *, model: str, timeout_seconds: int = 120,
             max_tokens: int = 0, retries: int = 2,
             seed: int | None = None,
             temperature: float | None = None) -> tuple[str, int, float, dict]:
    """Run one completion. Returns (full_text, tokens, cost_usd, usage)."""
    import litellm

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "timeout": timeout_seconds,
        "num_retries": retries,
    }
    if max_tokens and max_tokens > 0:
        kwargs["max_tokens"] = max_tokens
    if seed is not None:
        kwargs["seed"] = seed
    if temperature is not None:
        kwargs["temperature"] = temperature

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
    return text, tokens_used, cost_usd, usage


def _extract_json(text: str) -> Any:
    """Parse a JSON value, tolerating fences and surrounding prose."""
    s = text.strip()
    if s.startswith("```"):
        lines = s.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        s = "\n".join(lines).strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    for opener, closer in (("{", "}"), ("[", "]")):
        start, end = s.find(opener), s.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(s[start:end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError("response is not valid JSON")


def _matches_type(value: Any, name: str) -> bool:
    checks = {
        "object": lambda v: isinstance(v, dict),
        "array": lambda v: isinstance(v, list),
        "string": lambda v: isinstance(v, str),
        "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
        "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
        "boolean": lambda v: isinstance(v, bool),
        "null": lambda v: v is None,
    }
    check = checks.get(name)
    return check(value) if check else True


def schema_errors(value: Any, schema: dict, path: str = "$") -> list[str]:
    """Minimal JSON Schema check: type, required, properties, items."""
    if not isinstance(schema, dict):
        return []
    errors: list[str] = []
    expected = schema.get("type")
    if expected:
        names = expected if isinstance(expected, list) else [expected]
        if not any(_matches_type(value, n) for n in names):
            return [f"{path}: expected {expected}, got {type(value).__name__}"]
    if isinstance(value, dict):
        for key in schema.get("required") or []:
            if key not in value:
                errors.append(f"{path}: missing required {key!r}")
        for key, sub in (schema.get("properties") or {}).items():
            if key in value:
                errors.extend(schema_errors(value[key], sub, f"{path}.{key}"))
    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        for i, item in enumerate(value):
            errors.extend(schema_errors(item, schema["items"], f"{path}[{i}]"))
    return errors


def _with_schema(messages: list[dict], schema: dict) -> list[dict]:
    """Append the schema contract to the final user turn."""
    instruction = (
        "Return only one JSON value that satisfies this JSON Schema. "
        "No prose and no markdown fences.\n"
        + json.dumps(schema, separators=(",", ":"))
    )
    out = list(messages)
    last = dict(out[-1])
    last["content"] = str(last.get("content", "")) + "\n\n" + instruction
    out[-1] = last
    return out


def _model_chain(model: str, fallbacks: list[str] | None) -> list[str]:
    chain: list[str] = []
    for name in [model, *(fallbacks or [])]:
        resolved = resolve_model(name)
        if resolved and resolved not in chain:
            chain.append(resolved)
    return chain or [resolve_model(model)]


def _auth_error(exc: Exception) -> bool:
    code = getattr(exc, "status_code", None)
    return code in (401, 403)


def _preflight(messages: list[dict], model: str, max_tokens: int) -> None:
    """Reject an over-context request before spending a call."""
    spec = get_model_spec(model)
    window = int(spec.get("context_window") or 0)
    if window <= 0:
        return
    prompt_tokens = sum(estimate_prompt_tokens(str(m.get("content", ""))) for m in messages)
    reserve = max_tokens if max_tokens and max_tokens > 0 else 0
    if prompt_tokens + reserve > window:
        raise ValueError(
            f"request exceeds context window for {model}: "
            f"estimated {prompt_tokens} prompt + {reserve} output > {window}"
        )


def _unpack_chain_result(result, default_model: str):
    """Accept old 3/4-tuple test stubs and the current 6-tuple."""
    if len(result) == 6:
        return result
    if len(result) == 4:
        text, tokens, cost, last = result
        if isinstance(last, dict):
            return text, tokens, cost, default_model, 1, last
        return text, tokens, cost, last, 1, {}
    if len(result) == 3:
        text, tokens, cost = result
        return text, tokens, cost, default_model, 1, {}
    raise TypeError(f"unexpected completion result arity: {len(result)}")


def complete_chain(messages: list[dict], *, models: list[str],
                   timeout_seconds: int = 120, max_tokens: int = 0,
                   retries: int = 2, seed: int | None = None,
                   temperature: float | None = None,
                   max_models: int | None = None
                   ) -> tuple[str, int, float, str, int, dict]:
    """Try chain entries in order. Returns (text, tokens, cost, model, attempts, usage)."""
    last: Exception | None = None
    tried = 0
    for name in models:
        if max_models is not None and tried >= max(1, max_models):
            break
        tried += 1
        try:
            result = complete(
                messages, model=name, timeout_seconds=timeout_seconds,
                max_tokens=max_tokens, retries=retries, seed=seed,
                temperature=temperature,
            )
            text, tokens, cost, used, _attempts, usage = _unpack_chain_result(result, name)
            return text, tokens, cost, used, tried, usage
        except Exception as exc:
            if _auth_error(exc):
                raise
            last = exc
    raise last or RuntimeError("no models configured")


def policy_check(text: str, direction: str, mode: str,
                 db_path: Path | None) -> Any:
    """Run text policy and log every decision. Returns the worst decision."""
    if mode not in ("warn", "enforce"):
        return None
    from .policy import scan_text, worst
    decisions = scan_text(text, "outbound" if direction == "outbound" else "inbound")
    if db_path is not None and decisions:
        from .logging_db import log_policy_decision
        for d in decisions:
            log_policy_decision(
                db_path, action_kind=f"text:{direction}", decision=d.decision,
                rule_id=d.rule_id, detail=d.reason, receipt_hash=d.receipt_hash,
                binding_info={
                    "direction": direction, "mode": mode,
                    "source": "regex_policy", "decision": d.decision,
                },
            )
    return worst(decisions)


def record_observation(db_path: Path | None, project_id: str | None, skill_id: str,
                       prompt: str, outcome: str, *, judge: dict | None = None,
                       cost_usd: float = 0.0, latency_ms: int = 0,
                       plan: list | None = None) -> None:
    if db_path is None:
        return
    from .logging_db import current_project_id, log_observation
    log_observation(db_path, project_id=current_project_id(project_id),
                    skill_id=skill_id, prompt=prompt, outcome=outcome,
                    judge=judge, cost_usd=cost_usd, latency_ms=latency_ms,
                    plan=plan)


def _usage_counts(usage: dict) -> tuple[int, int, int]:
    prompt = int(usage.get("prompt_tokens") or 0)
    completion = int(usage.get("completion_tokens") or 0)
    cached = 0
    details = usage.get("prompt_tokens_details") or {}
    if isinstance(details, dict):
        cached = int(details.get("cached_tokens") or 0)
    return prompt, completion, cached


def _record_perf(db_path: Path | None, options: dict | None, *, model: str,
                 skill_id: str, duration_ms: int, success: bool,
                 usage: dict, cost_usd: float) -> None:
    if db_path is None or not _opt(options, "perf_cache_enabled", False):
        return
    try:
        from .perf_cache import record_sample
        prompt, completion, cached = _usage_counts(usage)
        record_sample(
            db_path, model=model, skill_id=skill_id,
            queue_depth=_opt(options, "queue_depth", 0),
            duration_ms=duration_ms, success=success,
            prompt_tokens=prompt, completion_tokens=completion,
            cached_tokens=cached, cost_usd=cost_usd, enabled=True,
        )
    except Exception:
        pass


def execute(request: ExecuteRequest, *, model: str, skill_paths: dict[str, str],
            db_path: Path | None = None, planner_score: float | None = None,
            fallback_prompt: str | None = None,
            skill_hashes: dict[str, str] | None = None,
            timeout_seconds: int = 120, max_tokens: int = 0,
            retries: int = 2, policy_mode: str = "off",
            project_id: str | None = None,
            fallback_models: list[str] | None = None,
            attest_manifest: Path | None = None,
            attest_key_path: Path | None = None,
            attest_strict: bool = False,
            options: dict | None = None) -> ExecuteResponse:
    """Run the skill via LiteLLM. Optionally log to SQLite."""
    t0 = time.time()
    timer = PhaseTimer()
    was_fallback = False
    text = ""
    tokens_used = 0
    cost_usd = 0.0
    used_model = ""
    structured_output: Any | None = None
    schema_valid: bool | None = None
    schema_error: str | None = None
    verifier_verdict: str | None = None
    failure_kind: str | None = None
    repairs = 0
    attempts = 1
    usage: dict = {}
    messages: list[dict] = []
    chain: list[str] = []
    skill_sha = (skill_hashes or {}).get(request.skill_id, "")
    output_ref: str | None = None
    preview_chars = int(_opt(options, "output_preview_chars", 8000))
    error_limit = int(_opt(options, "error_max_chars", 1000))

    def finish_error(err: str, kind: str, *, success: bool = False) -> ExecuteResponse:
        dur = time.time() - t0
        if db_path is not None:
            from .logging_db import log_execution
            log_execution(
                db_path, skill_id=request.skill_id, prompt=request.prompt,
                output=text, tokens_used=tokens_used,
                duration_seconds=dur, success=success, error=err[:error_limit],
                planner_score=planner_score, was_fallback=was_fallback,
                cost_usd=cost_usd, model=used_model or (chain[0] if chain else model),
                phases=timer.phases, repairs=repairs, output_ref=output_ref,
                failure_kind=kind,
            )
        record_observation(db_path, project_id, request.skill_id, request.prompt,
                           "error", cost_usd=cost_usd, latency_ms=int(dur * 1000))
        _record_perf(db_path, options, model=used_model or model,
                     skill_id=request.skill_id, duration_ms=int(dur * 1000),
                     success=False, usage=usage, cost_usd=cost_usd)
        return ExecuteResponse(
            skill_id=request.skill_id,
            output=text[:preview_chars],
            tokens_used=tokens_used,
            duration_seconds=dur,
            success=success,
            error=err[:error_limit],
            was_fallback=was_fallback,
            cost_usd=cost_usd,
            model=used_model,
            structured_output=structured_output,
            schema_valid=schema_valid,
            verifier_verdict=verifier_verdict,
            phases=timer.phases,
            attempts=attempts,
            repairs=repairs,
            output_ref=output_ref,
            failure_kind=kind,
        )

    try:
        with timer.phase("attest"):
            if attest_strict:
                if attest_manifest is None:
                    raise ValueError("strict attestation requires a manifest path")
                from .attest import verify_manifest
                result = verify_manifest(
                    attest_manifest,
                    attest_key_path or Path("~/.config/agent-foundry/attest.key"),
                    root=attest_manifest.parent,
                )
                if not result.ok:
                    detail = (result.errors or result.mismatched or result.missing)[:3]
                    raise ValueError(f"skill attestation failed: {detail}")

        with timer.phase("policy_in"):
            inbound = policy_check(request.prompt, "inbound", policy_mode, db_path)
        if inbound is not None and policy_mode == "enforce" \
                and inbound.decision in ("deny", "confirm"):
            return finish_error(f"policy {inbound.decision}: {inbound.rule_id}", "policy")

        was_fallback = request.skill_id == GENERIC_REASONING_ID
        chain = _model_chain(
            model,
            request.fallback_models if request.fallback_models is not None
            else fallback_models,
        )
        with timer.phase("build_messages"):
            messages, was_fallback = build_messages(
                request.skill_id, request.prompt, skill_paths,
                fallback_prompt=fallback_prompt,
                expected_sha256=skill_sha,
                model=chain[0],
            )

        constraint_kind = None
        enforced_by = None
        if request.output_schema is not None:
            messages = _with_schema(messages, request.output_schema)
            constraint_kind = "json_schema"
            enforced_by = "prompt_only"

        with timer.phase("preflight"):
            _preflight(messages, chain[0], max_tokens)

        max_models = None
        if _opt(options, "adaptive_retries", False) and db_path is not None:
            from .retry_policy import allocate_attempts, success_rate
            depth = int(_opt(options, "queue_depth", 0))
            min_depth = int(_opt(options, "adaptive_retries_min_queue_depth", 2))
            if depth >= min_depth:
                p = success_rate(
                    db_path, skill_id=request.skill_id, model=chain[0],
                    min_samples=int(_opt(options, "adaptive_retries_min_samples", 10)),
                )
                max_models = allocate_attempts(
                    p, max_attempts=max(1, int(_opt(options, "max_attempts", 3))),
                )
                attempts = max_models

        with timer.phase("complete"):
            text, tokens_used, cost_usd, used_model, attempts, usage = complete_chain(
                messages, models=chain, timeout_seconds=timeout_seconds,
                max_tokens=max_tokens, retries=retries,
                seed=request.seed, temperature=request.temperature,
                max_models=max_models,
            )

        if request.output_schema is not None:
            errors: list[str] = []
            with timer.phase("schema"):
                try:
                    structured_output = _extract_json(text)
                    errors = schema_errors(structured_output, request.output_schema)
                except ValueError as exc:
                    errors = [str(exc)]
            if errors:
                repair = messages + [
                    {"role": "assistant", "content": text},
                    {"role": "user", "content":
                     "That reply did not satisfy the schema: "
                     + "; ".join(errors[:3])
                     + ". Return only the corrected JSON value."},
                ]
                repairs = 1
                with timer.phase("schema_repair"):
                    try:
                        text, t2, c2, used_model, _repair_attempts, usage2 = complete_chain(
                            repair, models=[used_model],
                            timeout_seconds=timeout_seconds,
                            max_tokens=max_tokens, retries=retries,
                            seed=request.seed, temperature=request.temperature,
                        )
                        tokens_used += t2
                        cost_usd += c2
                        usage = usage2
                        structured_output = _extract_json(text)
                        errors = schema_errors(structured_output, request.output_schema)
                    except Exception as exc:
                        errors = [str(exc)]
            schema_valid = not errors
            if errors:
                schema_error = "output does not match schema: " + "; ".join(errors[:3])
                failure_kind = "schema"

        if request.verifier is not None:
            from .verifiers import run as run_verifier
            kind = str(request.verifier.get("kind") or "json_schema")
            spec = request.verifier.get("spec") or {}
            if structured_output is None:
                try:
                    structured_output = _extract_json(text)
                except ValueError:
                    structured_output = None
            verifier_verdict = run_verifier(kind, structured_output, spec)
            if verifier_verdict == "pass":
                schema_valid = True
                schema_error = None
                failure_kind = None
            elif verifier_verdict == "fail":
                schema_valid = False
                failure_kind = "schema"
                schema_error = f"verifier {kind} rejected the output"
    except Exception as exc:
        err = str(exc)
        kind = failure_kind or ("attest" if "attestation failed" in err else "provider")
        return finish_error(err, kind)

    with timer.phase("policy_out"):
        outbound = policy_check(text, "outbound", policy_mode, db_path)
    if outbound is not None and policy_mode == "enforce" \
            and outbound.decision in ("deny", "confirm"):
        return finish_error(
            f"policy {outbound.decision}: {outbound.rule_id}", "policy",
        )

    dur = time.time() - t0
    digest = trace_digest(
        skill_id=request.skill_id, skill_sha256=skill_sha, models=chain,
        messages=messages, output=text, schema=request.output_schema,
        seed=request.seed, temperature=request.temperature,
    )
    meta = request_metadata(
        skill_id=request.skill_id, skill_sha256=skill_sha, models=chain,
        messages=messages, schema=request.output_schema, seed=request.seed,
        temperature=request.temperature, constraint_kind=constraint_kind,
        enforced_by=enforced_by,
    )
    config = run_config(
        skill_id=request.skill_id, models=chain, seed=request.seed,
        temperature=request.temperature, schema=request.output_schema,
    )

    if _opt(options, "spill_enabled", True) and db_path is not None:
        try:
            from .spill import default_spill_root, save_output
            root = _opt(options, "spill_root", None)
            output_ref = save_output(
                Path(root) if root else default_spill_root(),
                session_id=_opt(options, "session_id", None),
                execution_id=uuid.uuid4().hex, text=text,
            )
        except Exception:
            output_ref = None

    schema_failed = request.output_schema is not None and schema_valid is False
    if db_path is not None:
        from .logging_db import log_execution
        prompt_tokens, completion_tokens, cached_tokens = _usage_counts(usage)
        log_execution(
            db_path, skill_id=request.skill_id, prompt=request.prompt,
            output=text, tokens_used=tokens_used, duration_seconds=dur,
            success=not schema_failed, error=schema_error,
            planner_score=planner_score, was_fallback=was_fallback,
            cost_usd=cost_usd, model=used_model, trace_digest=digest,
            phases=timer.phases, repairs=repairs, output_ref=output_ref,
            failure_kind=failure_kind,
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
            cached_tokens=cached_tokens, request_meta=meta, run_config=config,
        )
    record_observation(db_path, project_id, request.skill_id, request.prompt,
                       "error" if schema_failed else "success",
                       cost_usd=cost_usd, latency_ms=int(dur * 1000))
    _record_perf(db_path, options, model=used_model, skill_id=request.skill_id,
                 duration_ms=int(dur * 1000), success=not schema_failed,
                 usage=usage, cost_usd=cost_usd)

    return ExecuteResponse(
        skill_id=request.skill_id,
        output=text[:preview_chars],
        tokens_used=tokens_used,
        duration_seconds=dur,
        success=not schema_failed,
        error=schema_error,
        was_fallback=was_fallback,
        cost_usd=cost_usd,
        model=used_model,
        structured_output=structured_output,
        schema_valid=schema_valid,
        verifier_verdict=verifier_verdict,
        trace_digest=digest,
        phases=timer.phases,
        attempts=attempts,
        repairs=repairs,
        output_ref=output_ref,
        failure_kind=failure_kind,
    )
