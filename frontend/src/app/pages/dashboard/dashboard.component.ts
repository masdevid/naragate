import { Component, OnInit, inject, signal, effect } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { SettingsService, RuntimeSettings } from '../../services/settings.service';
import { I18nService } from '../../services/i18n.service';
import { DashboardWarningsComponent } from '../../components/dashboard-warnings/dashboard-warnings.component';
import { DashboardHeroComponent } from '../../components/dashboard-hero/dashboard-hero.component';
import { DashboardInputComponent } from '../../components/dashboard-input/dashboard-input.component';
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
      (analyze)="startAnalysis($event)"
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
      padding: var(--space-lg);
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
  setupComplete = signal(true);
  llmConfigured = signal(true);
  sectorsConfigured = signal(true);
  headlineParts = signal<string[]>([]);
  analyzing = signal(false);

  private router = inject(Router);
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