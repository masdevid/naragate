import { Component, EventEmitter, Input, Output, signal } from '@angular/core';
import { TPipe } from '../../pipes/t.pipe';

/** The signed-in account email with a dropdown (Logout). */
@Component({
  selector: 'app-nav-account-menu',
  standalone: true,
  imports: [TPipe],
  template: `
    <div class="acct">
      <button class="acct__btn" [attr.aria-expanded]="open()" [title]="email" (click)="toggle()">
        <span class="acct__email">{{ email }}</span>
        <span class="acct__caret">&#9662;</span>
      </button>

      @if (open()) {
        <div class="acct__backdrop" (click)="open.set(false)"></div>
        <div class="acct__menu" role="menu">
          <button class="acct__item" role="menuitem" (click)="onLogout()">{{ 'nav.logout' | t }}</button>
        </div>
      }
    </div>
  `,
  styles: [`
    :host { display: inline-block; }
    .acct { position: relative; }
    .acct__btn {
      display: inline-flex;
      align-items: center;
      gap: var(--space-2xs);
      background: none;
      border: 1px solid transparent;
      color: var(--color-muted);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      letter-spacing: 0.04em;
      cursor: pointer;
      padding: var(--space-3xs) var(--space-xs);
      transition: color var(--dur-short) var(--ease-out), border-color var(--dur-short) var(--ease-out);
    }
    .acct__btn:hover { color: var(--color-ink); border-color: var(--color-accent); }
    .acct__email { max-width: 12rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .acct__caret { color: var(--color-dim); }
    .acct__backdrop { position: fixed; inset: 0; z-index: 1; }
    .acct__menu {
      position: absolute;
      right: 0;
      top: calc(100% + var(--space-2xs));
      z-index: 2;
      min-width: 10rem;
      background: var(--color-paper-2);
      border: 1px solid var(--color-rule);
      padding: var(--space-2xs);
    }
    .acct__item {
      display: block;
      width: 100%;
      text-align: left;
      background: none;
      border: none;
      color: var(--color-muted);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      cursor: pointer;
      padding: var(--space-xs) var(--space-sm);
    }
    .acct__item:hover { color: var(--color-ink); background: var(--color-paper-3); }
  `],
})
export class NavAccountMenuComponent {
  @Input() email: string | null = '';
  @Output() logout = new EventEmitter<void>();

  open = signal(false);

  toggle() {
    this.open.update(v => !v);
  }

  onLogout() {
    this.open.set(false);
    this.logout.emit();
  }
}
