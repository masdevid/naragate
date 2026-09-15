// Claim-template fixtures + page helpers for the dashboard templates e2e suite.
// The 12 curated narrative templates on the dashboard (dashboard-examples) are
// driven through a full analysis (mocked SSE) and the rendered results page is
// asserted against the claim data that template would produce.
import { Page, Locator, expect } from '@playwright/test';

export const VERDICT_LABELS: Record<string, string> = {
  contradicted: 'Bertentangan',
  mixed: 'Campuran',
  supported: 'Didukung',
  strongly_supported: 'Sangat Didukung',
};

export const DIRECTION_LABELS: Record<string, string> = {
  above: 'Naik',
  below: 'Turun',
  between: 'Di Antara',
  neutral: 'Netral',
};

// Score → verdict bands exactly as declared in results-verdict.component.ts.
export const VERDICT_BANDS: Record<string, [number, number]> = {
  contradicted: [0, 30],
  mixed: [31, 60],
  supported: [61, 80],
  strongly_supported: [81, 100],
};

export function bandForScore(score: number): string {
  if (score <= 30) return 'contradicted';
  if (score <= 60) return 'mixed';
  if (score <= 80) return 'supported';
  return 'strongly_supported';
}

export interface TemplateEvidence {
  valuation?: any;
  fundamental?: any;
  market?: any;
  news?: any;
  corporate_actions?: any;
  filings?: any;
}

export interface TemplateCase {
  id: string;
  claimId: string;
  tile: string;                     // hasText selector that uniquely finds the tile
  narrative: string;                // the Indonesian narrative the tile emits
  claim: Record<string, any>;
  evidence?: TemplateEvidence;
  skeptic?: any;
  score: Record<string, any>;
  precheck?: Record<string, any>;   // /api/v1/precheck/ payload for policy templates
  clarification?: boolean;          // this template halts at the ticker guardrail
  expectedCardTitles: string[];     // the evidence sections this case is *intended* to show
  expectsPolicy?: boolean;          // the policy section is intended for this claim
  expectedMetrics?: { card: string; key: string; value: string | RegExp }[];
}

export class TemplateFlow {
  constructor(private readonly page: Page) {}

  readonly tiles = () => this.page.locator('.examples__card');
  readonly textarea = () => this.page.locator('textarea.input-section__field');
  readonly analyzeButton = () => this.page.locator('button.input-section__btn');

  async goto(): Promise<void> {
    await this.page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
    await expect(this.analyzeButton()).toBeVisible();
  }

  async chooseTemplate(c: TemplateCase): Promise<void> {
    await this.tiles().filter({ hasText: c.tile }).first().click();
    await expect(this.textarea()).toHaveValue(c.narrative);
  }

  async analyze(): Promise<void> {
    await this.analyzeButton().click();
    await expect(this.page).toHaveURL(/\/claim/);
  }

  async waitForResults(claimId: string): Promise<void> {
    await expect(this.page).toHaveURL(new RegExp(`/results/${claimId}`), { timeout: 15_000 });
  }

  // ---------- results page assertions ----------

  resultsQuote = () => this.page.locator('.results__quote');
  claimBlock = () => this.page.locator('.results__claim');
  verdictBadge = () => this.page.locator('.verdict__text .badge');
  gaugeValue = () => this.page.locator('.gauge__value');
  narrationItems = () => this.page.locator('.verdict__narration-item');
  legendActive = () => this.page.locator('.legend__item--active');
  evidenceCards = () => this.page.locator('app-evidence-card');
  radarLegend = () => this.page.locator('.radar__legend-item');

  evidenceCard(title: string): Locator {
    return this.page.locator('app-evidence-card', {
      has: this.page.locator('.card__title', { hasText: title }),
    });
  }

  async metric(card: Locator, key: string): Promise<Locator> {
    const keySpan = card.locator('.metric__key').filter({ hasText: new RegExp(`^${key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}$`) }).first();
    return keySpan.locator('xpath=..');
  }

  async expectNarrativeQuote(c: TemplateCase): Promise<void> {
    await expect(this.resultsQuote()).toContainText(c.narrative);
    // Coherence: a ticker-based narrative must actually reference its parsed ticker.
    if (!c.claim.is_policy) {
      await expect(this.resultsQuote()).toContainText(c.claim.ticker);
    }
  }

