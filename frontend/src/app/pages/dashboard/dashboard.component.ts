import { Component, OnInit, inject, signal, effect } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';
import { NarrativeService } from '../../services/narrative.service';
import { SettingsService, RuntimeSettings } from '../../services/settings.service';
import { I18nService } from '../../services/i18n.service';
import { ConfirmModalComponent } from '../../components/confirm-modal/confirm-modal.component';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [FormsModule, DatePipe, ConfirmModalComponent, TPipe],
  template: `
    <!-- Warnings -->
    @if (!llmConfigured()) {
      <div class="warn reveal" style="--i: 0">
        <div class="warn__inner">
          <span class="warn__icon">!</span>
          <span class="warn__text">{{ 'dashboard.warn_llm' | t }}</span>
          <button class="warn__btn" (click)="goSettings()">{{ 'dashboard.fix' | t }}</button>
          <button class="warn__dismiss" (click)="llmConfigured.set(true)">&times;</button>
        </div>
      </div>
    }
    @if (!sectorsConfigured()) {
      <div class="warn warn--yellow reveal" style="--i: 0">
        <div class="warn__inner">
          <span class="warn__icon">!</span>
          <span class="warn__text">{{ 'dashboard.warn_sectors' | t }}</span>
          <button class="warn__btn" (click)="goSettings()">{{ 'dashboard.fix' | t }}</button>
          <button class="warn__dismiss" (click)="sectorsConfigured.set(true)">&times;</button>
        </div>
      </div>
    }

    <!-- Hero -->
    <section class="hero">
      <div class="hero__inner">
        <p class="hero__eyebrow reveal" style="--i: 1">{{ 'dashboard.eyebrow' | t }}</p>
        <h1 class="hero__display reveal" style="--i: 2">
          @if (headlineParts().length > 1) {
            {{ headlineParts()[0] }}<em class="hero__accent"> {{ headlineParts()[1] }} </em>{{ headlineParts()[2] }}
          } @else {
            {{ 'dashboard.headline' | t }}
          }
        </h1>
        <p class="hero__sub reveal" style="--i: 3">
          {{ 'dashboard.sub' | t }}
        </p>
      </div>
    </section>

    <!-- Input -->
    <section class="input-section reveal" style="--i: 4">
      <div class="input-section__inner">
        <textarea
          [(ngModel)]="narrative"
          class="input-section__field"
          [placeholder]="'dashboard.textarea_placeholder' | t"
          rows="4"></textarea>
        <button
          (click)="startAnalysis()"
          [disabled]="!narrative.trim() || analyzing()"
          class="input-section__btn">
          {{ analyzing() ? ('dashboard.analyzing' | t) : ('dashboard.analyze_btn' | t) }}
        </button>
      </div>
    </section>

    <!-- Recent -->
    @if (recentClaims().length) {
      <section class="recent reveal" style="--i: 5">
        <div class="recent__inner">
          <div class="recent__header">
            <h2 class="recent__title">{{ 'dashboard.recent_title' | t }}</h2>
            @if (selectedIds().length) {
              <div class="recent__bulk">
                <span class="recent__bulk-count">{{ 'dashboard.selected' | t: { count: selectedIds().length } }}</span>
                <button class="recent__bulk-delete" (click)="confirmBulkDelete()">{{ 'dashboard.delete_selected' | t }}</button>
              </div>
            }
          </div>
          <div class="recent__list">
            @for (claim of recentClaims(); track claim.claim_id) {
              <div class="recent__item" [class.recent__item--selected]="selectedIds().includes(claim.claim_id)">
                <input
                  type="checkbox"
                  class="recent__check"
                  [checked]="selectedIds().includes(claim.claim_id)"
                  (change)="toggleSelect(claim.claim_id, $event)"
                  [attr.aria-label]="'dashboard.select_claim' | t">
                <button (click)="viewClaim(claim.claim_id)" class="recent__main">
                  <span class="recent__narrative">{{ claim.narrative }}</span>
                  <span class="recent__meta" [class.recent__meta--failed]="claim.status === 'failed'"
                    [class.recent__meta--pending]="claim.status === 'pending'">
                    {{ statusLabel(claim.status) }} &middot; {{ claim.created_at | date:'short' }}
                  </span>
                </button>
                <button
                  class="recent__delete"
                  (click)="confirmDelete(claim)"
                  [attr.aria-label]="'dashboard.delete_claim' | t"
                  title="{{ 'dashboard.delete_claim' | t }}">&times;</button>
              </div>
            }
          </div>
        </div>
      </section>
    }

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

    /* Warnings */
    .warn {
      padding: var(--space-sm) var(--space-lg);
      background: oklch(22% 0.02 25);
      border-bottom: 1px solid oklch(40% 0.1 25);
    }
    .warn--yellow {
      background: oklch(22% 0.02 85);
      border-bottom-color: oklch(40% 0.1 85);
    }
    .warn__inner {
      max-width: 52rem;
      margin: 0 auto;
      display: flex;
      align-items: center;
      gap: var(--space-sm);
    }
    .warn__icon {
      font-family: var(--font-display);
      font-size: var(--text-md);
      color: var(--color-danger);
      flex-shrink: 0;
    }
    .warn--yellow .warn__icon { color: var(--color-warning); }
    .warn__text {
      font-size: var(--text-sm);
      color: var(--color-ink);
      flex: 1;
    }
    .warn__btn {
      background: none;
      border: 1px solid var(--color-ink);
      color: var(--color-ink);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: var(--space-2xs) var(--space-sm);
      cursor: pointer;
      transition: opacity var(--dur-short) var(--ease-out);
      flex-shrink: 0;
    }
    .warn__btn:hover { opacity: 0.7; }
    .warn__dismiss {
      background: none;
      border: none;
      color: var(--color-muted);
      font-size: var(--text-md);
      cursor: pointer;
      padding: 0 var(--space-xs);
      line-height: 1;
    }

    /* Hero */
    .hero {
      padding: var(--space-4xl) var(--space-lg) var(--space-2xl);
      max-width: 52rem;
      margin: 0 auto;
    }
    .hero__eyebrow {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-accent);
      letter-spacing: 0.12em;
      text-transform: uppercase;
      margin-bottom: var(--space-lg);
    }
    .hero__display {
      font-size: var(--text-display);
      line-height: 1.02;
      color: var(--color-ink);
      max-width: 18ch;
    }
    .hero__accent {
      font-style: normal;
      color: var(--color-accent);
    }
    .hero__sub {
      font-size: var(--text-md);
      color: var(--color-muted);
      max-width: 42ch;
      margin-top: var(--space-lg);
      line-height: 1.55;
    }

    /* Input */
    .input-section {
      padding: 0 var(--space-lg) var(--space-3xl);
      max-width: 52rem;
      margin: 0 auto;
    }
    .input-section__field {
      width: 100%;
      background: var(--color-paper-2);
      border: none;
      border-top: 1px solid var(--color-rule);
      color: var(--color-ink);
      font-family: var(--font-body);
      font-size: var(--text-base);
      font-weight: 350;
      padding: var(--space-lg);
      resize: none;
      line-height: 1.55;
    }
    .input-section__field::placeholder {
      color: var(--color-dim);
    }
    .input-section__field:focus {
      outline: none;
      border-top-color: var(--color-accent);
    }
    .input-section__btn {
      display: inline-block;
      margin-top: var(--space-lg);
      padding: var(--space-md) var(--space-xl);
      background: var(--color-accent);
      color: var(--color-paper);
      border: none;
      font-family: var(--font-display);
      font-size: var(--text-md);
      text-transform: uppercase;
      letter-spacing: 0.02em;
      cursor: pointer;
      transition: opacity var(--dur-short) var(--ease-out);
    }
    .input-section__btn:hover { opacity: 0.9; }
    .input-section__btn:disabled { opacity: 0.3; cursor: not-allowed; }

    /* Recent */
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

    /* Footer */
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
      .hero { padding: var(--space-3xl) var(--space-md) var(--space-xl); }
      .hero__display { font-size: clamp(2rem, 8vw, 3.5rem); }
      .input-section, .recent, .footer { padding-left: var(--space-md); padding-right: var(--space-md); }
      .warn__inner { flex-wrap: wrap; }
    }
  `],
})
export class DashboardComponent implements OnInit {
  narrative = '';
  recentClaims = signal<any[]>([]);
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

