# License ledger

Agent Foundry is MIT-licensed. This ledger records the license status of each
artifact class so a bundled asset never inherits a repository-level assumption.

| Artifact class | License | Notes |
|---|---|---|
| Python package (`agent_foundry/`) | MIT | original work |
| Skills (`skills/`) | MIT | original prose; no copied third-party skill text |
| Agents (`agents/`) | MIT | original work |
| Web site and generated data (`web/`) | MIT | generated from this repository |
| Vendored code | none | no third-party source is vendored |
| Model weights | not distributed | providers serve models under their own terms |

Rule: when a future skill or asset is adapted from an external source, record
its upstream license and attribution in this table before merging.
