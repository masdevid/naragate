import { Component, OnInit, inject, signal, effect } from '@angular/core';
import { Router } from '@angular/router';
import { NarrativeService } from '../../services/narrative.service';
import { SettingsService, RuntimeSettings } from '../../services/settings.service';
import { I18nService } from '../../services/i18n.service';
import { ConfirmModalComponent } from '../../components/confirm-modal/confirm-modal.component';
import { DashboardWarningsComponent } from '../../components/dashboard-warnings/dashboard-warnings.component';
import { DashboardHeroComponent } from '../../components/dashboard-hero/dashboard-hero.component';
import { DashboardInputComponent } from '../../components/dashboard-input/dashboard-input.component';
import { DashboardRecentComponent } from '../../components/dashboard-recent/dashboard-recent.component';
import { DashboardTrendComponent } from '../../components/dashboard-trend/dashboard-trend.component';
import { DashboardBulkComponent } from '../../components/dashboard-bulk/dashboard-bulk.component';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    ConfirmModalComponent,
    DashboardWarningsComponent,
    DashboardHeroComponent,
    DashboardInputComponent,
    DashboardRecentComponent,
    DashboardTrendComponent,
    DashboardBulkComponent,
    TPipe,
  ],
  template: `
    <app-dashboard-warnings
      [setupComplete]="setupComplete()"
      [llmConfigured]="llmConfigured()"
      [sectorsConfigured]="sectorsConfigured()"
      (goSetup)="goSetup()"
      (goSettings)="goSettings()"
      (dismissLlm)="llmConfigured.set(true)"
      (dismissSectors)="sectorsConfigured.set(true)"/>

    <app-dashboard-hero [headlineParts]="headlineParts"/>

    <app-dashboard-input
      [analyzing]="analyzing()"
      (analyze)="startAnalysis($event)"/>

    <app-dashboard-bulk (complete)="refreshLists()"/>

    <app-dashboard-recent
      [claims]="recentClaims"
      [selectedIds]="selectedIds"
      (viewClaim)="viewClaim($event)"
      (confirmDelete)="confirmDelete($event)"
      (confirmBulkDelete)="confirmBulkDelete()"
      (selectedChange)="selectedIds.set($event)"/>

    <app-dashboard-trend [summary]="trendSummary"/>

    <!-- Footer -->
    <footer class="footer">
      <p class="footer__text">{{ 'dashboard.footer' | t }}</p>
    </footer>

    <!-- Confirm modals -->
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
  `,
  styles: [`
    :host { display: block; }
    .footer {
      padding: var(--space-2xl) var(--space-lg);
      border-top: 1px solid var(--color-rule);
      max-width: 52rem;
      margin: 0 auto;
    }
    .footer__text {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      letter-spacing: 0.04em;
    }
    @media (max-width: 640px) {
      .footer { padding-left: var(--space-md); padding-right: var(--space-md); }
    }
  `],
})
export class DashboardComponent implements OnInit {
  recentClaims = signal<any[]>([]);
  trendSummary = signal<any>(null);
  setupComplete = signal(true);
  llmConfigured = signal(true);
  sectorsConfigured = signal(true);
  headlineParts = signal<string[]>([]);
  selectedIds = signal<string[]>([]);
  analyzing = signal(false);
  pendingDelete: any = null;
  bulkDelete = false;

  private router = inject(Router);
  private narrativeService = inject(NarrativeService);
  private settingsService = inject(SettingsService);
  private i18n = inject(I18nService);

  constructor() {
    effect(() => {
      this.i18n.language();
      this.updateHeadline();
    });
  }

  ngOnInit() {
    this.updateHeadline();
    this.refreshLists();

    this.settingsService.getSettings().subscribe({
      next: (settings: RuntimeSettings) => {
        this.llmConfigured.set(!!(settings.llm_endpoint && settings.llm_endpoint.trim() && settings.llm_model && settings.llm_model.trim()));
        this.sectorsConfigured.set(!!(settings.sectors_api_key && settings.sectors_api_key.trim()));
      },
      error: () => {
        this.llmConfigured.set(false);
        this.sectorsConfigured.set(false);
      },
    });

    this.settingsService.getSetupStatus().subscribe({
      next: (status) => this.setupComplete.set(status.complete),
      error: () => this.setupComplete.set(false),
    });
  }

  startAnalysis(narrative: string) {
    if (narrative.trim() && !this.analyzing()) {
      this.analyzing.set(true);
      this.router.navigate(['/claim'], { queryParams: { narrative } });
    }
  }

  viewClaim(claimId: string) {
    this.router.navigate(['/results', claimId]);
  }

  confirmDelete(claim: any) {
    this.pendingDelete = claim;
  }

  confirmBulkDelete() {
    this.bulkDelete = true;
  }

  onDeleteConfirmed() {
    if (this.pendingDelete) {
      const id = this.pendingDelete.claim_id;
      this.narrativeService.deleteClaim(id).subscribe({
        next: () => {
          this.recentClaims.update(cs => cs.filter(c => c.claim_id !== id));
          this.pendingDelete = null;
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
        },
        error: () => { this.bulkDelete = false; },
      });
    }
  }

  onDeleteCancelled() {
    this.pendingDelete = null;
    this.bulkDelete = false;
  }

  goSettings() {
    this.router.navigate(['/settings']);
  }

  goSetup() {
    this.router.navigate(['/setup']);
  }

  refreshLists() {
    this.narrativeService.getClaims().subscribe({
      next: (claims) => this.recentClaims.set(claims),
      error: () => {},
    });

    this.narrativeService.getClaimsSummary().subscribe({
      next: (summary) => this.trendSummary.set(summary),
      error: () => {},
    });
  }

  private updateHeadline() {
    const raw = this.i18n.t('dashboard.headline');
    const parts = raw.split('{{_}}');
    this.headlineParts.set(parts);
  }
}