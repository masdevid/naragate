import { Component, OnInit, inject } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive, Router } from '@angular/router';
import { UpperCasePipe } from '@angular/common';
import { I18nService } from './services/i18n.service';
import { SettingsService } from './services/settings.service';
import { TPipe } from './pipes/t.pipe';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, TPipe, UpperCasePipe],
  template: `
    <nav class="nav">
      <a routerLink="/dashboard" class="nav__brand">Naragate</a>
      <div class="nav__links">
        <a routerLink="/dashboard" routerLinkActive="nav__link--active"
          [routerLinkActiveOptions]="{ exact: true }" class="nav__link">{{ 'nav.dashboard' | t }}</a>
        <a routerLink="/history" routerLinkActive="nav__link--active" class="nav__link">{{ 'nav.history' | t }}</a>
        <a routerLink="/settings" routerLinkActive="nav__link--active" class="nav__link">{{ 'nav.settings' | t }}</a>
        <a routerLink="/usage" routerLinkActive="nav__link--active" class="nav__link">{{ 'nav.usage' | t }}</a>
        <div class="nav__lang">
          @for (lang of langs; track lang.code) {
            <button class="nav__lang-btn" [class.nav__lang-btn--active]="i18n.language() === lang.code"
              (click)="i18n.setLanguage(lang.code)">
              {{ lang.code | uppercase }}
            </button>
          }
        </div>
      </div>
    </nav>
    <router-outlet></router-outlet>
    <footer class="disclaimer">
      <p class="disclaimer__text">{{ 'disclaimer.text' | t }}</p>
    </footer>
  `,
  styles: [`
    .nav {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--space-md) var(--space-lg);
      border-bottom: 1px solid var(--color-rule);
      max-width: 52rem;
      margin: 0 auto;
    }
    .nav__brand {
      font-family: var(--font-display);
      font-size: var(--text-md);
      text-transform: uppercase;
      letter-spacing: 0.02em;
      color: var(--color-ink);
      text-decoration: none;
    }
    .nav__links {
      display: flex;
      align-items: center;
      gap: var(--space-lg);
    }
    .nav__link {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-muted);
      text-decoration: none;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      transition: color var(--dur-short) var(--ease-out);
    }
    .nav__link:hover, .nav__link--active {
      color: var(--color-ink);
    }
    .nav__lang {
      display: flex;
      gap: var(--space-2xs);
      padding-left: var(--space-sm);
      border-left: 1px solid var(--color-rule);
    }
    .nav__lang-btn {
      background: none;
      border: 1px solid transparent;
      color: var(--color-dim);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      letter-spacing: 0.04em;
      cursor: pointer;
      padding: var(--space-3xs) var(--space-xs);
      transition: all var(--dur-short) var(--ease-out);
    }
    .nav__lang-btn:hover {
      color: var(--color-muted);
    }
    .nav__lang-btn--active {
      border-color: var(--color-accent);
      color: var(--color-accent);
    }
    .disclaimer {
      padding: var(--space-lg);
      border-top: 1px solid var(--color-rule);
      max-width: 52rem;
      margin: 0 auto;
    }
    .disclaimer__text {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      line-height: 1.5;
      letter-spacing: 0.02em;
    }
  `],
})
export class AppComponent implements OnInit {
  i18n = inject(I18nService);
  langs = this.i18n.getLanguages();
  private router = inject(Router);
  private settingsService = inject(SettingsService);

  ngOnInit() {
    let dismissed = false;
    try { dismissed = localStorage.getItem('naragate_setup_dismissed') === '1'; } catch {}
    if (dismissed || this.router.url.startsWith('/setup')) return;
    this.settingsService.getSetupStatus().subscribe({
      next: (status) => {
        if (!status.complete) {
          this.router.navigate(['/setup']);
        }
      },
      error: () => {},
    });
  }
}
