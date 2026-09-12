import { Component, Input, inject } from '@angular/core';
import { I18nService } from '../../services/i18n.service';
import { SectionHelpComponent } from '../section-help/section-help.component';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-skeptic-panel',
  standalone: true,
  imports: [SectionHelpComponent, TPipe],
  template: `
    <div class="skeptic">
      <h3 class="skeptic__title">{{ 'skeptic.title' | t }}</h3>
      <app-section-help helpKey="section_help.skeptic"/>

      @for (arg of counterArguments; track arg.point) {
        <div class="skeptic__arg">
          <p class="skeptic__point">{{ pointText(arg) }}</p>
          <div class="skeptic__bar-row">
            <span class="skeptic__label">{{ 'skeptic.strength' | t }}</span>
            <div class="skeptic__bar">
              <div class="skeptic__fill" [style.width.%]="arg.strength"
                [attr.data-level]="getLevel(arg.strength)"></div>
            </div>
            <span class="skeptic__pct">{{ arg.strength }}%</span>
          </div>
        </div>
      }

      @if (ambiguityList().length) {
        <div class="skeptic__section">
          <h4 class="skeptic__heading">{{ 'skeptic.ambiguity' | t }}</h4>
          @for (point of ambiguityList(); track point) {
            <p class="skeptic__item">{{ point }}</p>
          }
        </div>
      }

      @if (missingList().length) {
        <div class="skeptic__section">
          <h4 class="skeptic__heading">{{ 'skeptic.missing' | t }}</h4>
          @for (item of missingList(); track item) {
            <p class="skeptic__item">{{ item }}</p>
          }
        </div>
      }
    </div>
  `,
  styles: [`
    .skeptic { border-top: 1px solid var(--color-rule); padding-top: var(--space-lg); }
    .skeptic__title {
      font-family: var(--font-display); font-size: var(--text-md);
      text-transform: uppercase; letter-spacing: 0.02em; margin-bottom: var(--space-lg);
    }
    .skeptic__arg { padding: var(--space-md) 0; border-bottom: 1px solid var(--color-paper-3); }
    .skeptic__point { font-size: var(--text-sm); color: var(--color-ink); line-height: 1.5; margin-bottom: var(--space-sm); }
    .skeptic__bar-row { display: flex; align-items: center; gap: var(--space-sm); }
    .skeptic__label {
      font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-dim);
      text-transform: uppercase; letter-spacing: 0.04em; min-width: 5rem;
    }
    .skeptic__bar { flex: 1; height: 3px; background: var(--color-paper-3); }
    .skeptic__fill { height: 100%; transition: width var(--dur-long) var(--ease-out); }
    .skeptic__fill[data-level="high"] { background: var(--color-danger); }
    .skeptic__fill[data-level="mid"] { background: var(--color-warning); }
    .skeptic__fill[data-level="low"] { background: var(--color-success); }
    .skeptic__pct {
      font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-muted);
      min-width: 2.5rem; text-align: right;
    }
    .skeptic__section { margin-top: var(--space-lg); }
    .skeptic__heading {
      font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-dim);
      text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: var(--space-sm);
    }
    .skeptic__item {
      font-size: var(--text-sm); color: var(--color-muted); padding-left: var(--space-md);
      position: relative; line-height: 1.6;
    }
    .skeptic__item::before { content: '\u2014'; position: absolute; left: 0; color: var(--color-rule); }
  `],
})
export class SkepticPanelComponent {
  @Input() counterArguments: { point: string; point_en?: string; evidence_ref: string; strength: number }[] = [];
  @Input() ambiguityPoints: string[] = [];
  @Input() ambiguityPointsEn: string[] = [];
  @Input() missingEvidence: string[] = [];
  @Input() missingEvidenceEn: string[] = [];

  private i18n = inject(I18nService);

  private isEn() { return this.i18n.language() === 'en'; }

  pointText(arg: any): string {
    return this.isEn() && arg.point_en ? arg.point_en : arg.point;
  }

  ambiguityList(): string[] {
    return this.isEn() && this.ambiguityPointsEn?.length ? this.ambiguityPointsEn : this.ambiguityPoints;
  }

  missingList(): string[] {
    return this.isEn() && this.missingEvidenceEn?.length ? this.missingEvidenceEn : this.missingEvidence;
  }

  getLevel(strength: number): string {
    if (strength > 70) return 'high';
    if (strength > 40) return 'mid';
    return 'low';
  }
}
