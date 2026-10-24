"""Judge: score an output against a rubric using af-critic."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Literal

from .models import TokenEstimate


# When the LLM-judge runs on a known small rubric, these defaults are fine.
DEFAULT_JUDGE_INPUT_HARD = 200
DEFAULT_JUDGE_INPUT_PER_1K_CHARS = 200  # input tokens per 1k output chars
DEFAULT_JUDGE_OUTPUT = 100


def estimate_judge_cost(output_chars: int) -> TokenEstimate:
    inp = DEFAULT_JUDGE_INPUT_HARD + (output_chars // 1000) * DEFAULT_JUDGE_INPUT_PER_1K_CHARS
    return TokenEstimate(input=inp, output=DEFAULT_JUDGE_OUTPUT)


JudgeStatus = Literal["ok", "unparseable", "call_failed", "timeout"]


@dataclass
class JudgeResult:
    """One judge attempt. `status` is independent from the score value."""
    status: JudgeStatus
    scores: dict[str, Any] | None = None
    duration_s: float = 0.0
    model: str = ""
    error: str | None = None
    attempts: int = 1
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == "ok" and self.scores is not None


def _extract_json_object(text: str) -> dict[str, Any] | None:
    """Balanced-brace extraction; tolerates fences and nested objects."""
    if not text:
        return None
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    try:
        data = json.loads(stripped)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass
    start = stripped.find("{")
    while start != -1:
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(stripped)):
            ch = stripped[i]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        data = json.loads(stripped[start:i + 1])
                        if isinstance(data, dict):
                            return data
                    except json.JSONDecodeError:
                        pass
                    break
        start = stripped.find("{", start + 1)
    return None


def judge_output(
    task: str,
    output: str,
    *,
    model: str,
    judge_skill_id: str = "af-critic",
    skill_paths: dict[str, str] | None = None,
    fallback_prompt: str | None = None,
    timeout_seconds: int = 30,
    retries: int = 1,
) -> JudgeResult:
    """Score output. Transport errors retry; parse failures never become a score."""
    import litellm
    from .executor import build_messages

    if skill_paths is None:
        skill_paths = {}

    judge_prompt = (
        f"## Task\n{task}\n\n## Output\n{output}\n\n"
        "Score the output per the rubric in your system prompt. "
        "Return only the JSON object."
    )

    messages, _ = build_messages(judge_skill_id, judge_prompt, skill_paths,
                                 fallback_prompt=fallback_prompt)

    t0 = time.time()
    last_error: str | None = None
    attempts = max(1, retries + 1)
    status: JudgeStatus = "call_failed"
    for attempt in range(1, attempts + 1):
        try:
            resp = litellm.completion(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                timeout=timeout_seconds,
                num_retries=0,
            )
        except TimeoutError as exc:
            last_error = f"timeout: {exc}"
            status = "timeout"
            continue
        except Exception as exc:  # noqa: BLE001 - status must be observable
            last_error = str(exc)
            status = "call_failed"
            continue

        text = resp.choices[0].message.content or ""
        parsed = _extract_json_object(text)
        dur = time.time() - t0
        if parsed is None:
            return JudgeResult(
                status="unparseable", duration_s=round(dur, 3), model=model,
                error="judge output was not a JSON object", attempts=attempt,
            )
        parsed["_judge_duration_seconds"] = round(dur, 3)
        return JudgeResult(
            status="ok", scores=parsed, duration_s=round(dur, 3),
            model=model, attempts=attempt,
        )

    return JudgeResult(
        status=status, duration_s=round(time.time() - t0, 3), model=model,
        error=last_error, attempts=attempts,
    )
