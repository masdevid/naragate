import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { NarrativeService } from '../../services/narrative.service';
import { I18nService } from '../../services/i18n.service';
import { FormatService } from '../../services/format.service';
import { ScoreGaugeComponent } from '../../components/score-gauge/score-gauge.component';
import { VerdictBadgeComponent } from '../../components/verdict-badge/verdict-badge.component';
import { EvidenceCardComponent } from '../../components/evidence-card/evidence-card.component';
import { SkepticPanelComponent } from '../../components/skeptic-panel/skeptic-panel.component';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-results',
  standalone: true,
  imports: [ScoreGaugeComponent, VerdictBadgeComponent, EvidenceCardComponent, SkepticPanelComponent, TPipe],
  template: `
    <div class="results">
      <div class="results__inner">
        <button (click)="goBack()" class="results__back">&larr; {{ 'results.back' | t }}</button>

        @if (loading()) {
          <div class="results__loading">
            <p>{{ 'results.loading' | t }}</p>
          </div>
        } @else if (error()) {
          <div class="results__error">
            <p>{{ error() }}</p>
          </div>
        } @else if (claimData()) {
          @if (claimData().status === 'failed') {
            <div class="results__status results__status--failed">
              <p class="results__status-title">{{ 'results.failed_title' | t }}</p>
              <p class="results__status-text">{{ claimData().error || 'results.failed_message' | t }}</p>
              <button (click)="retry()" class="results__status-btn">{{ 'results.retry' | t }}</button>
            </div>
          } @else if (claimData().status === 'pending') {
            <div class="results__status">
              <p class="results__status-title">{{ 'results.pending_title' | t }}</p>
              <p class="results__status-text">{{ 'results.pending_message' | t }}</p>
            </div>
          }

          <div class="results__narrative">
            <p class="results__label">{{ 'results.narrative_label' | t }}</p>
            <p class="results__quote">&ldquo;{{ claimData().narrative }}&rdquo;</p>
          </div>

          @if (claimData().claim) {
            <div class="results__claim">
              <p class="results__label">{{ 'results.claim_label' | t }}</p>
              <p class="results__assertion">{{ assertion() }}</p>
              <div class="results__meta">
                <span class="results__meta-item">
                  <span class="results__meta-key">{{ 'results.ticker' | t }}</span>
                  <span class="results__meta-value">{{ claimData().claim.ticker }}</span>
                </span>
                <span class="results__meta-item">
                  <span class="results__meta-key">{{ 'results.category' | t }}</span>
                  <span class="results__meta-value">{{ claimData().claim.category }}</span>
                </span>
                <span class="results__meta-item">
                  <span class="results__meta-key">{{ 'results.direction' | t }}</span>
                  <span class="results__meta-value">
                    <span class="results__direction-icon">{{ directionIcon(claimData().claim.direction) }}</span>
                    {{ directionLabel(claimData().claim.direction) }}
                  </span>
                </span>
              </div>
            </div>
          }

          @if (claimData().score) {
            <div class="results__verdict">
              <app-score-gauge [score]="claimData().score.reality_gap_score"/>
              <div class="results__verdict-text">
                <app-verdict-badge [verdict]="claimData().score.verdict"/>
                <p class="results__explanation">{{ explanation() }}</p>
              </div>
            </div>
          }

          @if (claimData().evidence) {
            <div class="results__evidence">
              @if (claimData().evidence.valuation) {
                <app-evidence-card [title]="'results.valuation_title' | t" [cacheHit]="claimData().evidence.valuation.cache_hit">
                  <div class="results__metrics">
                    <div class="results__metric">
                      <span class="results__metric-key">{{ 'metric.pe_ratio' | t }}</span>
                      <span class="results__metric-val">{{ fmtNumber(claimData().evidence.valuation.metrics.pe, 2) }}</span>
                    </div>
                    <div class="results__metric">
                      <span class="results__metric-key">{{ 'metric.pb_ratio' | t }}</span>
                      <span class="results__metric-val">{{ fmtNumber(claimData().evidence.valuation.metrics.pb, 2) }}</span>
                    </div>
                    <div class="results__metric">
                      <span class="results__metric-key">{{ 'metric.ps_ratio' | t }}</span>
                      <span class="results__metric-val">{{ fmtNumber(claimData().evidence.valuation.metrics.ps, 2) }}</span>
                    </div>
                    <div class="results__metric">
                      <span class="results__metric-key">{{ 'metric.pe_premium' | t }}</span>
                      <span class="results__metric-val" [class]="'results__metric-val ' + changeClass(claimData().evidence.valuation.premium_pct.pe)">{{ fmtPercent(claimData().evidence.valuation.premium_pct.pe, 1) }}</span>
                    </div>
                  </div>
                </app-evidence-card>
              }

              @if (claimData().evidence.fundamental) {
                <app-evidence-card [title]="'results.fundamental_title' | t" [cacheHit]="claimData().evidence.fundamental.cache_hit">
                  <div class="results__metrics">
                    <div class="results__metric">
                      <span class="results__metric-key">{{ 'metric.revenue' | t }}</span>
                      <span class="results__metric-val">{{ fmtIdr(claimData().evidence.fundamental.metrics.revenue) }}</span>
                    </div>
                    <div class="results__metric">
                      <span class="results__metric-key">{{ 'metric.earnings' | t }}</span>
                      <span class="results__metric-val">{{ fmtIdr(claimData().evidence.fundamental.metrics.earnings) }}</span>
                    </div>
                    <div class="results__metric">
                      <span class="results__metric-key">{{ 'metric.revenue_trend' | t }}</span>
                      <span class="results__metric-val" [class]="'results__metric-val ' + trendClass(claimData().evidence.fundamental.trend.revenue_trend)">{{ trendLabel(claimData().evidence.fundamental.trend.revenue_trend) }}</span>
                    </div>
                    <div class="results__metric">
                      <span class="results__metric-key">{{ 'metric.earnings_trend' | t }}</span>
                      <span class="results__metric-val" [class]="'results__metric-val ' + trendClass(claimData().evidence.fundamental.trend.earnings_trend)">{{ trendLabel(claimData().evidence.fundamental.trend.earnings_trend) }}</span>
                    </div>
                    <div class="results__metric">
                      <span class="results__metric-key">{{ 'metric.roe' | t }}</span>
                      <span class="results__metric-val">{{ fmtNumber(claimData().evidence.fundamental.metrics.roe, 2) }}</span>
                    </div>
                    <div class="results__metric">
                      <span class="results__metric-key">{{ 'metric.debt_equity' | t }}</span>
                      <span class="results__metric-val">{{ fmtNumber(claimData().evidence.fundamental.metrics.debt_to_equity, 2) }}</span>
                    </div>
                  </div>
                </app-evidence-card>
              }

              @if (claimData().evidence.market) {
                <app-evidence-card [title]="'results.market_title' | t" [cacheHit]="claimData().evidence.market.cache_hit">
                  <div class="results__metrics">
                    <div class="results__metric">
                      <span class="results__metric-key">{{ 'metric.change_1d' | t }}</span>
                      <span class="results__metric-val" [class]="'results__metric-val ' + changeClass(claimData().evidence.market.performance['1d']?.price_change_pct)">{{ fmtPercent(claimData().evidence.market.performance['1d']?.price_change_pct, 2) }}</span>
                    </div>
                    <div class="results__metric">
                      <span class="results__metric-key">{{ 'metric.change_7d' | t }}</span>
                      <span class="results__metric-val" [class]="'results__metric-val ' + changeClass(claimData().evidence.market.performance['7d']?.price_change_pct)">{{ fmtPercent(claimData().evidence.market.performance['7d']?.price_change_pct, 2) }}</span>
                    </div>
                    <div class="results__metric">
                      <span class="results__metric-key">{{ 'metric.change_30d' | t }}</span>
                      <span class="results__metric-val" [class]="'results__metric-val ' + changeClass(claimData().evidence.market.performance['30d']?.price_change_pct)">{{ fmtPercent(claimData().evidence.market.performance['30d']?.price_change_pct, 2) }}</span>
                    </div>
                  </div>
                </app-evidence-card>
              }
            </div>
          }

          @if (claimData().skeptic) {
            <app-skeptic-panel
              [counterArguments]="claimData().skeptic.counter_arguments"
              [ambiguityPoints]="claimData().skeptic.ambiguity_points"
              [ambiguityPointsEn]="claimData().skeptic.ambiguity_points_en"
              [missingEvidence]="claimData().skeptic.missing_evidence"
              [missingEvidenceEn]="claimData().skeptic.missing_evidence_en"/>
          }
        }
      </div>
    </div>
  `,
  styles: [`
    .results { padding: var(--space-2xl) var(--space-lg); }
    .results__inner { max-width: 48rem; margin: 0 auto; }
    .results__back {
      background: none; border: none; color: var(--color-muted);
      font-family: var(--font-mono); font-size: var(--text-sm);
      cursor: pointer; padding: 0; margin-bottom: var(--space-xl);
      transition: color var(--dur-short) var(--ease-out);
    }
    .results__back:hover { color: var(--color-ink); }
    .results__loading, .results__error {
      padding: var(--space-4xl) 0; text-align: center;
      font-family: var(--font-mono); font-size: var(--text-sm); color: var(--color-muted);
    }
    .results__error { color: var(--color-danger); }
    .results__status {
      border: 1px solid var(--color-warning); padding: var(--space-lg);
      margin-bottom: var(--space-lg); display: flex; flex-direction: column; gap: var(--space-sm);
    }
    .results__status--failed { border-color: var(--color-danger); }
    .results__status-title {
      font-family: var(--font-mono); font-size: var(--text-xs); text-transform: uppercase;
      letter-spacing: 0.06em; color: var(--color-warning);
    }
    .results__status--failed .results__status-title { color: var(--color-danger); }
    .results__status-text { font-size: var(--text-sm); color: var(--color-muted); line-height: 1.55; }
    .results__status-btn {
      align-self: flex-start; background: none; border: 1px solid var(--color-ink);
      color: var(--color-ink); font-family: var(--font-mono); font-size: var(--text-xs);
      text-transform: uppercase; letter-spacing: 0.04em; padding: var(--space-2xs) var(--space-sm);
      cursor: pointer; transition: opacity var(--dur-short) var(--ease-out);
    }
    .results__status-btn:hover { opacity: 0.7; }
    .results__narrative { border-top: 1px solid var(--color-rule); padding: var(--space-lg) 0; }
    .results__label {
      font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-dim);
      text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: var(--space-sm);
    }
    .results__quote {
      font-size: var(--text-md); color: var(--color-muted); line-height: 1.55; font-style: italic;
    }
    .results__claim { border-top: 1px solid var(--color-rule); padding: var(--space-lg) 0; }
    .results__assertion { font-size: var(--text-xl); color: var(--color-ink); margin-bottom: var(--space-md); }
    .results__meta { display: flex; flex-wrap: wrap; gap: var(--space-lg); }
    .results__meta-item { display: flex; flex-direction: column; gap: var(--space-3xs); }
    .results__meta-key {
      font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-dim);
      text-transform: uppercase; letter-spacing: 0.06em;
    }
    .results__meta-value {
      font-family: var(--font-mono); font-size: var(--text-sm); color: var(--color-ink); text-transform: uppercase;
    }
    .results__direction-icon { margin-right: var(--space-2xs); color: var(--color-accent); }
    .results__verdict {
      border-top: 1px solid var(--color-rule); padding: var(--space-xl) 0;
      display: flex; align-items: flex-start; gap: var(--space-2xl);
    }
    .results__verdict-text { display: flex; flex-direction: column; gap: var(--space-md); }
    .results__explanation { font-size: var(--text-sm); color: var(--color-muted); max-width: 40ch; line-height: 1.55; }
    .results__metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr)); gap: var(--space-md); }
    .results__metric { display: flex; flex-direction: column; gap: var(--space-3xs); }
    .results__metric-key {
      font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-dim);
      text-transform: uppercase; letter-spacing: 0.04em;
    }
    .results__metric-val {
      font-family: var(--font-mono); font-size: var(--text-sm); color: var(--color-ink); font-variant-numeric: tabular-nums;
    }
    .trend--up { color: var(--color-success); }
    .trend--down { color: var(--color-danger); }
    .trend--flat { color: var(--color-warning); }
    .results__evidence { display: flex; flex-direction: column; }
    @media (max-width: 640px) {
      .results { padding: var(--space-lg) var(--space-md); }
      .results__verdict { flex-direction: column; align-items: center; text-align: center; }
      .results__explanation { max-width: none; }
    }
  `],
})
export class ResultsComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private narrativeService = inject(NarrativeService);
  private i18n = inject(I18nService);
  private format = inject(FormatService);

  claimId = '';
  claimData = signal<any>(null);
  loading = signal(true);
  error = signal('');

  ngOnInit() {
    this.claimId = this.route.snapshot.paramMap.get('id') || '';
    if (this.claimId) {
      this.loadClaim();
    } else {
      this.loading.set(false);
      this.error.set(this.i18n.t('results.no_claim'));
    }
  }

  loadClaim() {
    this.narrativeService.getClaim(this.claimId).subscribe({
      next: (data) => { this.claimData.set(data); this.loading.set(false); },
      error: (err) => { this.error.set(err.message || this.i18n.t('results.load_error')); this.loading.set(false); },
    });
  }

  goBack() { this.router.navigate(['/dashboard']); }

  retry() {
    const narrative = this.claimData()?.narrative;
    if (narrative) {
      this.router.navigate(['/claim'], { queryParams: { narrative } });
    }
  }

  assertion() {
    const claim = this.claimData()?.claim;
    if (!claim) return '';
    return this.i18n.language() === 'en' && claim.assertion_en ? claim.assertion_en : claim.assertion;
  }

  explanation() {
    const score = this.claimData()?.score;
    if (!score) return '';
    return this.i18n.language() === 'en' && score.explanation_en ? score.explanation_en : score.explanation;
  }

  fmtNumber(value: number | null | undefined, decimals = 2): string {
    return this.format.number(value, decimals);
  }

  fmtPercent(value: number | null | undefined, decimals = 1): string {
    return this.format.percent(value, decimals);
  }

  fmtIdr(value: number | null | undefined): string {
    return this.format.idr(value);
  }

  directionIcon(direction: string): string {
    return this.format.directionIcon(direction);
  }

  directionLabel(direction: string): string {
    return this.i18n.t(`direction.${direction}`);
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