  async expectClaimMeta(c: TemplateCase): Promise<void> {
    const block = this.claimBlock();
    await expect(block.locator('.results__assertion')).toContainText(c.claim.assertion);

    const ticker = block.locator('a.results__meta-value').filter({ hasText: c.claim.ticker });
    await expect(ticker).toBeVisible();
    await expect(ticker).toHaveAttribute('href', `https://sectors.app/idx/${c.claim.ticker.toLowerCase()}`);
    await expect(block.locator('.results__meta-value').filter({ hasText: c.claim.category })).toBeVisible();

    const direction = block.locator('.results__meta-item').filter({ hasText: DIRECTION_LABELS[c.claim.direction] });
    await expect(direction).toBeVisible();
  }

  async expectScore(c: TemplateCase): Promise<void> {
    const score = c.score.reality_gap_score;
    const verdict = c.score.verdict;
    const [min, max] = VERDICT_BANDS[verdict];

    await expect(this.gaugeValue()).toHaveText(String(score));
    await expect(this.verdictBadge()).toHaveText(VERDICT_LABELS[verdict]);
    await expect(this.verdictBadge()).toHaveAttribute('data-verdict', verdict);

    // Coherence: the displayed gauge score must fall inside the displayed verdict's band.
    const displayedVerdict = (await this.verdictBadge().getAttribute('data-verdict'))!;
    const displayedScore = Number(await this.gaugeValue().textContent());
    expect(displayedScore).toBeGreaterThanOrEqual(VERDICT_BANDS[displayedVerdict][0]);
    expect(displayedScore).toBeLessThanOrEqual(VERDICT_BANDS[displayedVerdict][1]);

    // Exactly one legend band is highlighted, and it is the verdict's band.
    const active = this.legendActive();
    await expect(active).toHaveCount(1);
    await expect(active.locator('.legend__name')).toHaveText(VERDICT_LABELS[verdict]);
    await expect(active.locator('.legend__swatch')).toHaveAttribute('data-verdict', verdict);
    await expect(active.locator('.legend__range')).toHaveText(`${min}\u2013${max}`);

    // Narration is always populated once a score exists.
    await expect(this.narrationItems().first()).toBeVisible();
    const dims = Object.keys(c.score.dimensions ?? {}).length;
    if (dims) await expect(this.radarLegend()).toHaveCount(dims);
  }

  async expectSections(c: TemplateCase): Promise<void> {
    // The exact set (and order) of evidence cards must match the intended case —
    // this catches an extra/unexpected section being shown for a narrative.
    await expect(this.page.locator('app-evidence-card .card__title')).toHaveText(c.expectedCardTitles);

    // The policy section appears only for policy claims; there it must carry no evidence cards.
    await expect(this.page.locator('.policy')).toHaveCount(c.expectsPolicy ? 1 : 0);
    if (c.expectsPolicy) {
      await expect(this.page.locator('.evidence .metric')).toHaveCount(0);
      await expect(this.page.locator('.evidence .section-help')).toHaveCount(0);
    }

    for (const m of c.expectedMetrics ?? []) {
      const card = this.evidenceCard(m.card);
      await expect(card).toBeVisible();
      const metricItem = await this.metric(card, m.key);
      await expect(metricItem.locator('.metric__val')).toHaveText(m.value);
    }
  }

  async expectSkeptic(c: TemplateCase): Promise<void> {
    const skeptic = c.skeptic;
    if (!skeptic) {
      await expect(this.page.locator('.skeptic__title')).toHaveCount(0);
      return;
    }
    await expect(this.page.locator('.skeptic__title')).toBeVisible();
    await expect(this.page.locator('.skeptic__arg')).toHaveCount(skeptic.counter_arguments.length);
    if (skeptic.counter_arguments.length) {
      await expect(this.page.locator('.skeptic__point').first()).toContainText(skeptic.counter_arguments[0].point);
      await expect(this.page.locator('.skeptic__pct').first()).toContainText(`${skeptic.counter_arguments[0].strength}%`);
    }
    const sections = (skeptic.ambiguity_points?.length ? 1 : 0) + (skeptic.missing_evidence?.length ? 1 : 0);
    await expect(this.page.locator('.skeptic__section')).toHaveCount(sections);
  }
}