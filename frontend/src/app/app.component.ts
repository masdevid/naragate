import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive, Router, NavigationEnd } from '@angular/router';
import { UpperCasePipe } from '@angular/common';
import { I18nService } from './services/i18n.service';
import { SettingsService } from './services/settings.service';
import { UsageService } from './services/usage.service';
import { AuthService } from './services/auth.service';
import { NaraWordmarkComponent } from './components/nara-wordmark/nara-wordmark.component';
import { SectorsHackathonComponent } from './components/sectors-hackathon/sectors-hackathon.component';
import { ScrollTopComponent } from './components/scroll-top/scroll-top.component';
import { TPipe } from './pipes/t.pipe';

interface NavItem {
  route: string;
  labelKey: string;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, TPipe, UpperCasePipe, NaraWordmarkComponent, SectorsHackathonComponent, ScrollTopComponent],
  template: `
    @if (!isLoginPage()) {
    <nav class="nav" [class.nav--open]="menuOpen()">
      <a routerLink="/dashboard" class="nav__brand" (click)="closeMenu()"><app-nara-wordmark /></a>

      <div class="nav__links">
        @for (item of menuItems; track item.route) {
          <a routerLink="{{ item.route }}" routerLinkActive="nav__link--active"
            [routerLinkActiveOptions]="{ exact: item.route === '/dashboard' }"
            class="nav__link" (click)="closeMenu()">{{ item.labelKey | t }}</a>
        }
        <div class="nav__lang">
          <a routerLink="/usage" class="nav__credit" (click)="closeMenu()">
            @if (credit()) {
              <span class="nav__credit-val"
                [class.nav__credit-val--ok]="creditLevel() === 'ok'"
                [class.nav__credit-val--warn]="creditLevel() === 'warn'"
                [class.nav__credit-val--danger]="creditLevel() === 'danger'">
                {{ 'nav.credit' | t }} {{ credit()!.remaining }} / {{ credit()!.budget }}
              </span>
            } @else {
              {{ 'nav.credit' | t }}
            }
          </a>
          @for (lang of langs; track lang.code) {
            <button class="nav__lang-btn" [class.nav__lang-btn--active]="i18n.language() === lang.code"
              (click)="i18n.setLanguage(lang.code)">
              {{ lang.code | uppercase }}
            </button>
          }
          <button class="nav__lang-btn" (click)="logout()">{{ 'nav.logout' | t }}</button>
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
          <a routerLink="/usage" class="nav__panel-credit" (click)="closeMenu()">{{ 'nav.credit' | t }}</a>
          <div class="nav__panel-lang">
            @for (lang of langs; track lang.code) {
              <button class="nav__lang-btn" [class.nav__lang-btn--active]="i18n.language() === lang.code"
                (click)="i18n.setLanguage(lang.code)">
                {{ lang.code | uppercase }}
              </button>
            }
          </div>
          <button class="nav__panel-link" (click)="logout()">{{ 'nav.logout' | t }}</button>
        </div>
      }
    </nav>
    }
    <router-outlet></router-outlet>
    <app-scroll-top/>
    <footer class="disclaimer">
      <p class="disclaimer__text">{{ 'disclaimer.text' | t }}</p>
      <div class="disclaimer__bottom">
        <p class="disclaimer__copy">&copy; 2026 {{ 'footer.copyright' | t }}</p>
        <app-sectors-hackathon />
      </div>
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
    .nav__credit {
      background: none;
      border: 1px solid transparent;
      color: var(--color-muted);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      letter-spacing: 0.04em;
      text-decoration: none;
      text-transform: uppercase;
      cursor: pointer;
      padding: var(--space-3xs) var(--space-xs);
      transition: all var(--dur-short) var(--ease-out);
    }
    .nav__credit:hover {
      color: var(--color-ink);
      border-color: var(--color-accent);
    }
    .nav__credit-val--ok {
      color: var(--color-success);
    }
    .nav__credit-val--warn {
      color: var(--color-warning);
    }
    .nav__credit-val--danger {
      color: var(--color-danger);
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
    .disclaimer__copy {
      font-family: var(--font-mono);
      font-size: var(--text-2xs);
      color: var(--color-dim);
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    .disclaimer__bottom {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--space-md);
      margin-top: var(--space-xs);
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
      .nav__panel-credit {
        display: flex;
        align-items: baseline;
        gap: var(--space-2xs);
        font-family: var(--font-mono);
        font-size: var(--text-xs);
        color: var(--color-muted);
        text-decoration: none;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        padding: var(--space-sm) 0;
        border-bottom: 1px solid var(--color-paper-3);
      }
      .nav__panel-credit:hover { color: var(--color-ink); }
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
  private usageService = inject(UsageService);
  private authService = inject(AuthService);

  isLoginPage = signal(false);

  menuItems: NavItem[] = [
    { route: '/dashboard', labelKey: 'nav.dashboard' },
    { route: '/history', labelKey: 'nav.history' },
    { route: '/llm-connector', labelKey: 'nav.connector' },
    { route: '/settings', labelKey: 'nav.settings' },
  ];

  menuOpen = signal(false);
  credit = signal<{ remaining: number; budget: number } | null>(null);
  creditLevel = computed<'ok' | 'warn' | 'danger'>(() => {
    const c = this.credit();
    if (!c || c.budget <= 0) return 'ok';
    const pct = (c.remaining / c.budget) * 100;
    if (pct <= 15) return 'danger';
    if (pct <= 30) return 'warn';
    return 'ok';
  });

  constructor() {
    this.router.events.subscribe(event => {
      if (event instanceof NavigationEnd) {
        this.menuOpen.set(false);
        this.isLoginPage.set(event.urlAfterRedirects.startsWith('/login'));
        this.refreshCredit();
      }
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

  logout() {
    this.authService.logout().subscribe({
      next: () => this.router.navigate(['/login']),
      error: () => this.router.navigate(['/login']),
    });
  }

  toggleMenu() {
    this.menuOpen.update(open => !open);
  }

  closeMenu() {
    this.menuOpen.set(false);
  }

  private refreshCredit() {
    this.usageService.getUsage().subscribe({
      next: (u) => this.credit.set({ remaining: u.sectors.remaining, budget: u.sectors.budget }),
      error: () => {},
    });
  }
}