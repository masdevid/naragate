import { test, expect } from '../fixtures';

/**
 * Production /history page, real backend — NO mocks, NO writes, zero credits.
 *
 * Verifies the *presented* history & trend view is coherent with the claims the
 * backend actually stores: the list, the aggregate trend summary and each
 * detail page must agree, and every score must sit in its verdict's band.
 *
 * Skips cleanly when the live store has no completed claims yet.
 */

const BAND_OF = (score: number): string =>
  score <= 30 ? 'contradicted' : score <= 60 ? 'mixed' : score <= 80 ? 'supported' : 'strongly_supported';

const VERDICT_LABEL: Record<string, string> = {
  contradicted: 'Bertentangan',
  mixed: 'Campuran',
  supported: 'Didukung',
  strongly_supported: 'Sangat Didukung',
};

test.describe('Production history page (real data)', () => {
  test('@HIST-E2E-001 list, trend summary and detail pages are coherent', async ({ page, request }) => {
    const PAGE_SIZE = 5;
    const all = await (await request.get('/api/v1/claims/?limit=1000')).json();
    const summary = await (await request.get('/api/v1/claims/summary')).json();
    const total = (await (await request.get('/api/v1/claims/count')).json()).total;
    const page1 = await (await request.get(`/api/v1/claims/?limit=${PAGE_SIZE}&offset=0`)).json();
    const completed = all.filter((c: any) => c.status === 'completed' && c.score);
    test.skip(completed.length === 0, 'no completed claims in the live store — run generate-history first');

    // ---- API-level coherence (is the data itself sensible?) ----
    expect(total).toBe(all.length);
    expect(summary.total_analyses).toBe(completed.length);
    const scores = completed.map((c: any) => c.score.reality_gap_score);
    const mean = scores.reduce((a: number, b: number) => a + b, 0) / scores.length;
    expect(summary.average_score).toBeCloseTo(Math.round(mean * 10) / 10, 1);

    const distSum = Object.values(summary.verdict_distribution).reduce((a: any, b: any) => a + b, 0);
    expect(distSum).toBe(summary.total_analyses);
    for (const c of completed) {
      expect(BAND_OF(c.score.reality_gap_score)).toBe(c.score.verdict);
      expect(VERDICT_LABEL[c.score.verdict]).toBeTruthy();
    }

    // ---- Rendered page ----
    await page.goto('/history', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('.history__title')).toBeVisible();

    const rows = page.locator('.recent__item');
    await expect(rows).toHaveCount(page1.length);

    // Pagination appears when there is more than one page, and pages differ.
    if (total > PAGE_SIZE) {
      await expect(page.locator('.recent__pager')).toBeVisible();
      await expect(page.locator('.recent__pager-info')).toContainText(/Halaman 1|Page 1/);
      await page.locator('.recent__pager-btn').last().click();
      await expect(page.locator('.recent__pager-info')).toContainText(/Halaman 2|Page 2/);
      await page.locator('.recent__pager-btn').first().click();
      await expect(page.locator('.recent__item')).toHaveCount(page1.length);
    }

    await expect(page.locator('.trend__count')).toContainText(String(summary.total_analyses));
    await expect(page.locator('.trend__stat-value')).toHaveText(String(summary.average_score));

    for (const [band, count] of Object.entries(summary.verdict_distribution)) {
      const row = page.locator('.trend__dist-row').filter({ has: page.locator(`.badge[data-verdict="${band}"]`) });
      await expect(row.locator('.trend__dist-count')).toHaveText(String(count));
    }

    // No unresolved placeholders leak into the rendered history.
    const historyText = await page.locator('.history').innerText();
    expect(historyText).not.toMatch(/undefined|NaN|\{\{/);

    // Every completed narrative on the current page is listed and labelled "Selesai".
    for (const c of page1.filter((c: any) => c.status === 'completed')) {
      const row = page
        .locator('.recent__item')
        .filter({ has: page.locator('.recent__narrative', { hasText: c.narrative }) })
        .filter({ hasText: 'Selesai' });
      await expect(row.first()).toBeVisible();
    }

    // A failed claim on the page is presented as failed, not completed.
    if (page1.some((c: any) => c.status === 'failed')) {
      await expect(page.locator('.recent__item').filter({ hasText: 'Gagal' }).first()).toBeVisible();
    }

    // ---- Cross-page coherence: clicking a row opens a detail page that agrees ----
    const target = page1.find((c: any) => c.status === 'completed' && c.score);
    test.skip(!target, 'no completed claim on the first page');
    await page
      .locator('.recent__item')
      .filter({ has: page.locator('.recent__narrative', { hasText: target.narrative }) })
      .filter({ hasText: 'Selesai' })
      .first()
      .locator('.recent__main')
      .click();

    await expect(page).toHaveURL(new RegExp(`/results/${target.claim_id}`));
    await expect(page.locator('.results__quote')).toContainText(target.narrative);
    await expect(page.locator('.gauge__value')).toHaveText(String(target.score.reality_gap_score));
    await expect(page.locator('.verdict__text .badge')).toHaveAttribute('data-verdict', target.score.verdict);
    await expect(page.locator('.verdict__text .badge')).toHaveText(VERDICT_LABEL[target.score.verdict]);
    await expect(page.locator('.legend__item--active .legend__name')).toHaveText(VERDICT_LABEL[target.score.verdict]);
    await expect(page.locator('.legend__item--active .legend__swatch')).toHaveAttribute('data-verdict', target.score.verdict);
  });

  test('@HIST-E2E-002 stored policy claims render the policy section, not evidence cards', async ({ page, request }) => {
    const claims = await (await request.get('/api/v1/claims/?limit=1000')).json();
    const policy = claims.filter((c: any) => c.status === 'completed' && c.claim?.is_policy && c.claim?.sector);
    test.skip(policy.length === 0, 'no stored policy claims — run generate-history first');

    for (const c of policy) {
      await page.goto(`/results/${c.claim_id}`, { waitUntil: 'domcontentloaded' });
      await expect(page.locator('.policy')).toBeVisible();
      await expect(page.locator('.policy__verdict')).toHaveText(/.+/);
      await expect(page.locator('app-evidence-card')).toHaveCount(0);
    }
  });
});