    this.narrativeService.getClaims().subscribe({
      next: (claims) => this.recentClaims.set(claims),
      error: () => {},
    });

    this.settingsService.getSettings().subscribe({
      next: (settings: RuntimeSettings) => {
        this.llmConfigured.set(!!(settings.llm_endpoint && settings.llm_endpoint.trim()));
        this.sectorsConfigured.set(!!(settings.sectors_api_key && settings.sectors_api_key.trim()));
      },
      error: () => {
        this.llmConfigured.set(false);
        this.sectorsConfigured.set(false);
      },
    });
  }

  startAnalysis() {
    if (this.narrative.trim() && !this.analyzing()) {
      this.analyzing.set(true);
      this.router.navigate(['/claim'], { queryParams: { narrative: this.narrative } });
    }
  }

  statusLabel(status: string): string {
    switch (status) {
      case 'completed': return this.i18n.t('status.completed');
      case 'failed': return this.i18n.t('status.failed');
      case 'pending': return this.i18n.t('status.pending');
      default: return status;
    }
  }

  viewClaim(claimId: string) {
    this.router.navigate(['/results', claimId]);
  }

  toggleSelect(claimId: string, event: Event) {
    const checked = (event.target as HTMLInputElement).checked;
    this.selectedIds.update(ids => checked ? [...ids, claimId] : ids.filter(id => id !== claimId));
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

  private updateHeadline() {
    const raw = this.i18n.t('dashboard.headline');
    const parts = raw.split('{{_}}');
    this.headlineParts.set(parts);
  }
}
