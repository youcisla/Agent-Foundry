"""Latest Claude model identifiers and short aliases.

The catalog is intentionally small: Agent Foundry routes skills, it does not
host models. Aliases keep config and CLI ergonomic; full IDs stay stable for
logs and receipts.
"""
from __future__ import annotations

from typing import Any

DEFAULT_MODEL = "claude-sonnet-5-5"

# Full IDs are the contract. Aliases are convenience only.
MODELS: list[dict[str, Any]] = [
    {
        "id": "claude-fable-5-1",
        "alias": "fable",
        "name": "Claude Fable 5.1",
        "tier": "frontier",
    },
    {
        "id": "claude-opus-5-5",
        "alias": "opus",
        "name": "Claude Opus 5.5",
        "tier": "deep",
    },
    {
        "id": "claude-sonnet-5-5",
        "alias": "sonnet",
        "name": "Claude Sonnet 5.5",
        "tier": "balanced",
    },
    {
        "id": "claude-haiku-5-5",
        "alias": "haiku",
        "name": "Claude Haiku 5.5",
        "tier": "fast",
    },
]

ALIASES: dict[str, str] = {m["alias"]: m["id"] for m in MODELS}
ALIASES.update({m["id"]: m["id"] for m in MODELS})


def resolve_model(name: str | None, default: str = DEFAULT_MODEL) -> str:
    """Resolve an alias or full ID. Unknown values pass through unchanged."""
    if not name:
        return default
    key = name.strip()
    return ALIASES.get(key.lower(), key)


def list_models() -> list[dict[str, Any]]:
    """Return a copy so callers cannot mutate the catalog."""
    return [dict(m) for m in MODELS]
