"""Small phase timer used by executor and loop responses."""
from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator


class PhaseTimer:
    """Collect inclusive phase durations in milliseconds."""

    def __init__(self) -> None:
        self._phases: dict[str, float] = {}
        self._stack: list[tuple[str, float]] = []

    def __enter__(self) -> "PhaseTimer":
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    @contextmanager
    def phase(self, name: str) -> Iterator[None]:
        start = time.perf_counter()
        self._stack.append((name, start))
        try:
            yield
        finally:
            _, started = self._stack.pop()
            elapsed = (time.perf_counter() - started) * 1000.0
            self._phases[name] = round(self._phases.get(name, 0.0) + elapsed, 3)

    @property
    def phases(self) -> dict[str, float]:
        return dict(self._phases)
