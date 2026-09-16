import { test, expect } from '../fixtures';
import { claimState } from '../api-mocks';

/**
 * Regression coverage for the follow-up chat race condition: while the agent is
 * still thinking about a template question, every other template must be
 * disabled so a second click cannot dismiss it and race a replacement.
 */
test.describe('Follow-up chat template race', () => {
  test('@FIX-E2E-005 templates disable while the agent is thinking', async ({ page }) => {
    page.addInitScript(() => localStorage.setItem('naragate_setup_dismissed', '1'));

    let releaseChat: () => void = () => {};
    const chatGate = new Promise<void>(resolve => { releaseChat = resolve; });
    let chatCalls = 0;

    await page.route('**/api/v1/claims/race-claim', route => route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(claimState({
        claim_id: 'race-claim',
        status: 'completed',
        score: { reality_gap_score: 72, verdict: 'supported', explanation: 'ok', dimensions: {} },
      })),
    }));
    await page.route('**/api/v1/claims/race-claim/suggestions', route => route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        claim_id: 'race-claim',
        suggestions: [
          { id: 's1', text: 'Kenapa skornya 72?', text_en: 'Why is the score 72?' },
          { id: 's2', text: 'Bukti apa yang menguatkan verdict?', text_en: 'What evidence supports the verdict?' },
        ],
        cached: false,
      }),
    }));
    await page.route('**/api/v1/claims/race-claim/suggestions/feedback', route => route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ recorded: true }),
    }));
    await page.route('**/api/v1/claims/race-claim/suggestions/next', route => route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        claim_id: 'race-claim',
        suggestion: { id: 's-new', text: 'Pertanyaan pengganti?', text_en: 'A replacement question?' },
      }),
    }));
    await page.route('**/api/v1/claims/race-claim/chat', async route => {
      chatCalls++;
      await chatGate;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ answer: 'Jawaban.', answer_en: 'The answer.' }),
      });
    });

    await page.goto('/results/race-claim', { waitUntil: 'domcontentloaded' });
    await page.locator('.chat__fab').click();

    const first = page.locator('.chat__suggestion', { hasText: 'Kenapa skornya 72?' });
    const second = page.locator('.chat__suggestion', { hasText: 'Bukti apa' });
    await expect(first).toBeEnabled();
    await expect(second).toBeEnabled();

    await first.click();

    // The agent is now thinking: the request is in flight and every remaining
    // template is disabled, so a second click cannot dismiss it.
    await expect.poll(() => chatCalls, { timeout: 5_000 }).toBe(1);
    await expect(second).toBeDisabled();

    // Force-clicking through the gate still must not start a second answer nor
    // dismiss the template.
    await second.dispatchEvent('click');
    await page.waitForTimeout(300);
    expect(chatCalls).toBe(1);
    await expect(second).toBeVisible();

    releaseChat();
    await expect(page.locator('.chat__suggestion', { hasText: 'Pertanyaan pengganti?' })).toBeVisible();
  });
});
