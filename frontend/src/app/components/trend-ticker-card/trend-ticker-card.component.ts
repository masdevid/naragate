import { Component, Input, Output, EventEmitter } from '@angular/core';

/**
 * A single per-ticker card in the trend slider: ticker, latest score, a spark
 * line of its score history, and a link out to Sectors.
 */
@Component({
  selector: 'app-trend-ticker-card',
  standalone: true,
  template: `
    <div
      class="trend__ticker"
      [class.trend__ticker--active]="active"
      role="button"
      tabindex="0"
      (click)="select.emit(ticker)"
      (keydown.enter)="select.emit(ticker)"
      (keydown.space)="select.emit(ticker); $event.preventDefault()">
      <div class="trend__ticker-head">
        <span class="trend__ticker-name">{{ ticker }}</span>
        <span class="trend__ticker-actions">
          <span class="trend__ticker-latest">{{ latest }}</span>
          <a
            class="trend__ticker-sectors"
            [href]="sectorsUrl"
            target="_blank"
            rel="noopener"
            title="Open in Sectors"
            (click)="$event.stopPropagation()">&#8599;</a>
        </span>
      </div>
      <svg class="trend__spark" [attr.viewBox]="viewBox" preserveAspectRatio="none">
        @for (points of lines; track $index) {
          <polyline class="trend__spark-line" [attr.points]="points" fill="none"/>
        }
        <circle class="trend__spark-dot" [attr.cx]="dotX" [attr.cy]="dotY" r="3"/>
      </svg>
    </div>
  `,
  styles: [`
    .trend__ticker {
      flex: 0 0 auto;
      width: 14rem;
      scroll-snap-align: start;
      border: 1px solid var(--color-paper-3);
      padding: var(--space-md);
      display: flex;
      flex-direction: column;
      gap: var(--space-sm);
      cursor: pointer;
      text-align: left;
      background: none;
      transition: border-color var(--dur-short) var(--ease-out), box-shadow var(--dur-short) var(--ease-out);
    }
    .trend__ticker:hover {
      border-color: var(--color-accent);
      box-shadow: inset 0 0 0 1px var(--color-accent);
    }
    .trend__ticker:focus-visible {
      outline: 2px solid var(--color-accent);
      outline-offset: 2px;
    }
    .trend__ticker--active {
      border-color: var(--color-accent);
      box-shadow: inset 0 0 0 1px var(--color-accent);
    }
    .trend__ticker-head {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: var(--space-sm);
    }
    .trend__ticker-name {
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      color: var(--color-ink);
      font-weight: 600;
      text-decoration: none;
      transition: color var(--dur-short) var(--ease-out);
    }
    .trend__ticker:hover .trend__ticker-name { color: var(--color-accent); }
    .trend__ticker-actions {
      display: flex;
      align-items: baseline;
      gap: var(--space-sm);
    }
    .trend__ticker-latest {
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      color: var(--color-accent);
    }
    .trend__ticker-sectors {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      text-decoration: none;
      transition: color var(--dur-short) var(--ease-out);
    }
    .trend__ticker-sectors:hover { color: var(--color-accent); }
    .trend__spark { width: 100%; height: 2.5rem; }
    .trend__spark-line {
      stroke: var(--color-accent);
      stroke-width: 1.5;
      stroke-linejoin: round;
      stroke-linecap: round;
    }
    .trend__spark-dot { fill: var(--color-accent); }
  `],
})
export class TrendTickerCardComponent {
  @Input() ticker = '';
  @Input() active = false;
  @Input() latest: number | string = '';
  @Input() sectorsUrl = '';
  @Input() viewBox = '0 0 200 40';
  @Input() lines: string[] = [];
  @Input() dotX = 0;
  @Input() dotY = 0;
  @Output() select = new EventEmitter<string>();
}
