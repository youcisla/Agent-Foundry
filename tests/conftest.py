"""Shared test isolation: reset module-level state and env between tests."""
from __future__ import annotations

import os

import pytest

_ENV_PREFIXES = ("AGENT_FOUNDRY_", "AF_")


@pytest.fixture(autouse=True)
def _reset_runtime_state(monkeypatch):
    """Kill order dependence: module caches, env overrides, budget state."""
    saved = {k: v for k, v in os.environ.items()
             if k.startswith(_ENV_PREFIXES)}
    try:
        from agent_foundry import indexer
        indexer.invalidate_cache()
    except Exception:
        pass
    yield
    for key in list(os.environ):
        if key.startswith(_ENV_PREFIXES):
            os.environ.pop(key, None)
    os.environ.update(saved)
