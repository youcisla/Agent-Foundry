# Workflow: CI/CD with Vercel Preview + Production

A reusable runbook for shipping web code via Vercel with safe rollback.

## When to Use

- Web app deployed to Vercel
- Need preview deploys on every PR
- Need one-click rollback to last known-good

## Steps

### 1. Setup (one-time)

```bash
# Link the project
vercel link

# Get the project ID and team ID
cat .vercel/project.json
```

Set in GitHub repo settings → Secrets:
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

### 2. Preview on Every PR

`.github/workflows/preview.yml`:

```yaml
name: Vercel Preview
on: [pull_request]
jobs:
  preview:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22 }
      - run: pnpm install --frozen-lockfile
      - run: pnpm typecheck
      - run: pnpm test
      - uses: actions/checkout@v4
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          github-comment: true
```

PR comments show the preview URL. Reviewers click → see the live deploy.

### 3. Production on Merge to Main

`.github/workflows/production.yml`:

```yaml
name: Vercel Production
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

### 4. Smoke Tests After Deploy

`.github/workflows/smoke.yml`:

```yaml
name: Post-Deploy Smoke
on:
  workflow_run:
    workflows: ["Vercel Production"]
    types: [completed]
jobs:
  smoke:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: ubuntu-latest
    steps:
      - run: |
          curl -fsS https://your-app.vercel.app/health | jq -e '.status == "ok"'
          curl -fsS https://your-app.vercel.app/api/ping
```

### 5. Rollback

```bash
# List recent deployments
vercel ls

# Promote a previous deployment to production
vercel promote <deployment-url>
```

Or in Vercel dashboard → Deployments → click "Promote to Production" on the last known-good.

## Verification Checklist

- [ ] Preview deploys trigger on PR open
- [ ] Preview comments show up in PR
- [ ] Production deploys on merge to main
- [ ] Smoke test runs after prod deploy
- [ ] Rollback procedure documented
- [ ] Secrets set in repo
- [ ] Health check endpoint exists
