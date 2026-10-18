"""Local attestation for installed skill manifests.

Uses HMAC-SHA256 with a per-user key. This detects accidental modification,
stale installs, and casual tampering. It is not a signature scheme and does
not defend against an attacker who can read the user's key.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MANIFEST_NAME = ".agent-foundry-installed.json"
SIG_SUFFIX = ".sig"
KEY_BYTES = 32
MIN_KEY_BYTES = 16


@dataclass
class VerifyResult:
    """Outcome of one manifest verification."""

    ok: bool
    checked: int = 0
    missing: list[str] = field(default_factory=list)
    mismatched: list[str] = field(default_factory=list)
    unsigned: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    manifest_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "checked": self.checked,
            "missing": self.missing,
            "mismatched": self.mismatched,
            "unsigned": self.unsigned,
            "errors": self.errors,
            "manifest_version": self.manifest_version,
        }


def canonical_json(obj: Any) -> bytes:
    """Stable bytes for signing: sorted keys, no whitespace variance."""
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def load_or_create_key(path: Path) -> bytes:
    """Read the attestation key, creating a 0600 file on first use."""
    path = path.expanduser()
    if path.exists():
        key = path.read_bytes()
        if len(key) < MIN_KEY_BYTES:
            raise ValueError(f"attestation key too short: {path}")
        return key
    path.parent.mkdir(parents=True, exist_ok=True)
    key = secrets.token_bytes(KEY_BYTES)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
    try:
        fd = os.open(str(path), flags, 0o600)
    except FileExistsError:
        return path.read_bytes()
    try:
        view = memoryview(key)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError(f"short write creating attestation key: {path}")
            view = view[written:]
    finally:
        os.close(fd)
    return key


def sign_manifest(manifest: dict[str, Any], key: bytes) -> str:
    """HMAC-SHA256 over the manifest with any existing signature removed."""
    body = {k: v for k, v in manifest.items() if k != "signature"}
    return hmac.new(key, canonical_json(body), hashlib.sha256).hexdigest()


def frontmatter_digest(skill_md: Path) -> str:
    """Hash the YAML frontmatter block, normalized to LF line endings."""
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    text = text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")
    if not text.startswith("---\n"):
        return hashlib.sha256(b"").hexdigest()
    end = text.find("\n---", 4)
    if end == -1:
        return hashlib.sha256(b"").hexdigest()
    return hashlib.sha256(text[4:end].encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_entries(root: Path) -> list[dict[str, str]]:
    """Build manifest entries for every direct child skill under root."""
    entries: list[dict[str, str]] = []
    if not root.exists():
        return entries
    now = datetime.now(timezone.utc).isoformat()
    for child in sorted(root.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        skill_md = child / "SKILL.md"
        if not skill_md.is_file():
            continue
        entries.append({
            "name": child.name,
            "sha256": _file_sha256(skill_md),
            "frontmatter_sha256": frontmatter_digest(skill_md),
            "installed_at": now,
        })
    return entries


def attest_root(root: Path, manifest_path: Path, key_path: Path) -> dict[str, Any]:
    """Write a signed v2 manifest for the installed skills under root."""
    root = root.expanduser()
    manifest_path = manifest_path.expanduser()
    key = load_or_create_key(key_path)

    previous: dict[str, Any] = {}
    if manifest_path.exists():
        try:
            previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            previous = {}

    entries = build_entries(root)
    manifest: dict[str, Any] = {
        "package": previous.get("package", "@youcisla/agent-foundry"),
        "repo": previous.get("repo", ""),
        "mode": previous.get("mode", "link"),
        "manifest_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "skills": [e["name"] for e in entries],
        "entries": entries,
    }
    manifest["signature"] = sign_manifest(manifest, key)

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    Path(str(manifest_path) + SIG_SUFFIX).write_text(
        manifest["signature"] + "\n", encoding="utf-8"
    )
    return manifest


def verify_manifest(
    manifest_path: Path,
    key_path: Path,
    *,
    root: Path | None = None,
) -> VerifyResult:
    """Verify signature, skill hashes, and coverage for one manifest."""
    manifest_path = manifest_path.expanduser()
    root = (root or manifest_path.parent).expanduser()
    result = VerifyResult(ok=False)

    if not manifest_path.exists():
        result.errors.append(f"manifest not found: {manifest_path}")
        return result

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        result.errors.append(f"cannot read manifest: {exc}")
        return result

    result.manifest_version = int(manifest.get("manifest_version", 1))
    if result.manifest_version < 2:
        result.errors.append("manifest has no attestation (v1 or older)")
        return result

    signature = str(manifest.get("signature") or "")
    if not signature:
        result.errors.append("manifest signature missing")
        return result

    try:
        key = load_or_create_key(key_path)
    except (OSError, ValueError) as exc:
        result.errors.append(f"cannot load attestation key: {exc}")
        return result

    expected = sign_manifest(manifest, key)
    if not hmac.compare_digest(signature, expected):
        result.errors.append("manifest signature mismatch")
        return result

    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        result.errors.append("manifest has no entries")
        return result

    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            result.errors.append("malformed manifest entry")
            continue
        name = str(entry.get("name") or "")
        if not name:
            result.errors.append("manifest entry missing name")
            continue
        seen.add(name)
        skill_md = root / name / "SKILL.md"
        if not skill_md.is_file():
            result.missing.append(name)
            continue
        result.checked += 1
        if _file_sha256(skill_md) != entry.get("sha256"):
            result.mismatched.append(name)
            continue
        fm_expected = entry.get("frontmatter_sha256")
        if fm_expected and frontmatter_digest(skill_md) != fm_expected:
            result.mismatched.append(name)

    if root.exists():
        for child in root.iterdir():
            if (child.is_dir() and (child / "SKILL.md").is_file()
                    and child.name not in seen):
                result.unsigned.append(child.name)

    result.ok = not (result.missing or result.mismatched or result.unsigned
                     or result.errors)
    return result
