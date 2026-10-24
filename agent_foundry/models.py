"""Pydantic data models for Agent Foundry."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class TokenEstimate(BaseModel):
    """Cost estimate in tokens. Total is auto-computed if not provided."""
    input: int = Field(ge=0, description="Input tokens (skill body + prompt)")
    output: int = Field(ge=0, description="Estimated output tokens")
    total: int = Field(default=0, ge=0, description="input + output (computed)")

    @model_validator(mode="before")
    @classmethod
    def _compute_total(cls, values):
        if isinstance(values, dict):
            inp = values.get("input", 0) or 0
            out = values.get("output", 0) or 0
            values = dict(values)
            values.setdefault("total", inp + out)
        return values


class SkillManifest(BaseModel):
    """One skill, as stored in skills/index.json."""
    id: str = Field(pattern=r"^[a-z0-9-]+$")
    name: str
    description: str = Field(max_length=500)
    trigger_patterns: list[str] = Field(default_factory=list)
    estimated_token_cost: dict = Field(default_factory=lambda: {"input": 200, "output": 300})
    estimated_time_seconds: int = 3
    version: str = "0.1.0"
    license: str = "MIT"
    category: Literal["core", "optional"] = "core"
    location: str
    tags: list[str] = Field(default_factory=list)
    is_fallback: bool = False
    sha256: str = ""

    def total_cost(self) -> int:
        c = self.estimated_token_cost or {}
        return (c.get("input", 0) or 0) + (c.get("output", 0) or 0)


class SkillIndex(BaseModel):
    """The full skill index."""
    version: str = "1"
    generated_at: datetime
    skills: list[SkillManifest]
    skill_paths: dict[str, str] = Field(default_factory=dict)
    skill_stats: dict[str, list[int]] = Field(default_factory=dict)  # path -> [size, mtime_ns]


# ===== Planner =====

class PlanRequest(BaseModel):
    prompt: str
    max_results: int = 5
    graph_path: str | None = None


class PlanResult(BaseModel):
    """One ranked skill in a plan."""
    skill_id: str
    name: str
    description: str
    score: float
    matched_patterns: list[str] = Field(default_factory=list)
    estimated_cost: TokenEstimate
    location: str | None = None


class PlanResponse(BaseModel):
    """Plan endpoint reply: ranked list of skills."""
    prompt: str
    results: list[PlanResult]
    total_available: int


# ===== Executor =====

class ExecuteRequest(BaseModel):
    skill_id: str
    prompt: str
    force: bool = False
    model: str | None = None
    fallback_models: list[str] | None = None
    output_schema: dict | None = None
    verifier: dict | None = None
    seed: int | None = None
    temperature: float | None = None


class ExecuteResponse(BaseModel):
    """Execute endpoint reply."""
    skill_id: str
    output: str = ""
    tokens_used: int = 0
    duration_seconds: float = 0.0
    success: bool = True
    error: str | None = None
    requires_confirmation: bool = False
    estimated_cost: TokenEstimate | None = None
    was_fallback: bool = False
    cost_usd: float = 0.0
    model: str = ""
    structured_output: Any | None = None
    schema_valid: bool | None = None
    verifier_verdict: Literal["pass", "fail", "unknown"] | None = None
    trace_digest: str = ""
    phases: dict[str, float] | None = None
    attempts: int = 1
    repairs: int = 0
    output_ref: str | None = None
    failure_kind: Literal[
        "provider", "schema", "policy", "attest", "budget", "internal"
    ] | None = None


# ===== Loop =====

class LoopRequest(BaseModel):
    prompt: str
    force: bool = False
    model: str | None = None
    budget: int | None = None
    judge: bool = False  # if true, score output via af-critic
    seed: int | None = None
    temperature: float | None = None


class LoopResponse(BaseModel):
    """Loop endpoint reply."""
    plan: list[PlanResult] = Field(default_factory=list)
    skill_id: str | None = None
    output: str = ""
    tokens_used: int = 0
    duration_seconds: float = 0.0
    success: bool = True
    error: str | None = None
    requires_confirmation: bool = False
    estimated_cost: TokenEstimate | None = None
    was_fallback: bool = False
    judge_score: dict | None = None   # correctness/slop/scope/verdict if --judge
    judged: bool = False
    judge_status: str | None = None
    cost_usd: float = 0.0
    session_id: int | None = None
    trace_digest: str = ""
    phases: dict[str, float] | None = None
    attempts: int = 1
    repairs: int = 0
    output_ref: str | None = None
    compacted_turns: int = 0
    failure_kind: Literal[
        "provider", "schema", "policy", "attest", "budget", "internal"
    ] | None = None


class LoopResumeRequest(BaseModel):
    session_id: int
    prompt: str
    model: str | None = None
    seed: int | None = None
    temperature: float | None = None


# ===== Index =====

class StatsResponse(BaseModel):
    total_executions: int = 0
    successful: int = 0
    failed: int = 0
    fallback_count: int = 0
    avg_tokens: int = 0
    avg_duration: float = 0.0
    thumbs_up: int = 0
    thumbs_down: int = 0
    instincts_count: int = 0


class FeedbackRequest(BaseModel):
    execution_id: int
    feedback: int = Field(..., description="1 = thumbs_up, -1 = thumbs_down")


class LearnResponse(BaseModel):
    new_instincts: int = 0
    updated_instincts: int = 0
    patterns_found: list[dict] = Field(default_factory=list)


class IndexResponse(BaseModel):
    total_skills: int
    took_ms: float
    regenerated: bool = True
