import { test, expect } from '../fixtures';
import type { Page } from '@playwright/test';
import { createServer, IncomingMessage, ServerResponse } from 'node:http';
import { DashboardPage } from '../analysis/analysis-page';
import { sseChunk } from '../api-mocks';

/**
 * Local fake SSE backend for /evaluate-bulk. It streams one line every ~250ms
 * with the exact framing the real backend uses (see backend stream.py), so the
 * queue is visible on the dashboard while the run is in-flight — and no real
 * /evaluate-bulk call (LLM / Sectors credits) is ever made.
 *
 * Playwright route fulfill() buffers the whole body, which destroys SSE timing,
 * so the app's fetch() is patched (addInitScript) to hit this server directly
 * instead. CORS is handled; the stream stays open until bulk_complete so UI
 * state can be asserted before the dashboard navigates to /history.
 */
async function startBulkFakeBackend(): Promise<{ url: string; close: () => Promise<void> }> {
  const narratives = [
    'UNVR stock has dropped 15% in a week, investors are panicking.',
    'UNVR stock has dropped 15% in a week, investors are panicking.',
  ];
  const CORS = { 'Access-Control-Allow-Origin': '*' };
  const server = createServer((req: IncomingMessage, res: ServerResponse) => {
    if (req.method === 'OPTIONS') {
      res.writeHead(204, {
        ...CORS,
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      });
      res.end();
      return;
    }
    if (req.method === 'POST' && (req.url || '').endsWith('/evaluate-bulk')) {
      res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        ...CORS,
      });
      (async () => {
        await sleep(150);
        res.write(sseChunk('bulk_started', { total: narratives.length }));
        for (let i = 0; i < narratives.length; i++) {
          await sleep(600);
          res.write(bulkItemStarted(i, narratives.length, narratives[i]));
          await sleep(600);
          const status = i === 0 ? 'completed' : 'duplicate';
          const extra = i === 0 ? { claim_id: 'c1', verdict: 'supported', score: 78 } : { claim_id: 'c1' };
          res.write(bulkItemCompleted(i, narratives.length, status, extra));
        }
        await sleep(150);
        res.write(sseChunk('bulk_complete', { processed: 1, failed: 0 }));
        res.end();
      })().catch(() => res.end());
      return;
    }
    res.writeHead(404, { ...CORS, 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ detail: 'not found' }));
  });
  await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve));
  const address = server.address();
  const port = typeof address === 'object' && address ? address.port : 0;
  return {
    url: `http://127.0.0.1:${port}`,
    close: () => new Promise<void>((resolve) => server.close(() => resolve())),
  };
}

function bulkItemStarted(index: number, total: number, narrative: string): string {
  return sseChunk('bulk_item_started', { index, total, narrative });
}
function bulkItemCompleted(index: number, total: number, status: string, extra = {}): string {
  return sseChunk('bulk_item_completed', { index, total, status, ...extra });
}
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

test.describe('Scanner single/bulk dashboard', () => {
  let fakeBackend: { url: string; close: () => Promise<void> } | undefined;

  test.afterAll(async () => {
    await fakeBackend?.close();
  });

  test.beforeEach(async ({ page }) => {
    fakeBackend = await startBulkFakeBackend();
    // Route the app's bulk SSE fetch to the local fake backend.
    await page.addInitScript(
      ({ url }) => {
        const orig = window.fetch;
        window.fetch = (input: any, init?: RequestInit): Promise<Response> => {
          const u = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
          try {
            if (u.includes('/api/v1/stream/evaluate-bulk')) {
              const path = new URL(u, location.origin).pathname;
              return orig(`${url}${path}`, { ...init, mode: 'cors' });
            }
          } catch {
            /* keep original */
          }
          return orig(input, init);
        };
      },
      { url: fakeBackend.url },
    );

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
      const tiles = page.locator('.examples__card');
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
      await expect(page.locator('.examples__card')).toHaveCount(0);

      const field = page.locator('textarea.input-section__field');
      await field.fill(
        'UNVR stock has dropped 15% in a week, investors are panicking.\n' +
        'UNVR stock has dropped 15% in a week, investors are panicking.',
      );
      await page.click('button.input-section__btn');

      // The fake backend streams one line every 250ms, so the queue is visible
      // while the run is in-flight: first line completes, the repeated second
      // line is flagged as a duplicate.
      const items = page.locator('.bulk__item');
      await expect(items).toHaveCount(2, { timeout: 5_000 });
      await expect(items.nth(0).locator('.bulk__item-status')).toContainText(/done|selesai/);
      await expect(items.nth(1).locator('.bulk__item-status')).toContainText(/duplicate|duplikat/);
      await expect(page.locator('.bulk__progress')).toContainText('2/2');
    });
});