"""Deterministic provider stubs for tests.

A stubbed provider must never let an accidental real call pass silently.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


def _canonical(messages: list[dict]) -> str:
    return json.dumps(
        [{"role": m.get("role"), "content": m.get("content")} for m in messages],
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    )


@dataclass
class CompletionStub:
    prefix: str = "OK:"
    text: str | None = None
    tokens: int = 7
    cost: float = 0.001

    def __call__(self, messages, **kwargs):
        if self.text is not None:
            body = self.text
        else:
            body = self.prefix + hashlib.sha256(
                _canonical(messages).encode("utf-8")
            ).hexdigest()[:12]
        return body, self.tokens, self.cost, {
            "prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7,
        }


class RaisingCompletion:
    """Installed in place of a provider to make an accidental call fail loudly."""

    def __call__(self, *args, **kwargs):
        raise AssertionError("real provider call attempted in a test")
