import { Component, Input, Output, EventEmitter } from '@angular/core';
import { TPipe } from '../../pipes/t.pipe';

/**
 * Prev/next pager with a page counter and the visible range. Renders nothing
 * when everything fits on a single page.
 */
@Component({
  selector: 'app-history-pager',
  standalone: true,
  imports: [TPipe],
  template: `
    @if (totalPages() > 1) {
      <div class="recent__pager">
        <button
          type="button"
          class="recent__pager-btn"
          [disabled]="page <= 0"
          (click)="go(page - 1)">
          {{ 'history.prev' | t }}
        </button>
        <span class="recent__pager-info">
          {{ 'history.page' | t: { page: page + 1, total: totalPages() } }}
          <span class="recent__pager-range">{{ 'history.showing' | t: { from: rangeFrom(), to: rangeTo(), total: total } }}</span>
        </span>
        <button
          type="button"
          class="recent__pager-btn"
          [disabled]="page >= totalPages() - 1"
          (click)="go(page + 1)">
          {{ 'history.next' | t }}
        </button>
      </div>
    }
  `,
  styles: [`
    .recent__pager {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--space-md);
      padding: var(--space-md) 0;
      margin-top: var(--space-sm);
      border-top: 1px solid var(--color-paper-3);
    }
    .recent__pager-btn {
      background: none;
      border: 1px solid var(--color-paper-3);
      color: var(--color-ink);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: var(--space-2xs) var(--space-sm);
      cursor: pointer;
      transition: border-color var(--dur-short) var(--ease-out), color var(--dur-short) var(--ease-out);
    }
    .recent__pager-btn:hover:not(:disabled) { border-color: var(--color-accent); color: var(--color-accent); }
    .recent__pager-btn:disabled { opacity: 0.4; cursor: not-allowed; }
    .recent__pager-info {
      display: flex;
      align-items: baseline;
      gap: var(--space-sm);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .recent__pager-range { color: var(--color-dim); }
  `],
})
export class HistoryPagerComponent {
  @Input() page = 0;
  @Input() total = 0;
  @Input() pageSize = 10;
  @Output() pageChange = new EventEmitter<number>();

  totalPages(): number {
    return Math.max(1, Math.ceil(this.total / Math.max(1, this.pageSize)));
  }

  rangeFrom(): number {
    return this.total ? this.page * this.pageSize + 1 : 0;
  }

  rangeTo(): number {
    return Math.min(this.total, (this.page + 1) * this.pageSize);
  }

  go(page: number) {
    if (page < 0 || page >= this.totalPages() || page === this.page) return;
    this.pageChange.emit(page);
  }
}
