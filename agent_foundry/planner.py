"""Planner: rank skills by prompt relevance + cost penalty + graph relationships."""
from __future__ import annotations

import json
import re
from pathlib import Path
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
        raw = pat.replace(r"\b", "").replace("\\\\", "")
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


def _graph_related(skill_id: str, graph_path: Path | None) -> list[str]:
    """Return skill IDs connected in the knowledge graph (max 3)."""
    if not graph_path or not graph_path.exists():
        return []
    try:
        data = json.loads(graph_path.read_text())
        edges = data.get("links", data.get("edges", []))
        related: set[str] = set()
        for e in edges:
            src = e.get("source", "")
            tgt = e.get("target", "")
            if src == skill_id:
                related.add(tgt)
            if tgt == skill_id:
                related.add(src)
        return sorted(related)[:3]
    except Exception:
        return []


def rank_skills(prompt: str, idx: SkillIndex, cfg: PlannerConfig, graph_path: Path | None = None) -> list[PlanResult]:
    """Return skills ranked by score (desc). Graph-aware: boosts skills related to the top match."""
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

    # Graph-aware boost: top match gets its related skills boosted
    if graph_path and results:
        top_id = results[0][1].skill_id
        related = _graph_related(top_id, graph_path)
        if related:
            for i, (s, r) in enumerate(results):
                if r.skill_id in related:
                    results[i] = (s * 1.15, r)  # 15% boost

    results.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in results[:cfg.max_results]]


def plan(request: PlanRequest, idx: SkillIndex, cfg: PlannerConfig) -> PlanResponse:
    graph_path = Path(request.graph_path) if request.graph_path else None
    ranked = rank_skills(request.prompt, idx, cfg, graph_path=graph_path)
    return PlanResponse(
        prompt=request.prompt,
        results=ranked,
        total_available=len(idx.skills),
    )
