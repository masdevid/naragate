import { Component, Input, inject } from '@angular/core';
import { I18nService } from '../../services/i18n.service';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-evidence-card',
  standalone: true,
  imports: [TPipe],
  template: `
    <div class="card">
      <button (click)="expanded = !expanded" class="card__header">
        <h3 class="card__title">{{ title }}</h3>
        <div class="card__meta">
          @if (cacheHit) {
            <span class="card__cache">{{ 'cache.hit' | t }}</span>
          }
          <span class="card__chevron" [class.card__chevron--open]="expanded">&#8595;</span>
        </div>
      </button>
      @if (expanded) {
        <div class="card__body">
          <ng-content></ng-content>
        </div>
      }
    </div>
  `,
  styles: [`
    .card { border-top: 1px solid var(--color-rule); }
    .card__header {
      display: flex; align-items: center; justify-content: space-between;
      width: 100%; padding: var(--space-lg) 0; background: none; border: none;
      cursor: pointer; color: var(--color-ink); text-align: left;
    }
    .card__title {
      font-family: var(--font-display); font-size: var(--text-md);
      text-transform: uppercase; letter-spacing: 0.02em;
    }
    .card__meta { display: flex; align-items: center; gap: var(--space-sm); }
    .card__cache {
      font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-dim);
      letter-spacing: 0.04em; text-transform: uppercase;
    }
    .card__chevron {
      font-size: var(--text-sm); color: var(--color-muted);
      transition: transform var(--dur-short) var(--ease-out);
    }
    .card__chevron--open { transform: rotate(180deg); }
    .card__body { padding-bottom: var(--space-lg); }
  `],
})
export class EvidenceCardComponent {
  @Input() title: string = '';
  @Input() cacheHit: boolean = false;
  expanded: boolean = true;

  private i18n = inject(I18nService);
}
