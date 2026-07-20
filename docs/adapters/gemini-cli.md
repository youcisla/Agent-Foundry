# Gemini CLI integration for Agent Foundry.

Gemini CLI (https://github.com/google-gemini/gemini-cli) does not have a
formal plugin manifest. Skills are added by symlinking this repo's
`skills/` directory into Gemini's skill location.

After running `bash scripts/install.sh --harness=gemini-cli`, the skills
are linked to `~/.gemini/skills/agent-foundry/`. Verify with:

  ls ~/.gemini/skills/agent-foundry/core/ | head

If you do not see 30 skills, file an issue. The install path is the
only stable surface today.

NOTE: this adapter is documented but NOT end-to-end tested. The agent
that built this site (2026-07-20) did not have Gemini CLI installed.
Do not advertise Gemini as a "tested harness" in marketing.
