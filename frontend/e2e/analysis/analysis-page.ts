import { Page, Locator, expect } from '@playwright/test';

export class DashboardPage {
  readonly narrativeInput: Locator;
  readonly analyzeButton: Locator;

  constructor(private readonly page: Page) {
    this.narrativeInput = page.locator('textarea.input-section__field');
    this.analyzeButton = page.locator('button.input-section__btn');
  }

  async goto(): Promise<void> {
    await this.page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
    await expect(this.analyzeButton).toBeVisible();
  }

  async analyze(narrative: string): Promise<void> {
    await this.narrativeInput.fill(narrative);
    await this.analyzeButton.click();
    await expect(this.page).toHaveURL(/\/claim/);
  }
}

export class ClaimPage {
  readonly error: Locator;

  constructor(private readonly page: Page) {
    this.error = page.locator('.claim__error');
  }

  async expectClarificationShown(): Promise<void> {
    // The ticker guardrail surfaces the clarification message and never
    // advances the pipeline to the evidence stage.
    await expect(this.error).toBeVisible();
    await expect(this.error).toContainText(/kode saham/i);
  }

  async waitForCompletionRedirect(): Promise<void> {
    await expect(this.page).toHaveURL(/\/results\/new-claim/, { timeout: 15_000 });
  }
}

export class ResultsPage {
  readonly statusBanner: Locator;
  readonly statusTitle: Locator;
  readonly retryButton: Locator;
  readonly suggestionChips: Locator;

  constructor(private readonly page: Page) {
    this.statusBanner = page.locator('.results__status');
    this.statusTitle = page.locator('.results__status-title');
    this.retryButton = page.locator('.results__status-btn');
    this.suggestionChips = page.locator('.chat__suggestion');
  }

  async goto(claimId: string): Promise<void> {
    await this.page.goto(`/results/${claimId}`, { waitUntil: 'domcontentloaded' });
  }

  async expectStillProcessing(): Promise<void> {
    await expect(this.statusBanner).toBeVisible();
    await expect(this.statusTitle).toContainText(/diproses/i);
  }

  async retry(): Promise<void> {
    await this.retryButton.click();
    await expect(this.page).toHaveURL(/\/claim/);
  }

  async expectCompleted(): Promise<void> {
    await expect(this.statusBanner).not.toBeVisible();
    await expect(this.page.locator('.results__narrative')).toBeVisible();
  }

  async expectContextualSuggestions(): Promise<void> {
    // Suggestions load lazily when the chat panel opens.
    await this.page.locator('.chat__fab').click();
    await expect(this.suggestionChips.first()).toContainText(/skornya 72/i);
  }
}