import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-score-gauge',
  standalone: true,
  template: `
    <div class="gauge">
      <svg class="gauge__ring" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="42" fill="none" stroke="var(--color-paper-3)" stroke-width="6"/>
        <circle cx="50" cy="50" r="42" fill="none" [attr.stroke]="getColor()" stroke-width="6"
          [attr.stroke-dasharray]="getDashArray()" stroke-linecap="round"
          class="gauge__fill"/>
      </svg>
      <div class="gauge__label">
        <span class="gauge__value" [style.color]="getColor()">{{ score }}</span>
        <span class="gauge__unit">/ 100</span>
      </div>
    </div>
  `,
  styles: [`
    .gauge {
      position: relative;
      width: 10rem;
      height: 10rem;
    }
    .gauge__ring {
      width: 100%;
      height: 100%;
      transform: rotate(-90deg);
    }
    .gauge__fill {
      transition: stroke-dasharray var(--dur-long) var(--ease-out);
    }
    .gauge__label {
      position: absolute;
      inset: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }
    .gauge__value {
      font-family: var(--font-display);
      font-size: var(--text-3xl);
      line-height: 1;
      text-transform: uppercase;
    }
    .gauge__unit {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-muted);
      margin-top: var(--space-3xs);
    }
  `],
})
export class ScoreGaugeComponent {
  @Input() score: number = 0;

  getColor(): string {
    if (this.score <= 30) return 'var(--color-danger)';
    if (this.score <= 60) return 'var(--color-warning)';
    if (this.score <= 80) return 'var(--color-success)';
    return 'var(--color-accent)';
  }

  getDashArray(): string {
    const circumference = 2 * Math.PI * 42;
    const filled = (this.score / 100) * circumference;
    return `${filled} ${circumference}`;
  }
}
