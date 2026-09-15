import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { I18nService } from '../../services/i18n.service';
import { TPipe } from '../../pipes/t.pipe';

/**
 * A single row in the history list: select checkbox, narrative + status/date,
 * and a delete action.
 */
@Component({
  selector: 'app-recent-item',
  standalone: true,
  imports: [DatePipe, TPipe],
  template: `
    <div class="recent__item" [class.recent__item--selected]="selected">
      <input
        type="checkbox"
        class="recent__check"
        [checked]="selected"
        (change)="toggle.emit({ id: claim.claim_id, checked: $any($event.target).checked })"
        [attr.aria-label]="'dashboard.select_claim' | t">
      <button (click)="view.emit(claim.claim_id)" class="recent__main">
        <span class="recent__narrative">{{ claim.narrative }}</span>
        <span class="recent__meta" [class.recent__meta--failed]="claim.status === 'failed'"
          [class.recent__meta--pending]="claim.status === 'pending'">
          {{ statusLabel(claim.status) }} &middot; {{ claim.created_at | date:'short' }}
        </span>
      </button>
      <button
        class="recent__delete"
        (click)="remove.emit(claim)"
        [attr.aria-label]="'dashboard.delete_claim' | t"
        title="{{ 'dashboard.delete_claim' | t }}">&times;</button>
    </div>
  `,
  styles: [`
    .recent__item {
      display: flex;
      align-items: center;
      gap: var(--space-sm);
      padding: var(--space-md) 0;
      border-top: 1px solid var(--color-paper-3);
      transition: background var(--dur-short) var(--ease-out);
    }
    .recent__item--selected { background: var(--color-paper-2); }
    .recent__check {
      accent-color: var(--color-accent);
      width: 1rem;
      height: 1rem;
      cursor: pointer;
      flex-shrink: 0;
    }
    .recent__main {
      display: flex;
      flex-direction: column;
      gap: var(--space-2xs);
      background: none;
      border: none;
      text-align: left;
      cursor: pointer;
      color: var(--color-ink);
      flex: 1;
      min-width: 0;
      padding: 0;
    }
    .recent__narrative {
      font-size: var(--text-sm);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .recent__meta {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .recent__meta--failed { color: var(--color-danger); }
    .recent__meta--pending { color: var(--color-warning); }
    .recent__delete {
      background: none;
      border: none;
      color: var(--color-dim);
      font-size: var(--text-md);
      line-height: 1;
      cursor: pointer;
      padding: var(--space-xs);
      flex-shrink: 0;
      transition: color var(--dur-short) var(--ease-out);
    }
    .recent__delete:hover { color: var(--color-danger); }
  `],
})
export class RecentItemComponent {
  @Input() claim: any;
  @Input() selected = false;
  @Output() view = new EventEmitter<string>();
  @Output() remove = new EventEmitter<any>();
  @Output() toggle = new EventEmitter<{ id: string; checked: boolean }>();

  private i18n = inject(I18nService);

  statusLabel(status: string): string {
    switch (status) {
      case 'completed': return this.i18n.t('status.completed');
      case 'failed': return this.i18n.t('status.failed');
      case 'pending': return this.i18n.t('status.pending');
      default: return status;
    }
  }
}
