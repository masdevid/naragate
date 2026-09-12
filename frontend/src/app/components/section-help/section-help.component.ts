import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-section-help',
  standalone: true,
  imports: [TPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="section-help">
      <span class="section-help__mark"></span>
      <p class="section-help__text">{{ helpKey() | t }}</p>
    </div>
  `,
  styles: [`
    :host { display: block; }
    .section-help {
      display: flex;
      align-items: flex-start;
      gap: var(--space-sm);
      padding: var(--space-sm) var(--space-md);
      border: 1px solid var(--color-rule);
      border-left: 2px solid var(--color-accent);
      background: var(--color-paper);
      margin-bottom: var(--space-md);
    }
    .section-help__mark {
      flex-shrink: 0;
      margin-top: 0.3rem;
      width: 0.4rem;
      height: 0.4rem;
      background: var(--color-accent);
    }
    .section-help__text {
      margin: 0;
      font-size: var(--text-xs);
      color: var(--color-muted);
      line-height: 1.55;
    }
  `],
})
export class SectionHelpComponent {
  readonly helpKey = input.required<string>();
}