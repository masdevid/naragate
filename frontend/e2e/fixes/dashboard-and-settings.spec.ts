import { test, expect } from '../fixtures';

/**
 * Regression coverage for the dashboard/settings/connector fixes:
 *  - headline dot removal (en + id)
 *  - LLM connector model count interpolation (was literally "{count}")
 *  - per-IP Sectors enforcement off by default: key already configured is shown
 *    to any IP and setup is complete (no blind redirect / save failure)
 *  - warning banners dedupe: one consolidated banner when setup is incomplete
 *    instead of overlapping stacked full-bleed bands
 */

function dismissSetup(page: import('@playwright/test').Page): void {
  page.addInitScript(() => localStorage.setItem('naragate_setup_dismissed', '1'));
}

function mockEmptySettings(page: import('@playwright/test').Page): void {
  // A fresh/un-configured install: no LLM, no Sectors, setup incomplete.
  void page.route('**/api/v1/settings/status', route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ complete: false, missing: ['sectors_api_key', 'llm_model'] }),
  }));
  void page.route('**/api/v1/settings', route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: '{}',
  }));
  void page.route('**/api/v1/usage', route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ sectors: { budget: 0, remaining: 0 } }),
  }));
}

test.describe('Dashboard fixes', () => {
  test('@FIX-E2E-001 headline renders without a trailing period', async ({ page }) => {
    dismissSetup(page);
    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
    const headline = page.locator('.hero__display');
    await expect(headline).toBeVisible();

    const text = (await headline.textContent())?.trim() ?? '';
    // Ends on the accent word, not on punctuation.
    await expect
      .poll(() => page.locator('.hero__display').textContent(), { timeout: 3_000 })
      .not.toMatch(/\.\s*$/);
    expect(text.endsWith('.')).toBe(false);
    expect(text.length).toBeGreaterThan(10);
  });

  test('@FIX-E2E-004 incomplete setup shows one consolidated warning (no stacked bands)', async ({ page }) => {
    dismissSetup(page);
    mockEmptySettings(page);
    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });

    const warns = page.locator('.warn');
    await expect(warns).toHaveCount(1);
    await expect(warns.first()).toContainText(/setup|mulai/i);
  });
});

test.describe('Settings · Sectors auto-configured', () => {
  test('@FIX-E2E-003 configured sectors key is visible to any IP and setup is complete', async ({ page }) => {
    dismissSetup(page);
    await page.goto('/settings', { waitUntil: 'domcontentloaded' });

    // Real backend: the saved key must resolve for ANY client IP (enforcement off).
    const sectors = page.locator('app-settings-sectors-section');
    await expect(sectors.locator('.sect__heading')).toContainText(/sectors/i);
    // The key renders in the saved (masked) state — bullets + last4.
    await expect(sectors.locator('.secret--saved')).toBeVisible();
    await expect(sectors.locator('.secret--saved')).toContainText(/•/);

    // Owner gating off: the ready state is visible, no error banner from a failed save.
    await expect(page.locator('.settings__save-error')).toHaveCount(0);
  });
});

test.describe('LLM connector model count', () => {
  test('@FIX-E2E-002 status shows an interpolated model count, not the {count} literal', async ({ page }) => {
    dismissSetup(page);
    await page.route('**/api/v1/settings', route => route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        llm_provider: 'custom',
        llm_endpoint: 'https://example.test/v1',
        llm_api_key: 'mk_••••••••••••••••',
        llm_model: '',
      }),
    }));
    await page.route('**/api/v1/settings/validate-llm', route => route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ ok: true, endpoint: 'https://example.test/v1', models: ['model-a', 'model-b'] }),
    }));

    await page.goto('/llm-connector', { waitUntil: 'domcontentloaded' });

    const status = page.locator('.conn__status');
    await expect(status).toContainText(/2\s+model/i);
    await expect(status).not.toContainText('{count}');
  });
});