"""Private full-output spill.

Inline responses stay bounded; the full text is persisted and referenced.
Best-effort: a spill failure must never fail the model call.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path


def default_spill_root() -> Path:
    """AF_SPILL_DIR > AF_CACHE_DIR/artifacts > config-dir artifacts."""
    explicit = os.environ.get("AF_SPILL_DIR")
    if explicit:
        return Path(explicit).expanduser()
    cache = os.environ.get("AF_CACHE_DIR")
    if cache:
        return Path(cache).expanduser() / "artifacts"
    return Path.home() / ".config" / "agent-foundry" / "artifacts"


def _session_dir(root: Path, session_id: int | str | None) -> Path:
    key = hashlib.sha256(str(session_id or "direct").encode("utf-8")).hexdigest()[:16]
    path = root / f"session-{key}"
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


def save_output(root: Path, *, session_id: int | str | None,
                execution_id: int | str, text: str) -> str | None:
    """Persist text atomically, return the path. None on any failure."""
    if not text:
        return None
    try:
        directory = _session_dir(Path(root), session_id)
        name = f"{execution_id}.txt"
        final = directory / name
        tmp = directory / f".{name}.tmp"
        fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, final)
        finally:
            if tmp.exists():
                try:
                    tmp.unlink()
                except OSError:
                    pass
        return str(final)
    except OSError:
        return None


def read_output(ref: str | None) -> str | None:
    if not ref:
        return None
    try:
        return Path(ref).read_text(encoding="utf-8")
    except OSError:
        return None


def preview(text: str, limit: int) -> str:
    return text[:limit] if limit and limit > 0 else text
