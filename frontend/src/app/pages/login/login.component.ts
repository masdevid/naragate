import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { I18nService } from '../../services/i18n.service';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule, TPipe],
  template: `
    <div class="login">
      <div class="login__card">
        <h1 class="login__title">{{ 'login.title' | t }}</h1>
        <p class="login__sub">{{ 'login.sub' | t }}</p>

        <label class="login__label">{{ 'login.email' | t }}</label>
        <input class="login__input" type="email" name="email" autocomplete="email"
          [(ngModel)]="email" (keyup.enter)="submit()" placeholder="name@example.com">

        <label class="login__label">{{ 'login.password' | t }}</label>
        <input class="login__input" type="password" name="password" autocomplete="current-password"
          [(ngModel)]="password" (keyup.enter)="submit()">

        <label class="login__label">
          {{ 'login.api_key' | t }} <span class="login__optional">({{ 'login.optional' | t }})</span>
        </label>
        <input class="login__input" type="text" name="apiKey" autocomplete="off"
          [(ngModel)]="apiKey" (keyup.enter)="submit()"
          [placeholder]="'settings.sectors_key_placeholder' | t">
        <p class="login__hint">{{ 'login.api_key_hint' | t }}</p>

        @if (error()) {
          <p class="login__error">{{ error() }}</p>
        }

        <button class="login__btn" [disabled]="loading()" (click)="submit()">
          {{ loading() ? ('login.submitting' | t) : ('login.submit' | t) }}
        </button>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; }
    .login { min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: var(--space-lg); }
    .login__card {
      width: 100%; max-width: 24rem; background: var(--color-paper-2);
      border: 1px solid var(--color-rule); padding: var(--space-2xl);
    }
    .login__title { font-family: var(--font-display); font-size: var(--text-lg); text-transform: uppercase; margin-bottom: var(--space-xs); }
    .login__sub { font-size: var(--text-sm); color: var(--color-muted); margin-bottom: var(--space-xl); }
    .login__label { display: block; font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-dim); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: var(--space-3xs); }
    .login__input {
      width: 100%; margin-bottom: var(--space-md); padding: var(--space-sm);
      background: var(--color-paper-3); border: 1px solid var(--color-rule);
      color: var(--color-ink); font-family: var(--font-mono); font-size: var(--text-sm);
    }
    .login__optional { color: var(--color-dim); text-transform: none; letter-spacing: 0; }
    .login__hint { font-size: var(--text-xs); color: var(--color-dim); margin: calc(-1 * var(--space-2xs)) 0 var(--space-md); }
    .login__error { font-size: var(--text-sm); color: var(--color-danger); margin-bottom: var(--space-md); }
    .login__btn {
      width: 100%; padding: var(--space-md); border: none; background: var(--color-accent);
      color: var(--color-paper); font-family: var(--font-mono); font-size: var(--text-sm);
      text-transform: uppercase; letter-spacing: 0.04em; cursor: pointer;
    }
    .login__btn:disabled { opacity: 0.6; cursor: default; }
  `],
})
export class LoginComponent {
  private auth = inject(AuthService);
  private router = inject(Router);
  private i18n = inject(I18nService);

  email = '';
  password = '';
  apiKey = '';
  loading = signal(false);
  error = signal('');

  submit() {
    if (!this.email || !this.password) {
      this.error.set(this.i18n.t('login.required'));
      return;
    }
    this.error.set('');
    this.loading.set(true);
    this.auth.login(this.email.trim(), this.password, this.apiKey).subscribe({
      next: () => {
        this.loading.set(false);
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(err?.message || this.i18n.t('login.failed'));
      },
    });
  }
}
