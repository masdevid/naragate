import { Component, Input, inject } from '@angular/core';
import { EvidenceCardComponent } from '../evidence-card/evidence-card.component';
import { SectionHelpComponent } from '../section-help/section-help.component';
import { I18nService } from '../../services/i18n.service';
import { FormatService } from '../../services/format.service';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-results-evidence',
  standalone: true,
  imports: [EvidenceCardComponent, SectionHelpComponent, TPipe],
  template: `
    <div class="evidence">
      @if (valuation() || fundamental() || market()) {
        <app-section-help helpKey="section_help.evidence"/>
      }
      @if (valuation()) {
        <app-evidence-card [title]="'results.valuation_title' | t" [cacheHit]="valuation().cache_hit">
          <div class="metrics">
            <div class="metric">
              <span class="metric__key">{{ 'metric.pe_ratio' | t }}</span>
              <span class="metric__val">{{ fmtNumber(valuation().metrics.pe, 2) }}</span>
            </div>
            <div class="metric">
              <span class="metric__key">{{ 'metric.pb_ratio' | t }}</span>
              <span class="metric__val">{{ fmtNumber(valuation().metrics.pb, 2) }}</span>
            </div>
            <div class="metric">
              <span class="metric__key">{{ 'metric.ps_ratio' | t }}</span>
              <span class="metric__val">{{ fmtNumber(valuation().metrics.ps, 2) }}</span>
            </div>
            <div class="metric">
              <span class="metric__key">{{ 'metric.pe_premium' | t }}</span>
              <span class="metric__val" [class]="'metric__val ' + changeClass(valuation().premium_pct.pe)">{{ fmtPercent(valuation().premium_pct.pe, 1) }}</span>
            </div>
          </div>
        </app-evidence-card>
      }

      @if (fundamental()) {
        <app-evidence-card [title]="'results.fundamental_title' | t" [cacheHit]="fundamental().cache_hit">
          <div class="metrics">
            <div class="metric">
              <span class="metric__key">{{ 'metric.revenue' | t }}</span>
              <span class="metric__val">{{ fmtIdr(fundamental().metrics.revenue) }}</span>
            </div>
            <div class="metric">
              <span class="metric__key">{{ 'metric.earnings' | t }}</span>
              <span class="metric__val">{{ fmtIdr(fundamental().metrics.earnings) }}</span>
            </div>
            <div class="metric">
              <span class="metric__key">{{ 'metric.revenue_trend' | t }}</span>
              <span class="metric__val" [class]="'metric__val ' + trendClass(fundamental().trend.revenue_trend)">{{ trendLabel(fundamental().trend.revenue_trend) }}</span>
            </div>
            <div class="metric">
              <span class="metric__key">{{ 'metric.earnings_trend' | t }}</span>
              <span class="metric__val" [class]="'metric__val ' + trendClass(fundamental().trend.earnings_trend)">{{ trendLabel(fundamental().trend.earnings_trend) }}</span>
            </div>
            <div class="metric">
              <span class="metric__key">{{ 'metric.roe' | t }}</span>
              <span class="metric__val">{{ fmtNumber(fundamental().metrics.roe, 2) }}</span>
            </div>
            <div class="metric">
              <span class="metric__key">{{ 'metric.debt_equity' | t }}</span>
              <span class="metric__val">{{ fmtNumber(fundamental().metrics.debt_to_equity, 2) }}</span>
            </div>
          </div>
        </app-evidence-card>
      }

      @if (market()) {
        <app-evidence-card [title]="'results.market_title' | t" [cacheHit]="market().cache_hit">
          <div class="metrics">
            <div class="metric">
              <span class="metric__key">{{ 'metric.change_1d' | t }}</span>
              <span class="metric__val" [class]="'metric__val ' + changeClass(market().performance['1d']?.price_change_pct)">{{ fmtPercent(market().performance['1d']?.price_change_pct, 2) }}</span>
            </div>
            <div class="metric">
              <span class="metric__key">{{ 'metric.change_7d' | t }}</span>
              <span class="metric__val" [class]="'metric__val ' + changeClass(market().performance['7d']?.price_change_pct)">{{ fmtPercent(market().performance['7d']?.price_change_pct, 2) }}</span>
            </div>
            <div class="metric">
              <span class="metric__key">{{ 'metric.change_30d' | t }}</span>
              <span class="metric__val" [class]="'metric__val ' + changeClass(market().performance['30d']?.price_change_pct)">{{ fmtPercent(market().performance['30d']?.price_change_pct, 2) }}</span>
            </div>
          </div>
        </app-evidence-card>
      }
    </div>
  `,
  styles: [`
    :host { display: block; }
    .evidence { display: flex; flex-direction: column; }
    .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr)); gap: var(--space-md); }
    .metric { display: flex; flex-direction: column; gap: var(--space-3xs); }
    .metric__key {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .metric__val {
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      color: var(--color-ink);
      font-variant-numeric: tabular-nums;
    }
    .trend--up { color: var(--color-success); }
    .trend--down { color: var(--color-danger); }
    .trend--flat { color: var(--color-warning); }
  `],
})
export class ResultsEvidenceComponent {
  @Input() valuation: () => any = () => null;
  @Input() fundamental: () => any = () => null;
  @Input() market: () => any = () => null;

  private i18n = inject(I18nService);
  private format = inject(FormatService);

  fmtNumber(value: number | null | undefined, decimals = 2): string {
    return this.format.number(value, decimals);
  }

  fmtPercent(value: number | null | undefined, decimals = 1): string {
    return this.format.percent(value, decimals);
  }

  fmtIdr(value: number | null | undefined): string {
    return this.format.idr(value);
  }

  trendLabel(trend: string): string {
    return this.i18n.t(`trend.${trend}`);
  }

  trendClass(trend: string): string {
    return this.format.trendClass(trend);
  }

  changeClass(value: number | null | undefined): string {
    return this.format.changeClass(value);
  }
}