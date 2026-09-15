import { test, expect } from '../fixtures';
import { DashboardPage, ClaimPage, ResultsPage } from './analysis-page';
import { successStream, clarificationStream, claimState } from '../api-mocks';

test.describe('Analysis edge cases', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/v1/stream/evaluate', route => route.fulfill({
      status: 200,
      contentType: 'text/event-stream',
      body: successStream('new-claim', 'default'),
    }));
  });

  test('@ANALYSIS-E2E-001 narrative without a ticker halts before evidence',
    { tag: ['@critical', '@e2e', '@analysis'] },
    async ({ page }) => {
      const dashboard = new DashboardPage(page);
      const claim = new ClaimPage(page);

      await page.route('**/api/v1/stream/evaluate', route => route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: clarificationStream('clarify-claim', 'Saham perbankan mahal'),
      }));

      await dashboard.goto();
      // Scrolling down then analyzing must land the claim page at the top.
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await dashboard.analyze('Saham perbankan mahal');
      await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0);

      await claim.expectClarificationShown();
    });

  test('@ANALYSIS-E2E-002 stuck "parsed" claim retry runs a fresh analysis',
    { tag: ['@high', '@e2e', '@analysis'] },
    async ({ page }) => {
      const results = new ResultsPage(page);

      await page.route('**/api/v1/claims/stuck-claim', route => route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(claimState()),  // status: 'parsed' -> "Still Processing"
      }));
      await page.route('**/api/v1/claims/new-claim', route => route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(claimState({
          claim_id: 'new-claim',
          status: 'completed',
          updated_at: '2026-09-08T08:00:00.000000',
          score: { reality_gap_score: 72, verdict: 'supported', explanation: 'ok', dimensions: {} },
        })),
      }));
      await page.route('**/api/v1/claims/new-claim/suggestions', route => route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          claim_id: 'new-claim',
          suggestions: [
            { id: 's1', text: 'Kenapa skornya 72?', text_en: 'Why is the score 72?' },
            { id: 's2', text: 'Bukti apa yang menguatkan verdict?', text_en: 'What evidence supports the verdict?' },
          ],
          cached: false,
        }),
      }));

      await results.goto('stuck-claim');
      await results.expectStillProcessing();

      await results.retry();

      // A fresh, complete pipeline run lands on the new completed claim.
      const claim = new ClaimPage(page);
      await claim.waitForCompletionRedirect();
      await results.expectCompleted();
      await results.expectContextualSuggestions();
    });
});