import { Component, Input } from '@angular/core';
import { ScoreGaugeComponent } from '../score-gauge/score-gauge.component';
import { VerdictBadgeComponent } from '../verdict-badge/verdict-badge.component';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-results-verdict',
  standalone: true,
  imports: [ScoreGaugeComponent, VerdictBadgeComponent, TPipe],
  template: `
    <div class="verdict">
      <app-score-gauge [score]="score()"/>
      <div class="verdict__text">
        <app-verdict-badge [verdict]="verdict()"/>
        <p class="verdict__explanation">{{ explanation() }}</p>
      </div>
    </div>
    <div class="disclaimer">
      <p class="disclaimer__text">{{ 'disclaimer.text' | t }}</p>
    </div>
  `,
  styles: [`
    :host { display: block; }
    .verdict {
      border-top: 1px solid var(--color-rule);
      padding: var(--space-xl) 0;
      display: flex;
      align-items: flex-start;
      gap: var(--space-2xl);
    }
    .verdict__text { display: flex; flex-direction: column; gap: var(--space-md); }
    .verdict__explanation { font-size: var(--text-sm); color: var(--color-muted); max-width: 40ch; line-height: 1.55; }
    .disclaimer {
      border-top: 1px solid var(--color-rule);
      padding: var(--space-md) 0;
    }
    .disclaimer__text {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      line-height: 1.5;
      letter-spacing: 0.02em;
    }
    @media (max-width: 640px) {
      .verdict { flex-direction: column; align-items: center; text-align: center; }
      .verdict__explanation { max-width: none; }
    }
  `],
})
export class ResultsVerdictComponent {
  @Input() score: () => number = () => 0;
  @Input() verdict: () => string = () => '';
  @Input() explanation: () => string = () => '';
}