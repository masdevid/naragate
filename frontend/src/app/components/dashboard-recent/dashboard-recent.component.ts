import { Component, Input, Output, EventEmitter } from '@angular/core';
import { TPipe } from '../../pipes/t.pipe';
import { RecentItemComponent } from '../recent-item/recent-item.component';
import { HistoryPagerComponent } from '../history-pager/history-pager.component';

@Component({
  selector: 'app-dashboard-recent',
  standalone: true,
  imports: [TPipe, RecentItemComponent, HistoryPagerComponent],
  template: `
    @if (claims().length) {
      <section class="recent reveal" style="--i: 5">
        <div class="recent__inner">
          <div class="recent__header">
            <h2 class="recent__title">{{ 'dashboard.recent_title' | t }}</h2>
            <div class="recent__bulk">
              <label class="recent__select-all">
                <input
                  type="checkbox"
                  class="recent__check"
                  [checked]="allSelected()"
                  (change)="toggleSelectAll()"
                  [attr.aria-label]="'dashboard.select_all' | t">
                <span>{{ 'dashboard.select_all' | t }}</span>
              </label>
              <button class="recent__bulk-delete" (click)="confirmDeleteAll.emit()">{{ 'dashboard.delete_all' | t }}</button>
              @if (selectedIds().length) {
                <span class="recent__bulk-count">{{ 'dashboard.selected' | t: { count: selectedIds().length } }}</span>
                <button class="recent__bulk-delete" (click)="confirmBulkDelete.emit()">{{ 'dashboard.delete_selected' | t }}</button>
              }
            </div>
          </div>
          @if (filterTicker()) {
            <div class="recent__filter">
              <span class="recent__filter-label">{{ 'history.filtering' | t: { ticker: activeFilter() } }}</span>
              <button class="recent__filter-clear" (click)="clearFilter.emit()">{{ 'history.filter_clear' | t }}</button>
            </div>
          }
          <div class="recent__list">
            @for (claim of claims(); track claim.claim_id) {
              <app-recent-item
                [claim]="claim"
                [selected]="selectedIds().includes(claim.claim_id)"
                (view)="viewClaim.emit($event)"
                (remove)="confirmDelete.emit($event)"
                (toggle)="setSelected($event.id, $event.checked)"/>
            }
          </div>
          <app-history-pager
            [page]="page()"
            [total]="total()"
            [pageSize]="pageSize"
            (pageChange)="pageChange.emit($event)"/>
        </div>
      </section>
    } @else if (filterTicker()) {
      <section class="recent reveal" style="--i: 5">
        <div class="recent__inner">
          <h2 class="recent__title">{{ 'dashboard.recent_title' | t }}</h2>
          <p class="recent__filter-empty">{{ 'history.filter_empty' | t: { ticker: activeFilter() } }}</p>
        </div>
      </section>
    }
  `,
  styles: [`
    :host { display: block; }
    .recent {
      padding: 0 var(--space-lg) var(--space-3xl);
      max-width: 52rem;
      margin: 0 auto;
    }
    .recent__title {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: var(--space-md);
    }
    .recent__header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--space-md);
      margin-bottom: var(--space-md);
    }
    .recent__header .recent__title { margin-bottom: 0; }
    .recent__bulk {
      display: flex;
      align-items: center;
      gap: var(--space-md);
    }
    .recent__select-all {
      display: flex;
      align-items: center;
      gap: var(--space-2xs);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      cursor: pointer;
      white-space: nowrap;
    }
    .recent__bulk-count {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .recent__bulk-delete {
      background: none;
      border: 1px solid var(--color-danger);
      color: var(--color-danger);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: var(--space-2xs) var(--space-sm);
      cursor: pointer;
      transition: background var(--dur-short) var(--ease-out), color var(--dur-short) var(--ease-out);
    }
    .recent__bulk-delete:hover {
      background: var(--color-danger);
      color: var(--color-paper);
    }
    .recent__filter {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--space-sm);
      padding: var(--space-sm) var(--space-md);
      border-left: 2px solid var(--color-accent);
      background: var(--color-paper-2);
      margin-bottom: var(--space-sm);
    }
    .recent__filter-label {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-ink);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .recent__filter-clear {
      background: none;
      border: none;
      color: var(--color-accent);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      cursor: pointer;
      padding: 0;
      transition: color var(--dur-short) var(--ease-out);
    }
    .recent__filter-clear:hover { color: var(--color-ink); }
    .recent__filter-empty {
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      color: var(--color-dim);
      padding: var(--space-lg) 0;
      border-top: 1px solid var(--color-paper-3);
    }
    .recent__list {
      display: flex;
      flex-direction: column;
    }
    @media (max-width: 640px) {
      .recent { padding-left: var(--space-md); padding-right: var(--space-md); }
      .recent__header { flex-wrap: wrap; }
      .recent__bulk { flex-wrap: wrap; gap: var(--space-sm); }
    }
  `],
})
export class DashboardRecentComponent {
  @Input() claims: () => any[] = () => [];
  @Input() selectedIds: () => string[] = () => [];
  @Input() filterTicker: () => string | null = () => null;
  @Input() total: () => number = () => 0;
  @Input() page: () => number = () => 0;
  @Input() pageSize = 10;
  @Output() viewClaim = new EventEmitter<string>();
  @Output() confirmDelete = new EventEmitter<any>();
  @Output() confirmBulkDelete = new EventEmitter<void>();
  @Output() confirmDeleteAll = new EventEmitter<void>();
  @Output() clearFilter = new EventEmitter<void>();
  @Output() pageChange = new EventEmitter<number>();
  @Output() selectedChange = new EventEmitter<string[]>();

  activeFilter(): string {
    return this.filterTicker() || '';
  }

  allSelected(): boolean {
    const claims = this.claims();
    return claims.length > 0 && this.selectedIds().length === claims.length;
  }

  toggleSelectAll() {
    const claims = this.claims();
    const next = this.allSelected() ? [] : claims.map(c => c.claim_id);
    this.selectedChange.emit(next);
  }

  setSelected(claimId: string, checked: boolean) {
    const current = this.selectedIds();
    const next = checked ? [...current, claimId] : current.filter(id => id !== claimId);
    this.selectedChange.emit(next);
  }
}