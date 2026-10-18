# Harness adapters

The canonical matrix, paths, and dos/don'ts live in
[harness-compatibility.md](../harness-compatibility.md).

All 14 adapters are **tested**. `scripts/test-install.js` runs every target in
a throwaway home and asserts:

1. The installer creates the documented layout without error.
2. All 39 skills are direct children of the harness's discovery root.
3. The indexer reads the installed tree and produces a valid `SkillIndex`.

Claude Code, Hermes, and OpenClaw also loaded the skills in a live session.
Run the full matrix with:

```bash
node scripts/test-install.js
python scripts/smoke-test.py claude-code
```
