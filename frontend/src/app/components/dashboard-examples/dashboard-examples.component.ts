import { Component, Output, EventEmitter, inject } from '@angular/core';
import { I18nService } from '../../services/i18n.service';
import { TPipe } from '../../pipes/t.pipe';

/**
 * Curated narrative template cards on the dashboard. Picking one emits the
 * narrative so the parent can fill the scanner input.
 */
@Component({
  selector: 'app-dashboard-examples',
  standalone: true,
  imports: [TPipe],
  template: `
    <div class="examples">
      <p class="examples__title">{{ 'dashboard.examples_title' | t }}</p>
      <div class="examples__grid">
        @for (ex of examples(); track ex.narrative) {
          <button class="examples__card" (click)="use.emit(ex.narrative)">
            <span class="examples__tag">{{ ex.tag }}</span>
            <span class="examples__text">{{ ex.narrative }}</span>
          </button>
        }
      </div>
    </div>
  `,
  styles: [`
    .examples {
      margin-top: var(--space-lg);
      display: flex;
      flex-direction: column;
      gap: var(--space-sm);
    }
    .examples__title {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .examples__grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
      grid-auto-rows: 1fr;
      gap: var(--space-sm);
    }
    .examples__card {
      display: flex;
      flex-direction: column;
      gap: var(--space-2xs);
      text-align: left;
      background: none;
      border: 1px solid var(--color-paper-3);
      color: var(--color-ink);
      padding: var(--space-md);
      cursor: pointer;
      transition: border-color var(--dur-short) var(--ease-out);
    }
    .examples__card:hover { border-color: var(--color-accent); }
    .examples__tag {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-accent);
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .examples__text {
      font-size: var(--text-sm);
      color: var(--color-muted);
      line-height: 1.5;
    }
  `],
})
export class DashboardExamplesComponent {
  @Output() use = new EventEmitter<string>();

  private i18n = inject(I18nService);

  examples(): { tag: string; narrative: string }[] {
    const en = this.i18n.language() === 'en';
    const t = (key: string) => this.i18n.t(key);
    return [
      { tag: en ? 'Valuation' : 'Valuasi', narrative: t('dashboard.examples.valuation') },
      { tag: en ? 'Fundamental' : 'Fundamental', narrative: t('dashboard.examples.fundamental') },
      { tag: en ? 'Market' : 'Pasar', narrative: t('dashboard.examples.market') },
      { tag: en ? 'News' : 'Berita', narrative: t('dashboard.examples.news') },
      { tag: en ? 'Policy \u00b7 BBM' : 'Kebijakan \u00b7 BBM', narrative: t('dashboard.examples.policy_bbm') },
      { tag: en ? 'Policy \u00b7 HBA' : 'Kebijakan \u00b7 HBA', narrative: t('dashboard.examples.policy_hba') },
      { tag: en ? 'Policy \u00b7 Nickel' : 'Kebijakan \u00b7 Nikel', narrative: t('dashboard.examples.policy_nickel') },
      { tag: en ? 'Needs ticker' : 'Butuh kode', narrative: t('dashboard.examples.no_ticker') },
      { tag: en ? 'Contradiction' : 'Kontradiksi', narrative: t('dashboard.examples.contradiction') },
      { tag: en ? 'Future price' : 'Harga masa depan', narrative: t('dashboard.examples.future_price') },
      { tag: en ? 'Below' : 'Turun', narrative: t('dashboard.examples.below_cpo') },
      { tag: en ? 'Below' : 'Turun', narrative: t('dashboard.examples.below_auto') },
    ];
  }
}