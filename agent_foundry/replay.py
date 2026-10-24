"""Canonical run identity: trace digest and request metadata.

The digest is bit-exact: same skill bytes, messages, model chain, sampling
parameters, schema, and output must produce the same string. Timestamps and
durations are deliberately excluded.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from functools import lru_cache
from typing import Any

from . import __version__

DIGEST_VERSION = 1


@lru_cache(maxsize=1)
def runtime_version() -> str:
    return __version__


@lru_cache(maxsize=1)
def git_sha() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=2, check=False,
        )
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=2, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    if out.returncode != 0:
        return ""
    sha = out.stdout.strip()
    return f"{sha}-dirty" if status.returncode == 0 and status.stdout.strip() else sha


def canonical_messages(messages: list[dict]) -> list[dict]:
    """Keep only role/content pair order; drop provider-only keys."""
    return [
        {"role": str(m.get("role", "")), "content": m.get("content", "")}
        for m in messages
    ]


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def trace_digest(
    *,
    skill_id: str,
    skill_sha256: str,
    models: list[str],
    messages: list[dict],
    output: str,
    schema: dict | None = None,
    seed: int | None = None,
    temperature: float | None = None,
) -> str:
    body = {
        "v": DIGEST_VERSION,
        "runtime": runtime_version(),
        "skill_id": skill_id,
        "skill_sha256": skill_sha256,
        "models": list(models),
        "seed": seed,
        "temperature": temperature,
        "messages": canonical_messages(messages),
        "schema": schema,
        "output": output,
    }
    return hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


def request_metadata(
    *,
    skill_id: str,
    skill_sha256: str,
    models: list[str],
    messages: list[dict],
    schema: dict | None = None,
    seed: int | None = None,
    temperature: float | None = None,
    constraint_kind: str | None = None,
    enforced_by: str | None = None,
) -> dict[str, Any]:
    """Everything needed to reconstruct the request, minus the output."""
    return {
        "digest_version": DIGEST_VERSION,
        "runtime_version": runtime_version(),
        "git_sha": git_sha(),
        "skill_id": skill_id,
        "skill_sha256": skill_sha256,
        "models": list(models),
        "seed": seed,
        "temperature": temperature,
        "schema": schema,
        "constraint_kind": constraint_kind,
        "enforced_by": enforced_by,
        "messages_sha256": hashlib.sha256(
            canonical_json(canonical_messages(messages)).encode("utf-8")
        ).hexdigest(),
        "message_roles": [m.get("role") for m in messages],
        "message_chars": [len(str(m.get("content", ""))) for m in messages],
    }


def run_config(
    *,
    skill_id: str,
    models: list[str],
    seed: int | None,
    temperature: float | None,
    schema: dict | None,
) -> dict[str, Any]:
    return {
        "runtime_version": runtime_version(),
        "git_sha": git_sha(),
        "skill_id": skill_id,
        "models": list(models),
        "seed": seed,
        "temperature": temperature,
        "schema_sha256": (
            hashlib.sha256(canonical_json(schema).encode("utf-8")).hexdigest()
            if schema is not None else None
        ),
    }
