import { Component, OnInit, inject, signal, effect } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { SettingsService, RuntimeSettings } from '../../services/settings.service';
import { AuthService } from '../../services/auth.service';
import { I18nService } from '../../services/i18n.service';
import { DashboardWarningsComponent } from '../../components/dashboard-warnings/dashboard-warnings.component';
import { DashboardHeroComponent } from '../../components/dashboard-hero/dashboard-hero.component';
import { DashboardInputComponent } from '../../components/dashboard-input/dashboard-input.component';
import { sanitizeNarrative } from '../../utils/sanitize';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    RouterLink,
    DashboardWarningsComponent,
    DashboardHeroComponent,
    DashboardInputComponent,
    TPipe,
  ],
  template: `
    @if (!authenticated()) {
      <div class="dashboard__notice">
        <span class="dashboard__notice-text">{{ 'dashboard.login_notice' | t }}</span>
        <a routerLink="/login" class="dashboard__notice-btn">{{ 'login.submit' | t }}</a>
      </div>
    }

    <app-dashboard-warnings
      [setupComplete]="setupComplete()"
      [showDetailWarnings]="setupComplete()"
      [llmConfigured]="llmConfigured()"
      [sectorsConfigured]="sectorsConfigured()"
      (goSetup)="goSetup()"
      (goSettings)="goSettings()"
      (dismissLlm)="llmConfigured.set(true)"
      (dismissSectors)="sectorsConfigured.set(true)"/>

    <app-dashboard-hero [headlineParts]="headlineParts"/>

    <app-dashboard-input
      [analyzing]="analyzing()"
      [authenticated]="authenticated()"
      (analyze)="startAnalysis($event)"
      (requireLogin)="goLogin()"
      (complete)="onBulkComplete()"/>

    <a routerLink="/history" class="dashboard__history">{{ 'dashboard.view_history' | t }}</a>

    <!-- Footer -->
    <footer class="footer">
      <p class="footer__text">{{ 'dashboard.footer' | t }}</p>
    </footer>
  `,
  styles: [`
    :host { display: block; }
    .dashboard__history {
      display: block;
      max-width: 52rem;
      margin: 0 auto;
      padding: var(--space-md);
      text-align: center;
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-accent);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      text-decoration: none;
      border-top: 1px solid var(--color-rule);
    }
    .dashboard__history:hover { text-decoration: underline; }
    .dashboard__notice {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--space-md);
      max-width: 52rem;
      margin: var(--space-lg) auto 0;
      padding: var(--space-sm) var(--space-md);
      background: var(--color-paper-2);
      border: 1px solid var(--color-warning);
    }
    .dashboard__notice-text {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-muted);
    }
    .dashboard__notice-btn {
      flex-shrink: 0;
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--color-accent);
      text-decoration: none;
      border: 1px solid var(--color-accent);
      padding: var(--space-2xs) var(--space-sm);
    }
    .dashboard__notice-btn:hover { background: var(--color-accent); color: var(--color-paper); }
    .footer {
      padding: var(--space-xl) var(--space-lg);
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
  setupComplete = signal(true);
  llmConfigured = signal(true);
  sectorsConfigured = signal(true);
  headlineParts = signal<string[]>([]);
  analyzing = signal(false);

  private router = inject(Router);
  private settingsService = inject(SettingsService);
  private auth = inject(AuthService);
  private i18n = inject(I18nService);

  authenticated = this.auth.isAuthenticated;

  constructor() {
    effect(() => {
      this.i18n.language();
      this.updateHeadline();
    });
  }

  ngOnInit() {
    this.updateHeadline();

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
    const clean = sanitizeNarrative(narrative);
    if (!clean || this.analyzing()) return;
    if (!this.auth.isAuthenticated()) {
      // Landed without a session — send them to log in first.
      this.router.navigate(['/login']);
      return;
    }
    this.analyzing.set(true);
    this.router.navigate(['/claim'], { queryParams: { narrative: clean } });
  }

  goLogin() {
    this.router.navigate(['/login']);
  }

  onBulkComplete() {
    this.router.navigate(['/history']);
  }

  goSettings() {
    this.router.navigate(['/settings']);
  }

  goSetup() {
    this.router.navigate(['/setup']);
  }

  private updateHeadline() {
    const raw = this.i18n.t('dashboard.headline');
    const parts = raw.split('{{_}}');
    this.headlineParts.set(parts);
  }
}