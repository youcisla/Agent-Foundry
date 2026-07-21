## GitHub Packages mirror

Publishing to GitHub Packages (`https://npm.pkg.github.com/@youcisla`) has
these benefits:

- **Auto-pinned to repo** — the package card appears on the GitHub repo
  sidebar, and the repo shows up as "Package" on your profile
- **No separate auth** — anyone cloning the repo can install via the
  GitHub Packages registry with their `GITHUB_TOKEN`
- **Dual registry** — npmjs.com for general discoverability; GitHub
  Packages for tight repo integration

Users install from npmjs.com:
```bash
npm install -g @youcisla/agent-foundry
```

Or from GitHub Packages (same package, different registry):
```bash
echo "@youcisla:registry=https://npm.pkg.github.com" >> .npmrc
npm install -g @youcisla/agent-foundry
```

## Anti-patterns

- Do NOT set the workflow to auto-publish on push — that would ship every
  WIP commit as a new npm version. Always use `workflow_dispatch`.
- Do NOT share `NPM_TOKEN` across repos — scope it to this package only.
- Do NOT skip quality gates — a broken tarball is worse than no publish.
- Do NOT publish without bumping the version — npm rejects re-publishing
  the same version.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `npm publish` 403 | NPM_TOKEN missing or wrong scope. Regenerate at npmjs.com/tokens |
| `npm publish` 404 on GitHub Packages | `packages: write` permission missing in workflow |
| `npm publish --dry-run` includes __pycache__ | Run `npm pack --dry-run` locally first |
| Git push fails after bump | `git push origin main --tags` needs `contents: write` permission |
| GitHub Packages version out of sync | The dual-publish steps both run; check the log for the GitHub Packages step |
