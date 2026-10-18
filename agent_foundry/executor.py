"""Executor: run a skill (prompt + body) via LiteLLM."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from .indexer import GENERIC_REASONING_ID, GENERIC_REASONING_SYSTEM_PROMPT
from .model_catalog import resolve_model
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


def complete_chain(messages: list[dict], *, models: list[str],
                   timeout_seconds: int = 120, max_tokens: int = 0,
                   retries: int = 2) -> tuple[str, int, float, str]:
    """Try each model in order. Returns (text, tokens, cost, used_model)."""
    last: Exception | None = None
    for name in models:
        try:
            text, tokens, cost = complete(
                messages, model=name, timeout_seconds=timeout_seconds,
                max_tokens=max_tokens, retries=retries,
            )
            return text, tokens, cost, name
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
            attest_strict: bool = False) -> ExecuteResponse:
    """Run the skill via LiteLLM. Optionally log to SQLite."""
    t0 = time.time()
    was_fallback = False
    text = ""
    tokens_used = 0
    cost_usd = 0.0
    used_model = ""
    structured_output: Any | None = None
    schema_valid: bool | None = None
    schema_error: str | None = None
    try:
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

        inbound = policy_check(request.prompt, "inbound", policy_mode, db_path)
        if inbound is not None and policy_mode == "enforce" \
                and inbound.decision in ("deny", "confirm"):
            return ExecuteResponse(
                skill_id=request.skill_id, success=False,
                error=f"policy {inbound.decision}: {inbound.rule_id}",
                requires_confirmation=inbound.decision == "confirm",
                was_fallback=request.skill_id == GENERIC_REASONING_ID,
            )

        was_fallback = request.skill_id == GENERIC_REASONING_ID
        messages, was_fallback = build_messages(
            request.skill_id, request.prompt, skill_paths,
            fallback_prompt=fallback_prompt,
            expected_sha256=(skill_hashes or {}).get(request.skill_id),
        )
        chain = _model_chain(
            model,
            request.fallback_models if request.fallback_models is not None
            else fallback_models,
        )
        if request.output_schema is not None:
            messages = _with_schema(messages, request.output_schema)
        text, tokens_used, cost_usd, used_model = complete_chain(
            messages, models=chain, timeout_seconds=timeout_seconds,
            max_tokens=max_tokens, retries=retries,
        )
        if request.output_schema is not None:
            errors: list[str] = []
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
                try:
                    text, t2, c2, used_model = complete_chain(
                        repair, models=[used_model],
                        timeout_seconds=timeout_seconds,
                        max_tokens=max_tokens, retries=retries,
                    )
                    tokens_used += t2
                    cost_usd += c2
                    structured_output = _extract_json(text)
                    errors = schema_errors(structured_output, request.output_schema)
                except Exception as exc:
                    errors = [str(exc)]
            schema_valid = not errors
            if errors:
                schema_error = "output does not match schema: " + "; ".join(errors[:3])
    except Exception as exc:
        err = str(exc)
        dur = time.time() - t0
        if db_path is not None:
            from .logging_db import log_execution
            log_execution(db_path, skill_id=request.skill_id, prompt=request.prompt,
                          output=text, tokens_used=tokens_used,
                          duration_seconds=dur, success=False, error=err[:1000],
                          planner_score=planner_score, was_fallback=was_fallback,
                          cost_usd=cost_usd)
        record_observation(db_path, project_id, request.skill_id, request.prompt,
                           "error", cost_usd=cost_usd, latency_ms=int(dur * 1000))
        return ExecuteResponse(
            skill_id=request.skill_id,
            output=text[:OUTPUT_MAX_CHARS],
            tokens_used=tokens_used,
            duration_seconds=dur,
            success=False,
            error=err[:1000],
            was_fallback=was_fallback,
            cost_usd=cost_usd,
            model=used_model,
            structured_output=structured_output,
            schema_valid=schema_valid,
        )

    dur = time.time() - t0
    outbound = policy_check(text, "outbound", policy_mode, db_path)
    if outbound is not None and policy_mode == "enforce" \
            and outbound.decision in ("deny", "confirm"):
        err = f"policy {outbound.decision}: {outbound.rule_id}"
        if db_path is not None:
            from .logging_db import log_execution
            log_execution(db_path, skill_id=request.skill_id, prompt=request.prompt,
                          output="", tokens_used=tokens_used,
                          duration_seconds=dur, success=False, error=err,
                          planner_score=planner_score, was_fallback=was_fallback,
                          cost_usd=cost_usd)
        record_observation(db_path, project_id, request.skill_id, request.prompt,
                           "error", cost_usd=cost_usd, latency_ms=int(dur * 1000))
        return ExecuteResponse(
            skill_id=request.skill_id, output="", tokens_used=tokens_used,
            duration_seconds=dur, success=False, error=err,
            was_fallback=was_fallback, cost_usd=cost_usd, model=used_model,
            structured_output=structured_output, schema_valid=schema_valid,
        )

    schema_failed = request.output_schema is not None and schema_valid is False
    if db_path is not None:
        from .logging_db import log_execution
        log_execution(db_path, skill_id=request.skill_id, prompt=request.prompt,
                      output=text, tokens_used=tokens_used,
                      duration_seconds=dur, success=not schema_failed,
                      error=schema_error, planner_score=planner_score,
                      was_fallback=was_fallback, cost_usd=cost_usd)
    record_observation(db_path, project_id, request.skill_id, request.prompt,
                       "error" if schema_failed else "success",
                       cost_usd=cost_usd, latency_ms=int(dur * 1000))

    return ExecuteResponse(
        skill_id=request.skill_id,
        output=text[:OUTPUT_MAX_CHARS],
        tokens_used=tokens_used,
        duration_seconds=dur,
        success=not schema_failed,
        error=schema_error,
        was_fallback=was_fallback,
        cost_usd=cost_usd,
        model=used_model,
        structured_output=structured_output,
        schema_valid=schema_valid,
    )
