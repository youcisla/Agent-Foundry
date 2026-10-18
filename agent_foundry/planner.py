"""Planner: rank skills by prompt relevance + cost penalty + graph relationships."""
from __future__ import annotations

import hashlib
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


_STOPWORDS = frozenset({
    "the", "and", "for", "that", "this", "with", "from", "how", "what",
    "when", "why", "where", "which", "your", "have", "will", "can", "are",
    "not", "but", "all", "was", "out", "use", "into", "any", "its", "our",
})


def _keyword_overlap(prompt: str, skill: SkillManifest, limit: int = 3) -> int:
    """Cheap lexical fallback when trigger regexes miss. Count shared content words."""
    p = {w for w in re.findall(r"[a-z]{3,}", prompt.lower()) if w not in _STOPWORDS}
    d = {w for w in re.findall(r"[a-z]{3,}", (skill.description or "").lower())
         if w not in _STOPWORDS}
    return min(limit, len(p & d))


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


_GRAPH_CACHE: dict[str, tuple[float, dict[str, list[str]]]] = {}
_SEM_CACHE: dict = {"key": None, "model": None, "ids": [], "vectors": []}


def _graph_adjacency(graph_path: Path) -> dict[str, list[str]]:
    """Parse the graph once per mtime and return an undirected adjacency map."""
    try:
        mtime = graph_path.stat().st_mtime
    except OSError:
        return {}
    cached = _GRAPH_CACHE.get(str(graph_path))
    if cached and cached[0] == mtime:
        return cached[1]

    try:
        data = json.loads(graph_path.read_text())
        edges = data.get("links", data.get("edges", []))
        adj: dict[str, list[str]] = {}
        for e in edges:
            src = e.get("source", "")
            tgt = e.get("target", "")
            if not src or not tgt:
                continue
            adj.setdefault(src, []).append(tgt)
            adj.setdefault(tgt, []).append(src)
    except Exception:
        return {}
    _GRAPH_CACHE[str(graph_path)] = (mtime, adj)
    return adj


def _graph_related(skill_id: str, graph_path: Path | None,
                   depth: int = 1) -> list[str]:
    """Return skill IDs connected in the knowledge graph (max 3 per depth)."""
    if not graph_path or not graph_path.exists():
        return []
    adj = _graph_adjacency(graph_path)
    related: list[str] = []
    frontier = [skill_id]
    seen = {skill_id}
    for _ in range(max(1, depth)):
        nxt: list[str] = []
        for node in frontier:
            for neigh in adj.get(node, []):
                if neigh not in seen:
                    seen.add(neigh)
                    nxt.append(neigh)
        related.extend(nxt[:3])
        frontier = nxt
    return related


def _semantic_scores(prompt: str, skills: list[SkillManifest], model_name: str) -> dict[str, float]:
    """Cosine similarity of prompt vs skill descriptions. Empty if unavailable."""
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except Exception:
        return {}

    signature = hashlib.sha1(
        (model_name + "|" + "|".join(f"{s.id}:{s.description}" for s in skills)).encode()
    ).hexdigest()
    if _SEM_CACHE["key"] != signature:
        try:
            model = _SEM_CACHE["model"]
            if model is None or _SEM_CACHE.get("model_name") != model_name:
                model = SentenceTransformer(model_name)
            vectors = model.encode([s.description for s in skills], normalize_embeddings=True)
            _SEM_CACHE.update({
                "key": signature,
                "model": model,
                "model_name": model_name,
                "ids": [s.id for s in skills],
                "vectors": [list(map(float, v)) for v in vectors],
            })
        except Exception:
            return {}

    try:
        q = _SEM_CACHE["model"].encode([prompt], normalize_embeddings=True)[0]
        q = list(map(float, q))
    except Exception:
        return {}

    out: dict[str, float] = {}
    for sid, vec in zip(_SEM_CACHE["ids"], _SEM_CACHE["vectors"]):
        out[sid] = sum(a * b for a, b in zip(q, vec))  # vectors are normalized
    return out


