---
name: npm-publish
description: "Publish the Agent Foundry package to npm. Use when finishing a feature that should ship a new version, when scripts/install.js, skills/, agents/, or harness adapter files change, or when running the release flow."
version: 0.1.0
author: Agent Foundry Contributors
---

# npm-publish

Full release flow for the Agent Foundry npm package. Pre-flight checks,
dry-run, version bump, publish, and tag. Handles 2FA prompts.

## When to use

- After committing changes to `package.json`, `scripts/`, `skills/`,
  `agents/`, or any harness adapter dir (`.codex/`, `.cursor/`, etc.)
- When local version differs from the published version
- The git post-commit hook fires a reminder when this skill applies

## Quick path

```bash
bash scripts/publish.sh                 # bump patch + dry-run + publish
bash scripts/publish.sh --no-bump      # publish current version
bash scripts/publish.sh --dry-run      # gates + dry-run only
bash scripts/publish.sh --version=minor  # explicit bump type
```

## Procedure

### 1 - Pre-flight

The script auto-runs these checks; fail-fast if any fail:

```bash
node -v                              # Node 18+
npm -v                               # npm 9+
npm whoami                           # must succeed; if not, run `npm login`
git status --short                   # must be empty
```

If `npm whoami` returns `ENEEDAAUTH`:
- Run `npm login` (opens browser for OTP)
- If 2FA isn't enabled, see `references/2fa-setup.md`

### 2 - Quality gates

`scripts/publish.sh` runs all three before publishing:
- `bash scripts/validate.sh` — 31 skills, no syntax errors
- `python scripts/foundry-eval.py` — 33+ checks pass
- `bash scripts/nox.sh` — 0 external references in tracked files

### 3 - Bump version

| Change | Bump |
|---|---|
| Bug fixes, copy edits, new skill/agent | patch (0.3.0 → 0.3.1) |
| New harness adapters, breaking install | minor (0.3.0 → 0.4.0) |
| Complete rewrite | major (rare) |

The script uses `npm version <bump> --no-git-tag-version` then commits
the bump so the publish picks up the new version.

### 4 - Dry-run

`scripts/publish.sh` always runs `npm publish --dry-run` first. Expected
output: 77 files, ~76 KB tarball, no `__pycache__/`, no `plans/`, no
`web/demo/*/renders/`. All 31 `SKILL.md` files present. All 3 `AGENT.md`
files present. All 4 install scripts (`install.{js,sh,bat,ps1}`).

### 5 - Publish

```bash
npm publish --access public
# If 2FA enabled, npm prompts for the 6-digit TOTP code.
```

For CI/non-interactive: set `NPM_CONFIG_OTP=123456` and the script will
pass it via `--otp`.

### 6 - Tag + verify

The script auto-tags with `git tag -a vX.Y.Z` and pushes. Verify:

```bash
npm view agent-foundry version
npm install -g agent-foundry@X.Y.Z
agent-foundry --list    # shows 14 harnesses
```

## Anti-patterns

- Do NOT publish from a dirty working tree — always commit first
- Do NOT skip the 2FA prompt or hardcode OTP in shell history
- Do NOT reuse a published version — npm rejects re-publishing same version
- Do NOT publish without running all three quality gates
- Do NOT ship `__pycache__/`, `node_modules/`, `plans/`, or `catalog/`
  in the tarball — `package.json#files` + `.npmignore` handle this

## See also

- `references/2fa-setup.md` — How to enable 2FA on npmjs.com (mandatory
  for publishing public packages since npm 2024 security update)
- `references/troubleshooting.md` — Common publish errors (E403, ENEEDAUTH,
  EOTP, version conflicts)
- `scripts/publish.sh` — The full automated script (source of truth)