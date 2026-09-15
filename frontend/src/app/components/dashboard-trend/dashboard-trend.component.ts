import { Component, ElementRef, Input, Output, EventEmitter, ViewChild, inject } from '@angular/core';
import { I18nService } from '../../services/i18n.service';
import { VerdictBadgeComponent } from '../verdict-badge/verdict-badge.component';
import { TrendTickerCardComponent } from '../trend-ticker-card/trend-ticker-card.component';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-dashboard-trend',
  standalone: true,
  imports: [VerdictBadgeComponent, TrendTickerCardComponent, TPipe],
  template: `
    @if (summary()) {
      <section class="trend reveal" style="--i: 6">
        <div class="trend__inner">
          <div class="trend__header">
            <h2 class="trend__title">{{ 'trend.title' | t }}</h2>
            <span class="trend__count">{{ 'trend.total' | t: { count: summary().total_analyses } }}</span>
          </div>

          <div class="trend__stats">
            <div class="trend__stat">
              <span class="trend__stat-value">{{ summary().average_score }}</span>
              <span class="trend__stat-label">{{ 'trend.avg_score' | t }}</span>
            </div>
            <div class="trend__distribution">
              @if (summary().total_analyses > 0) {
                @for (band of verdictBands; track band) {
                  @if (summary().verdict_distribution[band]) {
                    <div class="trend__dist-row">
                      <app-verdict-badge [verdict]="band"/>
                      <div class="trend__dist-bar">
                        <div class="trend__dist-fill" [style.width.%]="distPct(band)"></div>
                      </div>
                      <span class="trend__dist-count">{{ summary().verdict_distribution[band] }}</span>
                    </div>
                  }
                }
              } @else {
                <p class="trend__empty">{{ 'trend.empty' | t }}</p>
              }
            </div>
          </div>

          @if (tickers().length) {
            <div class="trend__slider">
              <button
                type="button"
                class="trend__nav trend__nav--prev"
                (click)="scroll(-1)"
                [attr.aria-label]="'trend.scroll_left' | t">&#8249;</button>
              <div class="trend__tickers" #tickerTrack>
                @for (ticker of tickers(); track ticker) {
                  <app-trend-ticker-card
                    [ticker]="ticker"
                    [active]="selectedTicker() === ticker"
                    [latest]="latestScore(ticker)"
                    [sectorsUrl]="sectorsUrl(ticker)"
                    [viewBox]="sparkViewBox"
                    [lines]="sparkPoints(ticker)"
                    [dotX]="sparkDot(ticker).x"
                    [dotY]="sparkDot(ticker).y"
                    (select)="tickerClick.emit($event)"/>
                }
              </div>
              <button
                type="button"
                class="trend__nav trend__nav--next"
                (click)="scroll(1)"
                [attr.aria-label]="'trend.scroll_right' | t">&#8250;</button>
            </div>
          }
        </div>
      </section>
    }
  `,
  styles: [`
    :host { display: block; }
    .trend {
      padding: 0 var(--space-lg) var(--space-3xl);
      max-width: 52rem;
      margin: 0 auto;
    }
    .trend__title {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: var(--space-md);
    }
    .trend__header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--space-md);
      margin-bottom: var(--space-md);
    }
    .trend__header .trend__title { margin-bottom: 0; }
    .trend__count {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .trend__stats {
      display: grid;
      grid-template-columns: 10rem 1fr;
      gap: var(--space-2xl);
      padding: var(--space-lg) 0;
      border-top: 1px solid var(--color-paper-3);
    }
    .trend__stat {
      display: flex;
      flex-direction: column;
      gap: var(--space-2xs);
    }
    .trend__stat-value {
      font-family: var(--font-mono);
      font-size: var(--text-3xl);
      color: var(--color-ink);
      line-height: 1;
    }
    .trend__stat-label {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .trend__distribution {
      display: flex;
      flex-direction: column;
      gap: var(--space-sm);
      justify-content: center;
    }
    .trend__dist-row {
      display: flex;
      align-items: center;
      gap: var(--space-sm);
    }
    .trend__dist-bar {
      flex: 1;
      height: 0.5rem;
      background: var(--color-paper-3);
      min-width: 4rem;
    }
    .trend__dist-fill {
      height: 100%;
      background: var(--color-accent);
      transition: width var(--dur-med) var(--ease-out);
    }
    .trend__dist-count {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-muted);
      width: 1.5rem;
      text-align: right;
    }
    .trend__empty {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .trend__slider {
      display: flex;
      align-items: stretch;
      gap: var(--space-sm);
      padding-top: var(--space-lg);
      border-top: 1px solid var(--color-paper-3);
    }
    .trend__tickers {
      display: flex;
      gap: var(--space-md);
      flex: 1;
      min-width: 0;
      overflow-x: auto;
      scroll-snap-type: x mandatory;
      scroll-behavior: smooth;
      padding-bottom: var(--space-2xs);
      scrollbar-width: thin;
    }
    .trend__nav {
      flex: 0 0 auto;
      align-self: center;
      width: 2rem;
      height: 2.5rem;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: none;
      border: 1px solid var(--color-paper-3);
      color: var(--color-muted);
      font-size: var(--text-lg);
      line-height: 1;
      cursor: pointer;
      transition: border-color var(--dur-short) var(--ease-out), color var(--dur-short) var(--ease-out);
    }
    .trend__nav:hover { border-color: var(--color-accent); color: var(--color-accent); }
    @media (max-width: 640px) {
      .trend { padding-left: var(--space-md); padding-right: var(--space-md); }
      .trend__stats { grid-template-columns: 1fr; gap: var(--space-lg); }
    }
  `],
})
export class DashboardTrendComponent {
  @Input() summary: () => any = () => null;
  @Input() selectedTicker: () => string | null = () => null;
  @Output() tickerClick = new EventEmitter<string>();

