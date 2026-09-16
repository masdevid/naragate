import { Component, Input, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiToken, AuthService } from '../../services/auth.service';
import { TPipe } from '../../pipes/t.pipe';

/**
 * Mints API tokens for non-web surfaces (MCP, skills, agents). A token resolves
 * to the same email as the web session, so the harness uses this user's own
 * Sectors key, evidence cache and credit ledger. The raw token is shown once.
 */
@Component({
  selector: 'app-settings-mcp-section',
  standalone: true,
  imports: [FormsModule, TPipe],
  template: `
    <section class="sect">
      <h2 class="sect__heading">{{ 'settings.section_mcp' | t }}</h2>
      <p class="sect__hint">{{ 'settings.section_mcp_hint' | t }}</p>

      @if (!authenticated) {
        <p class="sect__hint">{{ 'settings.mcp_signin_required' | t }}</p>
      } @else {
        @if (newToken()) {
          <div class="sect__new">
            <p class="sect__new-label">{{ 'settings.mcp_new_token' | t }}</p>
            <div class="sect__new-row">
              <code class="sect__token">{{ newToken() }}</code>
              <button class="sect__btn" (click)="copy()">
                {{ (copied() ? 'settings.mcp_copied' : 'settings.mcp_copy') | t }}
              </button>
            </div>
          </div>
        }

        <div class="sect__create">
          <input class="sect__input" [(ngModel)]="name"
            [placeholder]="'settings.mcp_token_name_placeholder' | t"/>
          <button class="sect__btn sect__btn--accent" (click)="create()" [disabled]="creating()">
            {{ (creating() ? 'settings.mcp_creating' : 'settings.mcp_create') | t }}
          </button>
        </div>

        @if (error()) {
          <p class="sect__error">{{ error() }}</p>
        }

        @if (tokens().length) {
          <ul class="sect__list">
            @for (tk of tokens(); track tk.id) {
              <li class="sect__item">
                <span class="sect__item-name">{{ tk.name }}</span>
                <span class="sect__item-meta">
                  {{ tk.prefix }}… · {{ 'settings.mcp_created' | t }} {{ shortDate(tk.created_at) }}
                  · {{ 'settings.mcp_last_used' | t }} {{ tk.last_used_at ? shortDate(tk.last_used_at) : ('settings.mcp_never_used' | t) }}
                </span>
                <button class="sect__revoke" (click)="revoke(tk)">{{ 'settings.mcp_revoke' | t }}</button>
              </li>
            }
          </ul>
        } @else {
          <p class="sect__hint">{{ 'settings.mcp_empty' | t }}</p>
        }

        <p class="sect__hint">{{ 'settings.mcp_env_hint' | t }}</p>
      }
    </section>
  `,
  styles: [`
    .sect { display: block; border-top: 1px solid var(--color-rule); padding: var(--space-xl) 0; }
    .sect__heading {
      font-family: var(--font-display);
      font-size: var(--text-md);
      text-transform: uppercase;
      margin-bottom: var(--space-xs);
    }
    .sect__hint {
      font-size: var(--text-xs);
      color: var(--color-dim);
      margin-bottom: var(--space-md);
      line-height: 1.5;
    }
    .sect__new {
      border: 1px solid var(--color-accent);
      padding: var(--space-sm) var(--space-md);
      margin-bottom: var(--space-md);
    }
    .sect__new-label {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-accent);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-bottom: var(--space-xs);
    }
    .sect__new-row { display: flex; align-items: center; gap: var(--space-sm); flex-wrap: wrap; }
    .sect__token {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-ink);
      word-break: break-all;
      flex: 1;
      min-width: 12rem;
    }
    .sect__create { display: flex; gap: var(--space-sm); margin-bottom: var(--space-md); }
    .sect__input {
      flex: 1;
      height: var(--ctl-h);
      background: var(--color-paper-2);
      border: 1px solid var(--color-paper-3);
      color: var(--color-ink);
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      padding: 0 var(--space-md);
    }
    .sect__input:focus { outline: none; border-color: var(--color-accent); }
    .sect__input::placeholder { color: var(--color-dim); }
    .sect__btn {
      height: var(--ctl-h);
      background: none;
      border: 1px solid var(--color-paper-3);
      color: var(--color-muted);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: 0 var(--space-sm);
      cursor: pointer;
      white-space: nowrap;
      transition: all var(--dur-short) var(--ease-out);
    }
    .sect__btn:hover:not(:disabled) { border-color: var(--color-accent); color: var(--color-accent); }
    .sect__btn:disabled { opacity: 0.3; cursor: not-allowed; }
    .sect__btn--accent { border-color: var(--color-accent); color: var(--color-accent); }
    .sect__list { list-style: none; margin: 0 0 var(--space-md); padding: 0; }
    .sect__item {
      display: flex;
      align-items: center;
      gap: var(--space-sm);
      flex-wrap: wrap;
      padding: var(--space-2xs) 0;
      border-bottom: 1px solid var(--color-rule);
    }
    .sect__item-name {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-ink);
    }
    .sect__item-meta {
      flex: 1;
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      min-width: 12rem;
    }
    .sect__revoke {
      background: none;
      border: none;
      color: var(--color-danger);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      cursor: pointer;
      padding: 0;
    }
    .sect__revoke:hover { text-decoration: underline; }
    .sect__error { font-size: var(--text-xs); color: var(--color-danger); margin-bottom: var(--space-md); }
  `],
})
export class SettingsMcpSectionComponent implements OnInit {
  @Input() authenticated = false;

  tokens = signal<ApiToken[]>([]);
  creating = signal(false);
  newToken = signal('');
  copied = signal(false);
  error = signal('');
  name = '';

  private auth = inject(AuthService);

  ngOnInit() {
    if (this.authenticated) this.refresh();
  }

  refresh() {
    this.auth.listTokens().subscribe({
      next: tokens => this.tokens.set(tokens),
      error: () => {},
    });
  }

  create() {
    if (this.creating()) return;
    this.creating.set(true);
    this.error.set('');
    this.copied.set(false);
    this.auth.createToken(this.name.trim()).subscribe({
      next: token => {
        this.creating.set(false);
        this.name = '';
        this.newToken.set(token.token || '');
        this.refresh();
      },
      error: (err: Error) => {
        this.creating.set(false);
        this.error.set(err?.message || 'Request failed');
      },
    });
  }

  revoke(tk: ApiToken) {
    this.auth.revokeToken(tk.id).subscribe({
      next: () => this.refresh(),
      error: (err: Error) => this.error.set(err?.message || 'Request failed'),
    });
  }

  copy() {
    navigator.clipboard?.writeText(this.newToken()).then(
      () => this.copied.set(true),
      () => {},
    );
  }

  shortDate(iso: string): string {
    return (iso || '').slice(0, 10);
  }
}
