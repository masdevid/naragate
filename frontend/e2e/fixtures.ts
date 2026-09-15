import { test as base, expect } from '@playwright/test';

/**
 * Shared e2e test with the app-login guard satisfied.
 *
 * The UI redirects to /login unless `/api/v1/auth/me` reports a session, so
 * every test gets an authenticated auth/me route by default. Individual specs
 * still mock the endpoints they exercise.
 */
export const test = base.extend({
  page: async ({ page }, use) => {
    await page.route('**/api/v1/auth/me', route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: true,
          email: 'e2e@example.com',
          subscription_tier: 'FREE',
          credits: 600,
          promo_credits: 442,
          key_bound: true,
        }),
      }),
    );
    await use(page);
  },
});

export { expect };
