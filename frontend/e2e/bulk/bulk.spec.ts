import { test, expect } from '@playwright/test';
import { DashboardPage } from '../analysis/analysis-page';

test.describe('Scanner single/bulk dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // The bulk endpoint is served by the local fake backend with per-item
    // delays — no real /evaluate-bulk calls, so no API credits are spent.
    await page.route('**/api/v1/claims/summary', route => route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ total_analyses: 0, average_score: 0, verdict_distribution: {}, by_ticker: {} }),
    }));
    await page.route('**/api/v1/claims', route => route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: '[]',
    }));
  });

  test('@BULK-E2E-001 single mode shows 12 curated tiles; bulk mode dedups a repeated line',
    { tag: ['@high', '@e2e', '@dashboard'] },
    async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();

      // Single mode: one region, merge of the old two forms, still 12 curated tiles.
      const tiles = page.locator('.input-section__example-card');
      await expect(tiles).toHaveCount(12);
      await expect(dashboard.analyzeButton).toBeVisible();

      // Edge coverage is discoverable, whatever the UX language (en/id tags).
      await expect(tiles.filter({ hasText: /Policy|Kebijakan/ })).toHaveCount(3);
      await expect(tiles.filter({ hasText: /Needs ticker|Butuh kode/ })).toHaveCount(1);
      await expect(tiles.filter({ hasText: /Contradiction|Kontradiksi/ })).toHaveCount(1);

      // A tile click fills the shared textarea (same ticker in both languages).
      await tiles.filter({ hasText: 'BBRI' }).click();
      await expect(page.locator('textarea.input-section__field')).toHaveValue(/BBRI/);

      // Switch to bulk mode on the same textarea; no tiles in bulk mode.
      await page.click('[data-mode="bulk"]');
      await expect(page.locator('.input-section__example-card')).toHaveCount(0);

      const field = page.locator('textarea.input-section__field');
      await field.fill(
        'UNVR stock has dropped 15% in a week, investors are panicking.\n' +
        'UNVR stock has dropped 15% in a week, investors are panicking.',
      );
      await page.click('button.input-section__btn');

      // The fake backend streams one line every 250ms, so the queue is visible
      // before the run completes and the dashboard navigates to /history.
      const items = page.locator('.bulk__item');
      await expect(items).toHaveCount(2, { timeout: 5_000 });
      await expect(items.nth(0).locator('.bulk__item-status')).toContainText(/done|selesai/);
      await expect(items.nth(1).locator('.bulk__item-status')).toContainText(/duplicate|duplikat/);
      await expect(page.locator('.bulk__progress')).toContainText('2/2');
    });
});