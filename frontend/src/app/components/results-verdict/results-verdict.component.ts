import { Component, Input } from '@angular/core';
import { ScoreGaugeComponent } from '../score-gauge/score-gauge.component';
import { VerdictBadgeComponent } from '../verdict-badge/verdict-badge.component';
import { SectionHelpComponent } from '../section-help/section-help.component';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-results-verdict',
  standalone: true,
  imports: [ScoreGaugeComponent, VerdictBadgeComponent, SectionHelpComponent, TPipe],
  template: `
    <app-section-help helpKey="section_help.verdict"/>
    <div class="verdict">
      <app-score-gauge [score]="score()"/>
      <div class="verdict__text">
        <app-verdict-badge [verdict]="verdict()"/>
        <p class="verdict__explanation">{{ explanation() }}</p>
      </div>
    </div>
    @if (narrative().length) {
      <div class="verdict__narration">
        <p class="verdict__narration-title">{{ 'verdict.narrative.title' | t }}</p>
        <ul class="verdict__narration-list">
          @for (point of narrative(); track $index) {
            <li class="verdict__narration-item">{{ point }}</li>
          }
        </ul>
      </div>
    }
    <div class="legend">
      <p class="legend__title">{{ 'verdict.legend.title' | t }}</p>
      <ul class="legend__list">
        @for (band of bands; track band.id) {
          <li class="legend__item" [class.legend__item--active]="verdict() === band.id">
            <span class="legend__swatch" [attr.data-verdict]="band.id"></span>
            <span class="legend__range">{{ band.min }}–{{ band.max }}</span>
            <span class="legend__name">{{ band.key | t }}</span>
            <span class="legend__desc">{{ band.descKey | t }}</span>
          </li>
        }
      </ul>
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
    .verdict__narration {
      border-top: 1px solid var(--color-rule);
      border-left: 3px solid var(--color-accent);
      padding: var(--space-lg);
      background: var(--color-paper-2);
      margin-bottom: var(--space-lg);
    }
    .verdict__narration-title {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--color-dim);
      margin-bottom: var(--space-sm);
    }
    .verdict__narration-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: var(--space-2xs); }
    .verdict__narration-item {
      font-size: var(--text-sm);
      color: var(--color-muted);
      line-height: 1.55;
      padding-left: var(--space-sm);
      border-left: 1px solid var(--color-rule);
    }
    .legend {
      border-top: 1px solid var(--color-rule);
      padding: var(--space-lg) 0 var(--space-xl);
    }
    .legend__title {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--color-dim);
      margin-bottom: var(--space-sm);
    }
    .legend__list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: var(--space-2xs); }
    .legend__item {
      display: grid;
      grid-template-columns: auto auto 1fr auto;
      align-items: center;
      gap: var(--space-sm);
      padding: var(--space-2xs) var(--space-xs);
      border: 1px solid transparent;
      font-size: var(--text-sm);
    }
    .legend__item--active {
      border-color: var(--color-rule);
      background: var(--color-paper-2);
    }
    .legend__swatch {
      width: 0.7rem;
      height: 0.7rem;
      border-radius: 2px;
    }
    .legend__swatch[data-verdict="contradicted"] { background: var(--verdict-contradicted-fg); }
    .legend__swatch[data-verdict="mixed"] { background: var(--verdict-mixed-fg); }
    .legend__swatch[data-verdict="supported"] { background: var(--verdict-supported-fg); }
    .legend__swatch[data-verdict="strongly_supported"] { background: var(--verdict-strong-fg); }
    .legend__range {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
    }
    .legend__name {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      font-weight: 500;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: var(--color-ink);
    }
    .legend__desc {
      font-size: var(--text-xs);
      color: var(--color-muted);
      text-align: right;
    }
    @media (max-width: 640px) {
      .legend__item { grid-template-columns: auto auto 1fr; grid-template-rows: auto auto; }
      .legend__desc { grid-column: 3; text-align: left; }
    }
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
  @Input() narrative: () => string[] = () => [];

  readonly bands = [
    { id: 'contradicted', min: 0, max: 30, key: 'verdict.contradicted', descKey: 'verdict.legend.contradicted' },
    { id: 'mixed', min: 31, max: 60, key: 'verdict.mixed', descKey: 'verdict.legend.mixed' },
    { id: 'supported', min: 61, max: 80, key: 'verdict.supported', descKey: 'verdict.legend.supported' },
    { id: 'strongly_supported', min: 81, max: 100, key: 'verdict.strongly_supported', descKey: 'verdict.legend.strongly_supported' },
  ];
}