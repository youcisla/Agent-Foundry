# Workflow: Weekly Release Train

A reusable runbook for shipping a release every week: tag, changelog, deploy, smoke.

## When to Use

- Web app on a weekly release cadence
- Want predictable release days (Tuesday 10am is industry standard)
- Need changelog hygiene

## Steps

### 1. Pre-Release Checklist (Monday)

```markdown
## [release-YYYY-MM-DD] pre-release

- [ ] All PRs merged into main since last release
- [ ] No `wip` or `do-not-merge` branches
- [ ] CI green on main
- [ ] No critical alerts in the last week
- [ ] Database migrations reviewed (if any)
- [ ] Feature flags set correctly (killswitches verified)
```

### 2. Generate Changelog (Monday)

```bash
LAST_TAG=$(git describe --tags --abbrev=0)
echo "## Changes since $LAST_TAG"
echo ""
git log $LAST_TAG..main --pretty=format:"- %s (%h)" --no-merges | head -50
```

Group by:
- ✨ Features
- 🐛 Bug fixes
- ⚡ Performance
- 📝 Documentation

### 3. Tag the Release (Monday afternoon)

```bash
VERSION=$(date +%Y.%m.%d)
git tag -a "v$VERSION" -m "Release $VERSION

$(cat CHANGELOG.md | sed -n '/## Changes/,/## /p' | head -30)"
git push origin "v$VERSION"
```

### 4. Build & Deploy (Tuesday 10am)

```bash
# Trigger production deploy via the CI/CD workflow
gh workflow run production.yml

# Wait for completion
gh run watch
```

### 5. Post-Deploy Smoke (Tuesday 10:30am)

```bash
# Health check
curl -fsS https://your-app.com/health | jq

# Smoke the top 5 user flows manually OR via Playwright
pnpm exec playwright test --grep @smoke
```

### 6. Verify Metrics (Tuesday 11am)

- Activation rate didn't drop
- Error rate stayed below 1%
- New signups still flowing
- No spike in support tickets

If any of these are off:
- Rollback: `vercel promote <previous-deployment>`
- Investigate: `vercel logs <failing-deployment>`
- Communicate: post in #releases with the rollback reason

### 7. Post-Release Notes (Tuesday 4pm)

```markdown
## Shipped: vYYYY.MM.DD

**Top changes:**
- Feature X — brief description, link to docs
- Bug fix Y — what was broken, what's now fixed

**Stats:**
- 47 PRs merged
- 3 contributors
- 0 rollback incidents

**Next week:**
- Focus on Z (link to RFC)
```

Post in:
- Team Slack #releases
- Customer changelog (if you have one)
- Status page (if relevant)

## Cadence

| Day | Task |
|-----|------|
| Monday morning | Pre-release checklist |
| Monday afternoon | Tag release |
| Monday evening | Notify on-call |
| Tuesday 10am | Deploy |
| Tuesday 10:30am | Smoke |
| Tuesday 11am | Metrics check |
| Tuesday 4pm | Post-release notes |

## Anti-patterns

- "We'll tag it whenever we have time" — drift kills cadence
- Skipping smoke tests because "this is a small change"
- Deploying Friday afternoon
- Rollback without investigating the cause first
- No post-release notes (everyone forgets what shipped)
