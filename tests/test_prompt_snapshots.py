import json
import os
import unittest
from pathlib import Path

from agent_foundry.executor import _with_schema, build_messages

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOTS = Path(__file__).resolve().parent / "snapshots" / "prompts"
SKILL_PATHS = {
    "api-design": str(ROOT / "skills" / "core" / "api-design" / "SKILL.md"),
}
SCHEMA = {
    "type": "object",
    "required": ["answer"],
    "properties": {"answer": {"type": "string"}},
}


def _render(case: str) -> str:
    if case == "skill":
        messages, _ = build_messages("api-design", "design a payments API",
                                     SKILL_PATHS)
    elif case == "fallback":
        messages, _ = build_messages("generic-reasoning", "hello", {})
    elif case == "schema":
        messages, _ = build_messages("api-design", "return JSON", SKILL_PATHS)
        messages = _with_schema(messages, SCHEMA)
    else:
        raise AssertionError(case)
    return json.dumps(messages, ensure_ascii=False, indent=2) + "\n"


class PromptSnapshotTests(unittest.TestCase):
    """Byte-exact prompt assembly. A one-space change must fail."""

    def test_snapshots(self):
        SNAPSHOTS.mkdir(parents=True, exist_ok=True)
        update = os.environ.get("UPDATE_PROMPT_SNAPSHOTS") == "1"
        for case in ("skill", "fallback", "schema"):
            path = SNAPSHOTS / f"{case}.json"
            rendered = _render(case)
            if update:
                path.write_text(rendered, encoding="utf-8")
                continue
            self.assertTrue(path.exists(), f"missing snapshot {path}; run with UPDATE_PROMPT_SNAPSHOTS=1")
            self.assertEqual(path.read_text(encoding="utf-8"), rendered,
                             f"prompt drift in {case}")
