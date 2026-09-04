import { Component, Input, inject } from '@angular/core';
import { I18nService } from '../../services/i18n.service';

@Component({
  selector: 'app-pipeline-progress',
  standalone: true,
  template: `
    <div class="pipeline">
      @for (step of steps; track step.key; let i = $index) {
        <div class="pipeline__step" [class.pipeline__step--active]="currentStep === step.key"
          [class.pipeline__step--done]="isCompleted(step.key)">
          <div class="pipeline__dot">
            @if (currentStep === step.key) {
              <span class="pipeline__spinner"></span>
            } @else if (isCompleted(step.key)) {
              <span class="pipeline__check">&#10003;</span>
            } @else {
              <span class="pipeline__num">{{ i + 1 }}</span>
            }
          </div>
          <span class="pipeline__label">{{ step.label }}</span>
        </div>
        @if (i < steps.length - 1) {
          <div class="pipeline__line" [class.pipeline__line--done]="isCompleted(step.key)"></div>
        }
      }
    </div>
  `,
  styles: [`
    .pipeline { display: flex; align-items: center; gap: 0; }
    .pipeline__step { display: flex; align-items: center; gap: var(--space-xs); }
    .pipeline__dot {
      width: 1.5rem; height: 1.5rem; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      background: var(--color-paper-3); color: var(--color-dim);
      font-family: var(--font-mono); font-size: var(--text-xs); flex-shrink: 0;
      transition: background var(--dur-short) var(--ease-out), color var(--dur-short) var(--ease-out);
    }
    .pipeline__step--active .pipeline__dot { background: var(--color-accent); color: var(--color-paper); }
    .pipeline__step--done .pipeline__dot { background: var(--color-success); color: var(--color-paper); }
    .pipeline__spinner {
      width: 0.75rem; height: 0.75rem; border: 2px solid var(--color-paper);
      border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .pipeline__check { font-size: 0.6rem; line-height: 1; }
    .pipeline__num { font-size: 0.55rem; }
    .pipeline__label {
      font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-muted);
      text-transform: uppercase; letter-spacing: 0.04em; white-space: nowrap;
    }
    .pipeline__step--active .pipeline__label { color: var(--color-ink); }
    .pipeline__step--done .pipeline__label { color: var(--color-dim); }
    .pipeline__line {
      width: 1.5rem; height: 1px; background: var(--color-paper-3);
      margin: 0 var(--space-2xs); flex-shrink: 0;
    }
    .pipeline__line--done { background: var(--color-success); }
    @media (max-width: 640px) {
      .pipeline__label { display: none; }
      .pipeline__line { width: var(--space-xs); }
    }
  `],
})
export class PipelineProgressComponent {
  @Input() currentStep: string = '';
  @Input() completedSteps: string[] = [];

  private i18n = inject(I18nService);

  get steps() {
    return [
      { key: 'claim_parsing', label: this.i18n.t('pipeline.parse') },
      { key: 'evidence_fetching', label: this.i18n.t('pipeline.evidence') },
      { key: 'skeptic_analysis', label: this.i18n.t('pipeline.skeptic') },
      { key: 'judge_assessment', label: this.i18n.t('pipeline.judge') },
      { key: 'score_computing', label: this.i18n.t('pipeline.score') },
    ];
  }

  isCompleted(stepKey: string): boolean {
    return this.completedSteps.includes(stepKey);
  }
}
