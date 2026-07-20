"""Planner: rank skills by prompt relevance + cost penalty."""
from __future__ import annotations

import re
from typing import Iterable

from .config import PlannerConfig
from .indexer import GENERIC_REASONING_ID, get_index_cached
from .models import (
    PlanRequest,
    PlanResponse,
    PlanResult,
    SkillIndex,
    SkillManifest,
    TokenEstimate,
)


def _cost_penalty(total_cost: int, divisor: float) -> float:
    return 1.0 / (1.0 + total_cost / divisor)


def _match_patterns(prompt: str, patterns: Iterable[str]) -> list[str]:
    """Return list of patterns that match the prompt (substring/regex).
    Patterns are tried as regex; if invalid or empty, fall back to plain substring."""
    matched: list[str] = []
    p_lower = prompt.lower()
    for pat in patterns or []:
        if not pat:
            continue
        try:
            if re.search(pat, prompt, re.IGNORECASE | re.DOTALL):
                matched.append(pat)
                continue
        except re.error:
            pass
        # Fallback: literal substring match
        raw = pat.replace(r"\b", "").replace("\\", "")
        if raw and raw.lower() in p_lower:
            matched.append(pat)
    return matched


def _name_in_prompt(prompt: str, skill: SkillManifest) -> bool:
    p_lower = prompt.lower()
    name_lower = (skill.name or "").lower()
    if name_lower and name_lower in p_lower:
        return True
    desc_lower = (skill.description or "").lower()
    if desc_lower and desc_lower[:60] in p_lower:
        return True
    return False


def rank_skills(prompt: str, idx: SkillIndex, cfg: PlannerConfig) -> list[PlanResult]:
    """Return skills ranked by score (desc). Excludes the fallback from pattern-based ranking."""
    results: list[tuple[float, PlanResult]] = []

    for skill in idx.skills:
        if skill.is_fallback:
            continue

        matched = _match_patterns(prompt, skill.trigger_patterns)
        score = len(matched) * cfg.pattern_match_weight

        if _name_in_prompt(prompt, skill):
            score += cfg.name_in_prompt_boost

        if score <= 0:
            continue

        total_cost = skill.total_cost()
        score *= _cost_penalty(total_cost, cfg.cost_penalty_divisor)

        cost = TokenEstimate(
            input=int(skill.estimated_token_cost.get("input", 0)),
            output=int(skill.estimated_token_cost.get("output", 0)),
        )
        results.append((
            score,
            PlanResult(
                skill_id=skill.id,
                name=skill.name,
                description=skill.description,
                score=round(score, 4),
                matched_patterns=matched,
                estimated_cost=cost,
                location=skill.location,
            ),
        ))

    results.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in results[:cfg.max_results]]


def plan(request: PlanRequest, idx: SkillIndex, cfg: PlannerConfig) -> PlanResponse:
    ranked = rank_skills(request.prompt, idx, cfg)
    return PlanResponse(
        prompt=request.prompt,
        results=ranked,
        total_available=len(idx.skills),
    )
