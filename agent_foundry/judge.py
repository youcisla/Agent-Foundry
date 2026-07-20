"""Judge: score an output against a rubric using af-critic."""
from __future__ import annotations

import json
import re
import time
from typing import Any

from .models import TokenEstimate


# When the LLM-judge runs on a known small rubric, these defaults are fine.
DEFAULT_JUDGE_INPUT_HARD = 200
DEFAULT_JUDGE_INPUT_PER_1K_CHARS = 200  # input tokens per 1k output chars
DEFAULT_JUDGE_OUTPUT = 100


def estimate_judge_cost(output_chars: int) -> TokenEstimate:
    inp = DEFAULT_JUDGE_INPUT_HARD + (output_chars // 1000) * DEFAULT_JUDGE_INPUT_PER_1K_CHARS
    return TokenEstimate(input=inp, output=DEFAULT_JUDGE_OUTPUT)


def _parse_json_score(text: str) -> dict[str, Any] | None:
    """Extract the first JSON object from the judge output."""
    if not text:
        return None
    # Try direct parse first
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    # Fallback: find the JSON block
    m = re.search(r"\{[^{}]*\"correctness\"[^{}]*\}", text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(0))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return None


def judge_output(
    task: str,
    output: str,
    *,
    model: str,
    judge_skill_id: str = "af-critic",
    skill_paths: dict[str, str] | None = None,
    fallback_prompt: str | None = None,
) -> dict | None:
    """Use the af-critic skill to score output against the task. Returns the parsed
    judge JSON or None if the call fails / returns unparseable output."""
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
    try:
        resp = litellm.completion(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
        )
        text = resp.choices[0].message.content or ""
    except Exception:
        return None

    dur = time.time() - t0
    parsed = _parse_json_score(text)
    if parsed is None:
        return None
    parsed["_judge_duration_seconds"] = round(dur, 3)
    return parsed
