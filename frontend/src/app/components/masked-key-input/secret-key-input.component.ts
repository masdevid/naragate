import { Component, Input, Output, EventEmitter, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { TPipe } from '../../pipes/t.pipe';

/**
 * Secret key input with a true "saved" state.
 *
 * The server never hands the browser the real key — it sends a masked value
 * like `42f599...954d`. This component distinguishes three states:
 *   - saved (masked placeholder): shows bullets + last-4, with Replace / Clear
 *   - editing: a password input with a show/hide toggle
 *   - empty: plain password input
 *
 * Emits `valueChange` ONLY on commit (blur / Enter / Clear), and only ever a
 * real value (or '' to clear) — never the masked placeholder, so a reload can
 * never re-save a masked sentinel over the real key.
 */
@Component({
  selector: 'app-secret-key-input',
  standalone: true,
  imports: [FormsModule, TPipe],
  template: `
    @if (isSaved() && !editing()) {
      <div class="secret" [class]="inputClass + ' secret--saved'">
        <span class="secret__display">{{ maskDisplay() }}<span class="secret__tail">…{{ last4() }}</span></span>
        <span class="secret__save-label">{{ 'settings.key_saved' | t }}</span>
        <button type="button" class="secret__action" (click)="startReplace()">{{ 'settings.key_replace' | t }}</button>
        <button type="button" class="secret__action secret__action--danger" (click)="clearKey()">{{ 'settings.key_clear' | t }}</button>
      </div>
    } @else {
      <div class="secret" [class]="inputClass + ' secret--edit'">
        <input
          [type]="revealed() ? 'text' : 'password'"
          [ngModel]="draft()"
          (ngModelChange)="onType($event)"
          (focus)="editing.set(true)"
          (blur)="commit()"
          (keydown.enter)="commit()"
          spellcheck="false"
          autocomplete="new-password"
          [placeholder]="isSaved() ? ('settings.key_replace_placeholder' | t) : placeholder">
        <button type="button" class="secret__reveal"
          (click)="revealed.set(!revealed())"
          [attr.aria-label]="revealed() ? 'Hide key' : 'Show key'">
          {{ revealed() ? ('settings.key_hide' | t) : ('settings.key_show' | t) }}
        </button>
        @if (isSaved()) {
          <button type="button" class="secret__cancel" (click)="cancelReplace()">{{ 'settings.key_cancel' | t }}</button>
        }
      </div>
    }
  `,
  styles: [`
    .secret {
      display: flex;
      align-items: center;
      gap: var(--space-sm);
      background: var(--color-paper-2);
      border: 1px solid var(--color-paper-3);
      color: var(--color-ink);
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      padding: var(--space-sm) var(--space-md);
      min-height: 2.6rem;
      transition: border-color var(--dur-short) var(--ease-out);
    }
    .secret:focus-within { border-color: var(--color-accent); }
    .secret--saved { color: var(--color-dim); }
    .secret__display { letter-spacing: 0.12em; white-space: nowrap; }
    .secret__tail { letter-spacing: 0.02em; }
    .secret__save-label {
      font-size: var(--text-xs);
      color: var(--color-success);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-left: var(--space-2xs);
    }
    .secret input {
      flex: 1;
      min-width: 0;
      background: none;
      border: none;
      color: var(--color-ink);
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      outline: none;
    }
    .secret input::placeholder { color: var(--color-dim); }
    .secret__action {
      background: none;
      border: 1px solid var(--color-paper-3);
      color: var(--color-muted);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: var(--space-3xs) var(--space-sm);
      cursor: pointer;
      white-space: nowrap;
      flex-shrink: 0;
      transition: all var(--dur-short) var(--ease-out);
    }
    .secret__action:hover { border-color: var(--color-dim); color: var(--color-ink); }
    .secret__action--danger:hover { border-color: var(--color-danger); color: var(--color-danger); }
    .secret__reveal, .secret__cancel {
      background: none;
      border: none;
      color: var(--color-dim);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      cursor: pointer;
      white-space: nowrap;
      flex-shrink: 0;
    }
    .secret__reveal:hover { color: var(--color-ink); }
    .secret__cancel:hover { color: var(--color-danger); }
    .secret--edit { padding: var(--space-3xs) var(--space-md); }
    .secret--edit input { padding: var(--space-sm) 0; }
  `],
})
export class SecretKeyInputComponent {
  @Input() placeholder = '';
  @Input() inputClass = '';
  @Output() valueChange = new EventEmitter<string>();

  private _value = '';
  draft = signal('');
  revealed = signal(false);
  editing = signal(false);

  @Input() set value(v: string | undefined | null) {
    this._value = v || '';
    if (this.isMasked(this._value)) {
      this.draft.set('');
    } else {
      this.draft.set(this._value);
    }
  }

  get value(): string {
    return this._value;
  }

  isMasked(v: string): boolean {
    return v.includes('...') || v.includes('••••');
  }

  isSaved(): boolean {
    return this.isMasked(this._value) || (!!this._value && this._value.length > 12 && this._value.includes('.'));
  }

  last4(): string {
    return this._value ? this._value.slice(-4) : '';
  }

  maskDisplay(): string {
    const n = Math.max(8, this._value.length - 4);
    return '•'.repeat(Math.min(n, 16));
  }

  startReplace() {
    this.draft.set('');
    this.revealed.set(false);
    this.editing.set(true);
  }

  cancelReplace() {
    this.editing.set(false);
    this.draft.set('');
  }

  clearKey() {
    this._value = '';
    this.draft.set('');
    this.editing.set(false);
    this.valueChange.emit('');
  }

  onType(v: string) {
    this.draft.set(v);
  }

  /** Commit the drafted value — only emits a real string (or '' if emptied). */
  commit() {
    if (this.isSaved() && this.editing() && !this.draft().trim()) {
      // Replaced-to-edit then cleared without typing → back to saved state.
      this.editing.set(false);
      this.draft.set('');
      return;
    }
    this.editing.set(false);
    const v = this.draft();
    if (v === this._value) {
      return;
    }
    this._value = v;
    this.valueChange.emit(v);
  }
}