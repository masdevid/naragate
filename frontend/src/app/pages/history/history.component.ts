import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { NarrativeService } from '../../services/narrative.service';
import { ConfirmModalComponent } from '../../components/confirm-modal/confirm-modal.component';
import { DashboardRecentComponent } from '../../components/dashboard-recent/dashboard-recent.component';
import { DashboardTrendComponent } from '../../components/dashboard-trend/dashboard-trend.component';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-history',
  standalone: true,
  imports: [RouterLink, ConfirmModalComponent, DashboardRecentComponent, DashboardTrendComponent, TPipe],
  template: `
    <section class="history">
      <div class="history__header">
        <h1 class="history__title">{{ 'history.title' | t }}</h1>
        <a routerLink="/dashboard" class="history__back">{{ 'history.back' | t }}</a>
      </div>

      @if (recentClaims().length === 0) {
        <p class="history__empty">{{ 'history.empty' | t }}</p>
      }

      <app-dashboard-recent
        [claims]="filteredClaims"
        [selectedIds]="selectedIds"
        [filterTicker]="selectedTicker"
        (viewClaim)="viewClaim($event)"
        (confirmDelete)="confirmDelete($event)"
        (confirmBulkDelete)="confirmBulkDelete()"
        (confirmDeleteAll)="confirmDeleteAll()"
        (selectedChange)="selectedIds.set($event)"
        (clearFilter)="selectedTicker.set(null)"/>

      <app-dashboard-trend
        [summary]="trendSummary"
        [selectedTicker]="selectedTicker"
        (tickerClick)="onTickerClick($event)"/>

      @if (pendingDelete) {
        <app-confirm-modal
          [title]="'dashboard.confirm_delete_title' | t"
          [message]="'dashboard.confirm_delete_message' | t"
          [confirmLabel]="'dashboard.delete' | t"
          [cancelLabel]="'dashboard.cancel' | t"
          (confirmed)="onDeleteConfirmed()"
          (cancelled)="onDeleteCancelled()"/>
      }
      @if (bulkDelete) {
        <app-confirm-modal
          [title]="'dashboard.confirm_bulk_title' | t: { count: selectedIds().length }"
          [message]="'dashboard.confirm_bulk_message' | t"
          [confirmLabel]="'dashboard.delete' | t"
          [cancelLabel]="'dashboard.cancel' | t"
          (confirmed)="onDeleteConfirmed()"
          (cancelled)="onDeleteCancelled()"/>
      }
      @if (deleteAll) {
        <app-confirm-modal
          [title]="'dashboard.confirm_delete_all_title' | t"
          [message]="'dashboard.confirm_delete_all_message' | t"
          [confirmLabel]="'dashboard.delete' | t"
          [cancelLabel]="'dashboard.cancel' | t"
          (confirmed)="onDeleteAllConfirmed()"
          (cancelled)="onDeleteAllCancelled()"/>
      }
    </section>
  `,
  styles: [`
    :host { display: block; }
    .history {
      padding: var(--space-2xl) var(--space-lg) var(--space-3xl);
      max-width: 52rem;
      margin: 0 auto;
    }
    .history__header {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: var(--space-md);
      margin-bottom: var(--space-2xl);
    }
    .history__title {
      font-family: var(--font-display);
      font-size: var(--text-xl);
      color: var(--color-ink);
      margin: 0;
    }
    .history__back {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-accent);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      text-decoration: none;
    }
    .history__back:hover { text-decoration: underline; }
    .history__empty {
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      color: var(--color-dim);
      padding: var(--space-2xl) 0;
      border-top: 1px solid var(--color-paper-3);
      text-align: center;
    }
    @media (max-width: 640px) {
      .history { padding-left: var(--space-md); padding-right: var(--space-md); }
    }
  `],
})
export class HistoryComponent implements OnInit {
  recentClaims = signal<any[]>([]);
  trendSummary = signal<any>(null);
  selectedIds = signal<string[]>([]);
  selectedTicker = signal<string | null>(null);
  filteredClaims = computed(() => {
    const claims = this.recentClaims();
    const ticker = this.selectedTicker();
    if (!ticker) return claims;
    return claims.filter(c => (c.claim?.ticker || '') === ticker);
  });
  pendingDelete: any = null;
  bulkDelete = false;
  deleteAll = false;

  private router = inject(Router);
  private narrativeService = inject(NarrativeService);

  ngOnInit() {
    this.refreshLists();
  }

  viewClaim(claimId: string) {
    this.router.navigate(['/results', claimId]);
  }

  onTickerClick(ticker: string) {
    this.selectedTicker.set(this.selectedTicker() === ticker ? null : ticker);
  }

  confirmDelete(claim: any) {
    this.pendingDelete = claim;
  }

  confirmBulkDelete() {
    this.bulkDelete = true;
  }

  confirmDeleteAll() {
    this.deleteAll = true;
  }

  onDeleteConfirmed() {
    if (this.pendingDelete) {
      const id = this.pendingDelete.claim_id;
      this.narrativeService.deleteClaim(id).subscribe({
        next: () => {
          this.recentClaims.update(cs => cs.filter(c => c.claim_id !== id));
          this.pendingDelete = null;
          this.refreshSummary();
        },
        error: () => { this.pendingDelete = null; },
      });
    } else if (this.bulkDelete) {
      const ids = this.selectedIds();
      this.narrativeService.deleteClaims(ids).subscribe({
        next: () => {
          this.recentClaims.update(cs => cs.filter(c => !ids.includes(c.claim_id)));
          this.selectedIds.set([]);
          this.bulkDelete = false;
          this.refreshSummary();
        },
        error: () => { this.bulkDelete = false; },
      });
    }
  }

  onDeleteAllConfirmed() {
    this.narrativeService.deleteAllClaims().subscribe({
      next: () => {
        this.recentClaims.set([]);
        this.selectedIds.set([]);
        this.deleteAll = false;
        this.refreshSummary();
      },
      error: () => { this.deleteAll = false; },
    });
  }

  onDeleteAllCancelled() {
    this.deleteAll = false;
  }

  onDeleteCancelled() {
    this.pendingDelete = null;
    this.bulkDelete = false;
  }

  refreshLists() {
    this.narrativeService.getClaims().subscribe({
      next: (claims) => this.recentClaims.set(claims),
      error: () => {},
    });
    this.refreshSummary();
  }

  refreshSummary() {
    this.narrativeService.getClaimsSummary().subscribe({
      next: (summary) => this.trendSummary.set(summary),
      error: () => {},
    });
  }
}