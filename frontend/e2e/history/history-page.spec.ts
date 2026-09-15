import { test, expect } from '@playwright/test';

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
    // Mirror the page's own request (getClaims() uses the backend default limit).
    const claims = await (await request.get('/api/v1/claims/')).json();
    const summary = await (await request.get('/api/v1/claims/summary')).json();
    const completed = claims.filter((c: any) => c.status === 'completed' && c.score);
    test.skip(completed.length === 0, 'no completed claims in the live store — run generate-history first');

    // ---- API-level coherence (is the data itself sensible?) ----
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
    await expect(rows).toHaveCount(claims.length);

    await expect(page.locator('.trend__count')).toContainText(String(summary.total_analyses));
    await expect(page.locator('.trend__stat-value')).toHaveText(String(summary.average_score));

    for (const [band, count] of Object.entries(summary.verdict_distribution)) {
      const row = page.locator('.trend__dist-row').filter({ has: page.locator(`.badge[data-verdict="${band}"]`) });
      await expect(row.locator('.trend__dist-count')).toHaveText(String(count));
    }

    // No unresolved placeholders leak into the rendered history.
    const historyText = await page.locator('.history').innerText();
    expect(historyText).not.toMatch(/undefined|NaN|\{\{/);

    // Every completed narrative is listed and labelled "Selesai"
    // (a narrative can repeat — e.g. a stuck retry — so require at least one).
    for (const c of completed) {
      const row = page
        .locator('.recent__item')
        .filter({ has: page.locator('.recent__narrative', { hasText: c.narrative }) })
        .filter({ hasText: 'Selesai' });
      await expect(row.first()).toBeVisible();
    }

    // The guardrail claim is stored as failed and presented as such.
    const failed = claims.find((c: any) => c.status === 'failed' && c.narrative === 'Saham perbankan sedang mahal.');
    if (failed) {
      const row = page.locator('.recent__item').filter({ hasText: 'Saham perbankan sedang mahal.' });
      await expect(row.locator('.recent__meta')).toContainText('Gagal');
    }

    // ---- Cross-page coherence: clicking a row opens a detail page that agrees ----
    const target = completed[0];
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
    const claims = await (await request.get('/api/v1/claims/')).json();
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