def _llm_rerank(prompt: str, results: list[tuple[float, PlanResult]],
                model: str, top_k: int) -> list[tuple[float, PlanResult]]:
    """Optional LLM ordering of the top candidates. Returns input on any failure."""
    try:
        import litellm

        candidates = [
            {"id": r.skill_id, "description": (r.description or "")[:160]}
            for _, r in results[:top_k]
        ]
        messages = [
            {"role": "system",
             "content": 'Reorder the candidate skills for the prompt. Return only JSON: {"order": ["id", ...]}.'},
            {"role": "user",
             "content": json.dumps({"prompt": prompt, "candidates": candidates})},
        ]
        resp = litellm.completion(
            model=model, messages=messages, timeout=30,
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.choices[0].message.content or "{}")
        order = data.get("order") or []
        rank = {sid: i for i, sid in enumerate(order)}
        head = sorted(results[:top_k], key=lambda pair: rank.get(pair[1].skill_id, 999))
        return head + results[top_k:]
    except Exception:
        return results


def rank_skills(prompt: str, idx: SkillIndex, cfg: PlannerConfig,
                graph_path: Path | None = None,
                weights: dict[str, float] | None = None,
                rerank_model: str | None = None) -> list[PlanResult]:
    """Return skills ranked by score (desc). Graph-aware: boosts skills related to the top match."""
    results: list[tuple[float, PlanResult]] = []

    semantic: dict[str, float] = {}
    if cfg.semantic_enabled:
        semantic = _semantic_scores(prompt, [s for s in idx.skills if not s.is_fallback],
                                    cfg.semantic_model)

    for skill in idx.skills:
        if skill.is_fallback:
            continue

        matched = _match_patterns(prompt, skill.trigger_patterns)
        score = len(matched) * cfg.pattern_match_weight

        if _name_in_prompt(prompt, skill):
            score += cfg.name_in_prompt_boost

        overlap = _keyword_overlap(prompt, skill)
        if overlap:
            score += overlap * 0.04

        if semantic:
            score += max(0.0, semantic.get(skill.id, 0.0)) * cfg.semantic_weight

        if score <= 0:
            continue

        total_cost = skill.total_cost()
        score *= _cost_penalty(total_cost, cfg.cost_penalty_divisor)
        if weights:
            score *= max(0.1, float(weights.get(skill.id, 1.0)))

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

    # Graph-aware boost: top match boosts its 2-hop neighborhood.
    if graph_path and results:
        top_id = results[0][1].skill_id
        related = _graph_related(top_id, graph_path, depth=2)
        if related:
            boost = {sid: (1.15 if i < 3 else 1.08) for i, sid in enumerate(related)}
            for i, (s, r) in enumerate(results):
                factor = boost.get(r.skill_id)
                if factor:
                    results[i] = (s * factor, r)

    results.sort(key=lambda x: x[0], reverse=True)
    if cfg.rerank_enabled and rerank_model and len(results) > 1:
        results = _llm_rerank(prompt, results, rerank_model, cfg.rerank_top_k)
    return [r for _, r in results[:cfg.max_results]]


def _safe_graph_path(raw: str | None) -> Path | None:
    """Only allow graph JSON inside the repo root or current working directory."""
    if not raw:
        return None
    try:
        path = Path(raw).expanduser().resolve()
    except OSError:
        return None
    if path.suffix.lower() != ".json" or not path.is_file():
        return None
    roots = [Path.cwd().resolve(), Path(__file__).resolve().parent.parent]
    if not any(path.is_relative_to(root) for root in roots):
        return None
    return path


def plan(request: PlanRequest, idx: SkillIndex, cfg: PlannerConfig,
         weights: dict[str, float] | None = None,
         rerank_model: str | None = None) -> PlanResponse:
    graph_path = _safe_graph_path(request.graph_path)
    ranked = rank_skills(request.prompt, idx, cfg, graph_path=graph_path,
                         weights=weights, rerank_model=rerank_model)
    return PlanResponse(
        prompt=request.prompt,
        results=ranked,
        total_available=len(idx.skills),
    )
