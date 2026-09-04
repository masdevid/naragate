import { Component, Input, inject } from '@angular/core';
import { I18nService } from '../../services/i18n.service';

@Component({
  selector: 'app-verdict-badge',
  standalone: true,
  template: `
    <span class="badge" [attr.data-verdict]="verdict">
      {{ getLabel() }}
    </span>
  `,
  styles: [`
    .badge {
      display: inline-block;
      padding: var(--space-2xs) var(--space-sm);
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      font-weight: 500;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    .badge[data-verdict="contradicted"] {
      background: var(--verdict-contradicted-bg);
      color: var(--verdict-contradicted-fg);
    }
    .badge[data-verdict="mixed"] {
      background: var(--verdict-mixed-bg);
      color: var(--verdict-mixed-fg);
    }
    .badge[data-verdict="supported"] {
      background: var(--verdict-supported-bg);
      color: var(--verdict-supported-fg);
    }
    .badge[data-verdict="strongly_supported"] {
      background: var(--verdict-strong-bg);
      color: var(--verdict-strong-fg);
    }
  `],
})
export class VerdictBadgeComponent {
  @Input() verdict: string = '';
  private i18n = inject(I18nService);

  getLabel(): string {
    const key = `verdict.${this.verdict}`;
    const translated = this.i18n.t(key);
    return translated !== key ? translated : this.verdict.replace(/_/g, ' ');
  }
}
