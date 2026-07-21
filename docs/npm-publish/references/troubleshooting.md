# npm publish troubleshooting

Common errors and fixes when running `bash scripts/publish.sh` or
`npm publish`.

## E403 Forbidden — 2FA required

```
npm error code E403
npm error 403 Forbidden - PUT https://registry.npmjs.org/agent-foundry
  - Two-factor authentication or granular access token with bypass 2fa
    enabled is required to publish packages.
```

**Fix:** Enable 2FA or set a granular token. See `2fa-setup.md`.

## EOTP — OTP expired

```
npm error code EOTP
npm error This operation requires a one-time password (OTP).
```

**Fix:** TOTP codes expire every 30 seconds. Re-run and enter the current
code from your authenticator app. For CI, set `NPM_CONFIG_OTP` immediately
before calling `npm publish`.

## ENEEDAUTH — not logged in

```
npm error code ENEEDAUTH
npm error need auth This command requires you to be logged in.
```

**Fix:**
```bash
npm login
# Or set a token:
npm config set //registry.npmjs.org/:_authToken=npm_xxx
```

## Version already exists

```
npm error code E403
npm error 403 You cannot publish over the previously published versions:
npm error 403 [agent-foundry@0.3.0]
```

**Fix:** Bump the version. `npm version patch --no-git-tag-version`.

## Tarball too big / contains junk

```
npm notice package size: 850 kB
```

**Fix:** Check `package.json#files[]` and `.npmignore`. Common offenders:
- `__pycache__/*.pyc` — should be excluded
- `node_modules/` — should be excluded
- `plans/`, `catalog/` — internal, not for users
- `web/demo/*/renders/` — HyperFrames output, regenerable
- `graphify-out/` — graph data, regenerable

Run `npm pack --dry-run` to inspect what would ship.

## Working tree dirty

```
  ⚠ working tree is dirty:
  M  package.json
```

**Fix:** `git status` → commit or stash before publishing.

## Quality gates fail

```
✗ validate: 1 failed
✗ foundry-eval: 2 failed
```

**Fix:** Fix the errors before publishing. Broken publishes are worse
than no publish — they ship broken tarballs to every user.

## Permission denied (hooks/post-commit)

```
bash: .git/hooks/post-commit: Permission denied
```

**Fix (Unix):**
```bash
chmod +x .git/hooks/post-commit
```

**Fix (Windows):** git-bash should respect `chmod +x`. If not, run the
hook logic manually:
```bash
bash .git/hooks/post-commit
```

## Token revoked / 401

```
npm error code E401
npm error 401 Unauthorized - You must be logged in to publish packages.
```

**Fix:** Regenerate the granular token:
1. https://www.npmjs.com/settings/youraccount → Tokens
2. Generate new token (Publish scope)
3. `npm config set //registry.npmjs.org/:_authToken=npm_xxx`

## Hook prints reminder but you don't want to publish

The post-commit hook is **advisory** — it never auto-publishes. To
silence the reminder, just don't run `bash scripts/publish.sh`. The
reminder is a one-time notice after each commit; it doesn't accumulate.

If you want to disable the hook entirely:
```bash
chmod -x .git/hooks/post-commit
# or
mv .git/hooks/post-commit .git/hooks/post-commit.disabled
```

## "Cannot publish over previously published version"

npm forbids re-publishing a version that's already on the registry. This
is intentional — every version must be unique and immutable.

**Fix:** Bump the version:
```bash
npm version patch --no-git-tag-version   # 0.3.0 → 0.3.1
git add package.json
git commit -m "chore: bump v0.3.1"
bash scripts/publish.sh
```