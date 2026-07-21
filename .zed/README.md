# Agent Foundry — Zed Adapter

**Status:** Coming soon — Zed's agent client (zquire) is in beta and lacks a
stable plugin API. We document the expected layout but won't ship a tested
adapter until the upstream API stabilizes.

## Expected layout

```
.zed/
  settings.json
  commands/
    af.md
  agents/
    af-critic.md
```

## Install

```bash
node scripts/install.js --harness=zed
# Will print the layout but copy nothing until upstream ships.