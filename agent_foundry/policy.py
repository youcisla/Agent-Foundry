"""Deterministic action policy.

The gate classifies text, shell, file, and network actions before a caller
acts on them. It is a speed bump, not a sandbox: regex rules can be evaded by
obfuscation. Callers must still use allowlists and least privilege.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

Decision = Literal["allow", "confirm", "deny"]

_PROTECTED_CONFIG = {
    ".eslintrc", ".eslintrc.js", ".eslintrc.cjs", ".eslintrc.json",
    ".eslintrc.yml", ".eslintrc.yaml", "eslint.config.js", "eslint.config.mjs",
    "eslint.config.cjs", "eslint.config.ts", ".prettierrc", ".prettierrc.json",
    ".prettierrc.yml", ".prettierrc.yaml", "prettier.config.js",
    "prettier.config.cjs", ".ruff.toml", "ruff.toml", ".flake8", "tox.ini",
    ".editorconfig", "biome.json", ".stylelintrc", ".stylelintrc.json",
    ".markdownlint.json", ".markdownlintrc",
}

_DESTRUCTIVE_SHELL = [
    (re.compile(r"\brm\s+-(?:[A-Za-z]*r[A-Za-z]*f|[A-Za-z]*f[A-Za-z]*r)\b", re.I),
     "recursive-force-delete"),
    (re.compile(r"\bgit\s+reset\s+--hard\b", re.I), "hard-reset"),
    (re.compile(r"\bgit\s+push\b[^\n]*(?:--force\b|\s-f\b)", re.I), "force-push"),
    (re.compile(r"\bgit\s+clean\s+-[A-Za-z]*f", re.I), "git-clean-force"),
    (re.compile(r"\bmkfs(?:\.[A-Za-z0-9]+)?\b", re.I), "format-filesystem"),
    (re.compile(r"\bdd\s+if=[^\n]*\bof=/dev/", re.I), "raw-disk-write"),
    (re.compile(r"\b(?:shutdown|reboot)\b", re.I), "host-shutdown"),
]

_NETWORK_INSTALL = [
    (re.compile(r"\b(?:curl|wget)\b[^\n|]*\|\s*(?:ba)?sh\b", re.I), "pipe-to-shell"),
    (re.compile(r"\bnpm\s+(?:i|install)\s+-g\b", re.I), "global-npm-install"),
    (re.compile(r"\bpip\s+install\s+(?:https?://|git\+)", re.I), "remote-pip-install"),
]

_SECRET_PATTERNS = [
    ("anthropic-key", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}")),
    ("openai-key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_\-]{20,}")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}")),
    ("github-pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}")),
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]

_INJECTION_PATTERNS = [
    ("ignore-instructions", re.compile(r"\bignore (?:all )?(?:previous|prior|above) instructions?\b", re.I)),
    ("disregard-instructions", re.compile(r"\bdisregard (?:all )?(?:previous|prior|system) (?:instructions?|prompts?)\b", re.I)),
    ("reveal-system-prompt", re.compile(r"\b(?:reveal|print|show) (?:your|the) (?:system )?(?:prompt|instructions)\b", re.I)),
    ("developer-mode", re.compile(r"\bdeveloper mode\b", re.I)),
    ("jailbreak", re.compile(r"\bjailbreak\b", re.I)),
    ("exfiltration", re.compile(r"\bexfiltrat(?:e|ion)\b", re.I)),
    ("send-to-url", re.compile(r"\b(?:send|post|upload) (?:the|all|this) (?:data|content|secrets?) to https?://", re.I)),
    ("hide-from-user", re.compile(r"\bdo not tell the user\b", re.I)),
    ("unrestricted-persona", re.compile(r"\bact as (?:an? )?(?:unrestricted|uncensored)\b", re.I)),
    ("safety-override", re.compile(r"\boverride (?:your|the) (?:safety|system) (?:rules|prompt)\b", re.I)),
    ("new-instructions", re.compile(r"\bnew instructions?:\s", re.I)),
    ("role-reset", re.compile(r"\byou are now (?:dan|developer|unrestricted)\b", re.I)),
]


@dataclass(frozen=True)
class PolicyAction:
    kind: Literal["shell", "file_write", "text", "network"]
    value: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyDecision:
    decision: Decision
    rule_id: str | None
    reason: str
    receipt_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "rule_id": self.rule_id,
            "reason": self.reason,
            "receipt_hash": self.receipt_hash,
        }


def _receipt(action: PolicyAction, decision: Decision, rule_id: str | None) -> str:
    body = {
        "kind": action.kind,
        "value": action.value,
        "decision": decision,
        "rule_id": rule_id,
    }
    return hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _make(action: PolicyAction, decision: Decision, rule_id: str | None,
          reason: str) -> PolicyDecision:
    return PolicyDecision(decision, rule_id, reason, _receipt(action, decision, rule_id))


def _entropy(value: str) -> float:
    if not value:
        return 0.0
    counts: dict[str, int] = {}
    for ch in value:
        counts[ch] = counts.get(ch, 0) + 1
    total = len(value)
    return -sum((n / total) * math.log2(n / total) for n in counts.values())


def _looks_like_secret(token: str) -> bool:
    if len(token) < 32:
        return False
    if re.fullmatch(r"[0-9a-fA-F]+", token):
        return False  # hashes are commonly published; not treated as secrets
    classes = sum((
        bool(re.search(r"[a-z]", token)),
        bool(re.search(r"[A-Z]", token)),
        bool(re.search(r"[0-9]", token)),
        bool(re.search(r"[_\-]", token)),
    ))
    return classes >= 3 and _entropy(token) >= 4.2


def _scan_secrets(text: str) -> list[PolicyDecision]:
    action = PolicyAction("text", text, {"direction": "outbound"})
    found: list[PolicyDecision] = []
    for rule_id, pattern in _SECRET_PATTERNS:
        if pattern.search(text):
            found.append(_make(action, "deny", rule_id,
                               f"secret-like material matched {rule_id}"))
    for token in re.findall(r"[A-Za-z0-9_\-]{32,}", text):
        if _looks_like_secret(token):
            found.append(_make(action, "deny", "high-entropy-token",
                               "high-entropy token resembles a credential"))
            break
    return found


def _scan_injections(text: str) -> list[PolicyDecision]:
    action = PolicyAction("text", text, {"direction": "inbound"})
    return [
        _make(action, "confirm", rule_id,
              f"prompt-injection pattern matched {rule_id}")
        for rule_id, pattern in _INJECTION_PATTERNS
        if pattern.search(text)
    ]


def scan_text(text: str, direction: Literal["inbound", "outbound"] = "inbound") -> list[PolicyDecision]:
    """Return every text risk. Clean text returns an empty list."""
    if direction == "outbound":
        return _scan_secrets(text)
    return _scan_injections(text)


def _check_shell(action: PolicyAction) -> PolicyDecision:
    for pattern, rule_id in _DESTRUCTIVE_SHELL:
        if pattern.search(action.value):
            return _make(action, "confirm", rule_id,
                         f"destructive shell pattern: {rule_id}")
    for pattern, rule_id in _NETWORK_INSTALL:
        if pattern.search(action.value):
            return _make(action, "confirm", rule_id,
                         f"network install pattern: {rule_id}")
    return _make(action, "allow", None, "no shell rule matched")


def _check_file_write(action: PolicyAction) -> PolicyDecision:
    raw = action.value.strip()
    if not raw:
        return _make(action, "deny", "invalid-path", "empty file path")
    path = Path(raw).expanduser()
    workspace = Path(str(action.context.get("workspace") or Path.cwd())).expanduser()
    try:
        workspace = workspace.resolve()
        resolved = (workspace / path).resolve() if not path.is_absolute() else path.resolve()
    except OSError:
        return _make(action, "deny", "invalid-path", "path cannot be resolved")

    if not resolved.is_relative_to(workspace):
        return _make(action, "deny", "path-escape",
                     "path resolves outside the workspace")

    name = resolved.name
    in_ci = ".github" in resolved.parts and "workflows" in resolved.parts
    if (name in _PROTECTED_CONFIG or in_ci) and resolved.exists():
        return _make(action, "deny", "protected-config",
                     "refusing to modify an existing linter, formatter, or CI config")
    return _make(action, "allow", None, "file path allowed")


def _check_network(action: PolicyAction) -> PolicyDecision:
    for pattern, rule_id in _NETWORK_INSTALL:
        if pattern.search(action.value):
            return _make(action, "confirm", rule_id,
                         f"network install pattern: {rule_id}")
    return _make(action, "allow", None, "no network rule matched")


def evaluate(action: PolicyAction) -> PolicyDecision:
    """Classify one action. Unknown kinds fail closed."""
    if action.kind == "shell":
        return _check_shell(action)
    if action.kind == "file_write":
        return _check_file_write(action)
    if action.kind == "network":
        return _check_network(action)
    if action.kind == "text":
        direction = str(action.context.get("direction", "inbound"))
        decisions = scan_text(action.value, "outbound" if direction == "outbound" else "inbound")
        for wanted in ("deny", "confirm"):
            for decision in decisions:
                if decision.decision == wanted:
                    return decision
        return _make(action, "allow", None, "no text rule matched")
    return _make(action, "deny", "invalid-action", f"unknown action kind: {action.kind}")


def worst(decisions: list[PolicyDecision]) -> PolicyDecision | None:
    """Return the highest-severity decision, or None when the list is empty."""
    for wanted in ("deny", "confirm"):
        for decision in decisions:
            if decision.decision == wanted:
                return decision
    return decisions[0] if decisions else None
