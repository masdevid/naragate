import { test, expect } from '../fixtures';

/**
 * The MCP/API access section lets a signed-in user mint a per-user token for
 * non-web harnesses, list it (metadata only) and revoke it.
 */
test.describe('Settings · MCP & API access', () => {
  test('@FIX-E2E-006 mint and revoke an API token', async ({ page }) => {
    page.addInitScript(() => localStorage.setItem('naragate_setup_dismissed', '1'));

    const record = {
      id: 'id1', name: 'laptop', prefix: 'nrg_abc123',
      created_at: '2026-09-16T00:00:00.000Z', last_used_at: null,
    };
    let created = false;

    await page.route('**/api/v1/settings/status', route => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ complete: true, missing: [] }),
    }));
    await page.route('**/api/v1/settings', route => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ authenticated: true, email: 'a@example.com' }),
    }));
    await page.route('**/api/v1/auth/tokens', route => {
      if (route.request().method() === 'POST') {
        created = true;
        return route.fulfill({
          status: 200, contentType: 'application/json',
          body: JSON.stringify({ ...record, token: 'nrg_abc123456789', email: 'a@example.com' }),
        });
      }
      return route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ tokens: created ? [record] : [] }),
      });
    });
    await page.route('**/api/v1/auth/tokens/*', route => {
      created = false;
      return route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ status: 'ok' }),
      });
    });

    await page.goto('/settings', { waitUntil: 'domcontentloaded' });
    const section = page.locator('app-settings-mcp-section');
    await expect(section).toBeVisible();

    await section.locator('.sect__input').fill('laptop');
    await section.locator('.sect__btn--accent').click();

    // The raw token is shown exactly once.
    await expect(section.locator('.sect__token')).toContainText('nrg_abc123456789');
    await expect(section.locator('.sect__item-name')).toContainText('laptop');

    await section.locator('.sect__revoke').click();
    await expect(section.locator('.sect__item')).toHaveCount(0);
  });
});
