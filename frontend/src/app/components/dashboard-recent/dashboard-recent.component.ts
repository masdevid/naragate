import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { I18nService } from '../../services/i18n.service';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-dashboard-recent',
  standalone: true,
  imports: [DatePipe, TPipe],
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
          <div class="recent__list">
            @for (claim of claims(); track claim.claim_id) {
              <div class="recent__item" [class.recent__item--selected]="selectedIds().includes(claim.claim_id)">
                <input
                  type="checkbox"
                  class="recent__check"
                  [checked]="selectedIds().includes(claim.claim_id)"
                  (change)="toggleSelect(claim.claim_id, $event)"
                  [attr.aria-label]="'dashboard.select_claim' | t">
                <button (click)="viewClaim.emit(claim.claim_id)" class="recent__main">
                  <span class="recent__narrative">{{ claim.narrative }}</span>
                  <span class="recent__meta" [class.recent__meta--failed]="claim.status === 'failed'"
                    [class.recent__meta--pending]="claim.status === 'pending'">
                    {{ statusLabel(claim.status) }} &middot; {{ claim.created_at | date:'short' }}
                  </span>
                </button>
                <button
                  class="recent__delete"
                  (click)="confirmDelete.emit(claim)"
                  [attr.aria-label]="'dashboard.delete_claim' | t"
                  title="{{ 'dashboard.delete_claim' | t }}">&times;</button>
              </div>
            }
          </div>
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
    .recent__list {
      display: flex;
      flex-direction: column;
    }
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
  @Output() viewClaim = new EventEmitter<string>();
  @Output() confirmDelete = new EventEmitter<any>();
  @Output() confirmBulkDelete = new EventEmitter<void>();
  @Output() confirmDeleteAll = new EventEmitter<void>();

  private i18n = inject(I18nService);

  statusLabel(status: string): string {
    switch (status) {
      case 'completed': return this.i18n.t('status.completed');
      case 'failed': return this.i18n.t('status.failed');
      case 'pending': return this.i18n.t('status.pending');
      default: return status;
    }
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

  toggleSelect(claimId: string, event: Event) {
    const checked = (event.target as HTMLInputElement).checked;
    const current = this.selectedIds();
    const next = checked ? [...current, claimId] : current.filter(id => id !== claimId);
    this.selectedChange.emit(next);
  }

  @Output() selectedChange = new EventEmitter<string[]>();
}