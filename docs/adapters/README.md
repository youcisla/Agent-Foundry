# Harness adapters

The canonical matrix, paths, and dos/don'ts live in
[harness-compatibility.md](../harness-compatibility.md).

Status values:

| Status | Meaning |
| --- | --- |
| ✅ tested | Installer verified and the harness loaded the skills in a real session |
| ◐ beta | Installer verified against current vendor docs; harness load not yet exercised |
| ○ coming-soon | No working adapter |

## What "tested" means

1. The installer creates the documented layout without error.
2. The harness discovers the skills on next start.
3. The indexer reads the installed tree and produces a valid `SkillIndex`.

Items 1 and 3 are covered by the installer's `--dry-run` and the unit tests.
Item 2 requires a live harness session; until then the adapter stays `beta`.
