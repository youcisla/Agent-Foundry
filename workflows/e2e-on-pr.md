# Workflow: E2E Tests on Every PR

A reusable runbook for running Playwright E2E tests on every pull request, with flake mitigation.

## When to Use

- Web app with critical user flows to protect
- Want to catch regressions before merge
- Already have Playwright installed and configured

## Steps

### 1. Setup (one-time)

```bash
pnpm add -D @playwright/test
npx playwright install --with-deps chromium
```

Create `playwright.config.ts`:

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 4 : undefined,
  reporter: process.env.CI ? 'github' : 'list',
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  webServer: {
    command: 'pnpm dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
```

### 2. Write a Critical-Flow Test

`e2e/signup.spec.ts`:

```typescript
import { test, expect } from '@playwright/test';

test('new user can sign up and reach the dashboard', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('link', { name: 'Sign up' }).click();
  await page.getByLabel('Email').fill(`test-${Date.now()}@example.com`);
  await page.getByLabel('Password').fill('correct-horse-battery-staple');
  await page.getByRole('button', { name: 'Create account' }).click();
  await expect(page).toHaveURL(/dashboard/);
  await expect(page.getByRole('heading', { name: 'Welcome' })).toBeVisible();
});
```

### 3. GitHub Action

`.github/workflows/e2e.yml`:

```yaml
name: E2E
on: [pull_request]
jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22 }
      - run: pnpm install --frozen-lockfile
      - run: pnpm exec playwright install --with-deps chromium
      - run: pnpm exec playwright test
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
```

### 4. PR Comment with Results

Add to the action:

```yaml
      - uses: dawidd6/action-comment-pull-request@v1
        if: always()
        with:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          filePath: playwright-report/index.html
```

### 5. Run Locally First

```bash
pnpm exec playwright test --ui    # interactive mode
pnpm exec playwright test          # headless
pnpm exec playwright show-report   # see last run
```

## Flake Mitigation

If a test flakes:
1. Check `playwright-report/` for trace
2. Look for `await` without proper waits
3. Add `await expect(element).toBeVisible()` instead of `sleep()`
4. If unfixable, add `test.fixme()` and open an issue

## Verification Checklist

- [ ] Playwright installed and configured
- [ ] At least 3 critical flows covered
- [ ] Tests run in parallel (4+ workers in CI)
- [ ] Retries enabled (2 in CI)
- [ ] Traces uploaded on failure
- [ ] PR comment shows results
- [ ] Total runtime <10 min
