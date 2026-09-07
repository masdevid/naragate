import { Component, Input, inject } from '@angular/core';
import { EvidenceCardComponent } from '../evidence-card/evidence-card.component';
import { I18nService } from '../../services/i18n.service';
import { FormatService } from '../../services/format.service';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-results-filings',
  standalone: true,
  imports: [EvidenceCardComponent, TPipe],
  template: `
    <div class="filings">
      @if (filings()) {
        <app-evidence-card [title]="'results.filings_title' | t" [cacheHit]="filings().cache_hit">
          <div class="filings__body">
            <span class="filings__badge" [class]="'filings__badge--' + filings().recent_bias">
              {{ biasLabel(filings().recent_bias) }}
            </span>
            <p class="filings__summary">{{ summary(filings()) }}</p>
            @if (filings().filings?.length) {
              <p class="filings__recent">{{ 'filings.recent_title' | t }}</p>
              <ul class="filings__list">
                @for (f of filings().filings.slice(0, 5); track $index) {
                  <li class="filings__item">
                    <span class="filings__date">{{ f.date }}</span>
                    <span class="filings__person">
                      <span class="filings__name">{{ f.insider_name }}</span>
                      <span class="filings__title">{{ f.insider_title }}</span>
                    </span>
                    <span class="filings__type" [class]="'filings__type--' + f.transaction_type">
                      {{ typeLabel(f.transaction_type) }}
                    </span>
                    <span class="filings__shares">{{ fmtNumber(f.shares, 0) }}</span>
                    <span class="filings__value">{{ fmtIdr(f.total_value) }}</span>
                  </li>
                }
              </ul>
            }
          </div>
        </app-evidence-card>
      }
    </div>
  `,
  styles: [`
    :host { display: block; }
    .filings { display: flex; flex-direction: column; }
    .filings__body { display: flex; flex-direction: column; gap: var(--space-sm); }
    .filings__badge {
      align-self: flex-start;
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      padding: var(--space-3xs) var(--space-xs);
      border: 1px solid var(--color-rule);
    }
    .filings__badge--net_buying { color: var(--color-success); border-color: var(--color-success); }
    .filings__badge--net_selling { color: var(--color-danger); border-color: var(--color-danger); }
    .filings__badge--balanced { color: var(--color-dim); }
    .filings__summary { font-size: var(--text-sm); color: var(--color-muted); line-height: 1.55; }
    .filings__recent {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-top: var(--space-sm);
    }
    .filings__list {
      list-style: none;
      padding: 0;
      margin: 0;
      display: flex;
      flex-direction: column;
      gap: var(--space-2xs);
    }
    .filings__item {
      display: grid;
      grid-template-columns: 7rem 1fr auto auto;
      gap: var(--space-sm);
      align-items: center;
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      padding: var(--space-2xs) 0;
      border-top: 1px solid var(--color-rule);
    }
    .filings__date { color: var(--color-muted); }
    .filings__person { display: flex; flex-direction: column; gap: var(--space-3xs); }
    .filings__name { color: var(--color-ink); }
    .filings__title { color: var(--color-dim); }
    .filings__type {
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: var(--space-3xs) var(--space-xs);
      border: 1px solid var(--color-rule);
    }
    .filings__type--buy { color: var(--color-success); border-color: var(--color-success); }
    .filings__type--sell { color: var(--color-danger); border-color: var(--color-danger); }
    .filings__shares { text-align: right; }
    .filings__value { text-align: right; }
  `],
})
export class ResultsFilingsComponent {
  @Input() filings: () => any = () => null;

  private i18n = inject(I18nService);
  private format = inject(FormatService);

  biasLabel(bias: string): string {
    return this.i18n.t(`filings.bias.${bias}`);
  }

  typeLabel(type: string): string {
    return this.i18n.t(`filings.type.${type}`);
  }

  fmtNumber(value: number | null | undefined, decimals = 2): string {
    return this.format.number(value, decimals);
  }

  fmtIdr(value: number | null | undefined): string {
    return this.format.idr(value);
  }

  summary(evidence: any): string {
    if (!evidence) return '';
    return this.i18n.language() === 'en' && evidence.summary_en ? evidence.summary_en : evidence.summary;
  }
}