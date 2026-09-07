import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive, Router, NavigationEnd } from '@angular/router';
import { UpperCasePipe } from '@angular/common';
import { I18nService } from './services/i18n.service';
import { SettingsService } from './services/settings.service';
import { TPipe } from './pipes/t.pipe';

interface NavItem {
  route: string;
  labelKey: string;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, TPipe, UpperCasePipe],
  template: `
    <nav class="nav" [class.nav--open]="menuOpen()">
      <a routerLink="/dashboard" class="nav__brand" (click)="closeMenu()">Naragate</a>

      <div class="nav__links">
        @for (item of menuItems; track item.route) {
          <a routerLink="{{ item.route }}" routerLinkActive="nav__link--active"
            [routerLinkActiveOptions]="{ exact: item.route === '/dashboard' }"
            class="nav__link" (click)="closeMenu()">{{ item.labelKey | t }}</a>
        }
        <div class="nav__lang">
          @for (lang of langs; track lang.code) {
            <button class="nav__lang-btn" [class.nav__lang-btn--active]="i18n.language() === lang.code"
              (click)="i18n.setLanguage(lang.code)">
              {{ lang.code | uppercase }}
            </button>
          }
        </div>
      </div>

      <button
        class="nav__toggle"
        [attr.aria-expanded]="menuOpen()"
        [attr.aria-label]="(menuOpen() ? 'nav.close' : 'nav.menu') | t"
        (click)="toggleMenu()">
        <span class="nav__toggle-bar"></span>
        <span class="nav__toggle-bar"></span>
        <span class="nav__toggle-bar"></span>
      </button>

      @if (menuOpen()) {
        <div class="nav__panel">
          @for (item of menuItems; track item.route) {
            <a routerLink="{{ item.route }}" routerLinkActive="nav__panel-link--active"
              [routerLinkActiveOptions]="{ exact: item.route === '/dashboard' }"
              class="nav__panel-link" (click)="closeMenu()">{{ item.labelKey | t }}</a>
          }
          <div class="nav__panel-lang">
            @for (lang of langs; track lang.code) {
              <button class="nav__lang-btn" [class.nav__lang-btn--active]="i18n.language() === lang.code"
                (click)="i18n.setLanguage(lang.code)">
                {{ lang.code | uppercase }}
              </button>
            }
          </div>
        </div>
      }
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
      gap: var(--space-md);
      padding: var(--space-md) var(--space-lg);
      border-bottom: 1px solid var(--color-rule);
      max-width: 52rem;
      margin: 0 auto;
      position: relative;
    }
    .nav__brand {
      font-family: var(--font-display);
      font-size: var(--text-md);
      text-transform: uppercase;
      letter-spacing: 0.02em;
      color: var(--color-ink);
      text-decoration: none;
      white-space: nowrap;
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
    .nav__toggle {
      display: none;
      background: none;
      border: none;
      cursor: pointer;
      padding: var(--space-2xs);
      flex-direction: column;
      gap: 5px;
    }
    .nav__toggle-bar {
      display: block;
      width: 1.25rem;
      height: 2px;
      background: var(--color-ink);
      transition: transform var(--dur-short) var(--ease-out), opacity var(--dur-short) var(--ease-out);
    }
    .nav--open .nav__toggle-bar:nth-child(1) { transform: translateY(7px) rotate(45deg); }
    .nav--open .nav__toggle-bar:nth-child(2) { opacity: 0; }
    .nav--open .nav__toggle-bar:nth-child(3) { transform: translateY(-7px) rotate(-45deg); }
    .nav__panel {
      display: none;
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
    @media (max-width: 768px) {
      .nav { padding: var(--space-sm) var(--space-md); }
      .nav__links { display: none; }
      .nav__toggle { display: flex; }
      .nav__panel {
        display: flex;
        flex-direction: column;
        gap: var(--space-2xs);
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: var(--color-paper-2);
        border-bottom: 1px solid var(--color-rule);
        padding: var(--space-md);
        z-index: var(--z-dropdown);
      }
      .nav__panel-link {
        font-family: var(--font-mono);
        font-size: var(--text-sm);
        color: var(--color-muted);
        text-decoration: none;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        padding: var(--space-sm) 0;
        border-bottom: 1px solid var(--color-paper-3);
        transition: color var(--dur-short) var(--ease-out);
      }
      .nav__panel-link:hover, .nav__panel-link--active { color: var(--color-ink); }
      .nav__panel-lang {
        display: flex;
        gap: var(--space-2xs);
        padding-top: var(--space-sm);
      }
    }
  `],
})
export class AppComponent implements OnInit {
  i18n = inject(I18nService);
  langs = this.i18n.getLanguages();
  private router = inject(Router);
  private settingsService = inject(SettingsService);

  menuItems: NavItem[] = [
    { route: '/dashboard', labelKey: 'nav.dashboard' },
    { route: '/history', labelKey: 'nav.history' },
    { route: '/settings', labelKey: 'nav.settings' },
    { route: '/usage', labelKey: 'nav.usage' },
  ];

  menuOpen = signal(false);

  constructor() {
    this.router.events.subscribe(event => {
      if (event instanceof NavigationEnd) this.menuOpen.set(false);
    });
  }

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

  toggleMenu() {
    this.menuOpen.update(open => !open);
  }

  closeMenu() {
    this.menuOpen.set(false);
  }
}