  @ViewChild('tickerTrack') tickerTrack?: ElementRef<HTMLDivElement>;

  private i18n = inject(I18nService);

  scroll(direction: number): void {
    const el = this.tickerTrack?.nativeElement;
    if (!el) return;
    el.scrollBy({ left: direction * Math.round(el.clientWidth * 0.8), behavior: 'smooth' });
  }

  readonly verdictBands = ['contradicted', 'mixed', 'supported', 'strongly_supported'];
  readonly sparkWidth = 200;
  readonly sparkHeight = 40;

  get sparkViewBox(): string {
    return `0 0 ${this.sparkWidth} ${this.sparkHeight}`;
  }

  tickers(): string[] {
    const s = this.summary();
    if (!s || !s.by_ticker) return [];
    return Object.keys(s.by_ticker).sort();
  }

  sectorsUrl(ticker: string): string {
    return `https://sectors.app/idx/${ticker.toLowerCase()}`;
  }

  distPct(band: string): number {
    const s = this.summary();
    if (!s || !s.total_analyses) return 0;
    return Math.round(((s.verdict_distribution?.[band] || 0) / s.total_analyses) * 100);
  }

  latestScore(ticker: string): number {
    const points = this.pointsFor(ticker);
    return points.length ? points[points.length - 1].score : 0;
  }

  sparkLines(ticker: string): { points: string }[] {
    const points = this.pointsFor(ticker);
    if (points.length < 2) return [];
    const coords = points.map((p, i) => {
      const x = (i / (points.length - 1)) * this.sparkWidth;
      const y = this.sparkHeight - (p.score / 100) * (this.sparkHeight - 6) - 3;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    });
    return [{ points: coords.join(' ') }];
  }

  sparkPoints(ticker: string): string[] {
    return this.sparkLines(ticker).map(line => line.points);
  }

  sparkDot(ticker: string): { x: number; y: number } {
    const points = this.pointsFor(ticker);
    if (!points.length) return { x: 0, y: 0 };
    const i = points.length - 1;
    const x = points.length > 1 ? (i / (points.length - 1)) * this.sparkWidth : this.sparkWidth / 2;
    const y = this.sparkHeight - (points[i].score / 100) * (this.sparkHeight - 6) - 3;
    return { x, y };
  }

  private pointsFor(ticker: string): { score: number }[] {
    const s = this.summary();
    if (!s || !s.by_ticker) return [];
    return s.by_ticker[ticker] || [];
  }
}