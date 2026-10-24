"""Task-type verifier registry.

A deterministic verifier runs before a paid judge. A definitive result can
skip the judge; an unknown result falls through to it.
"""
from __future__ import annotations

from typing import Any, Callable, Literal

from .executor import schema_errors

VerifierVerdict = Literal["pass", "fail", "unknown"]
Verifier = Callable[[Any, dict], VerifierVerdict]

_REGISTRY: dict[str, Verifier] = {}


def register(name: str, verifier: Verifier) -> None:
    _REGISTRY[name] = verifier


def get(name: str) -> Verifier | None:
    return _REGISTRY.get(name)


def verify_schema(value: Any, spec: dict) -> VerifierVerdict:
    schema = spec.get("schema")
    if not isinstance(schema, dict):
        return "unknown"
    return "fail" if schema_errors(value, schema) else "pass"


register("json_schema", verify_schema)


def run(name: str, value: Any, spec: dict) -> VerifierVerdict:
    verifier = get(name)
    if verifier is None:
        return "unknown"
    try:
        return verifier(value, spec)
    except Exception:
        return "unknown"
