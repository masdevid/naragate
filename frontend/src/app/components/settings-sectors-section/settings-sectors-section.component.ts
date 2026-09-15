import { Component, Input, Output, EventEmitter, inject, signal } from '@angular/core';
import { SettingsService, SectorsValidateResult } from '../../services/settings.service';
import { TPipe } from '../../pipes/t.pipe';
import { SecretKeyInputComponent } from '../masked-key-input/secret-key-input.component';

/**
 * Settings section for the Sectors API key. The key is bound to the logged-in
 * Sectors account (email), not an IP address.
 */
@Component({
  selector: 'app-settings-sectors-section',
  standalone: true,
  imports: [TPipe, SecretKeyInputComponent],
  template: `
    <section class="sect">
      <h2 class="sect__heading">{{ 'settings.section_sectors' | t }}</h2>

      @if (boundEmail) {
        <p class="sect__hint">{{ 'settings.sectors_bound_email' | t:{email: boundEmail} }}</p>
      }

      <div class="sect__field">
        <label class="sect__label">{{ 'settings.field_sectors_key' | t }}</label>
        <div class="sect__input-row">
          <app-secret-key-input [value]="sectorsApiKey"
            (valueChange)="fieldChange.emit({ field: 'sectors_api_key', value: $event })"
            inputClass="sect__input sect__input--flex"
            [placeholder]="'settings.sectors_key_placeholder' | t"/>
          <button (click)="validateSectorsKey()" [disabled]="!sectorsKeyPresent() || sectorsValidating()"
            class="sect__validate-btn">
            {{ 'settings.sectors_validate' | t }}
          </button>
        </div>
        <span class="sect__status" [class.sect__status--ok]="sectorsValidation()?.ok === true"
          [class.sect__status--err]="sectorsValidation()?.ok === false"
          [class.sect__status--loading]="sectorsValidating()">
          @if (sectorsValidating()) {
            {{ 'settings.validating' | t }}
          } @else if (sectorsValidation()?.ok === true) {
            {{ 'settings.sectors_valid_ok' | t }}
          } @else if (sectorsValidation()?.ok === false) {
            {{ 'settings.sectors_valid_error' | t }}
          }
        </span>
      </div>
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
      margin-bottom: var(--space-lg);
    }
    .sect__field { margin-bottom: var(--space-md); }
    .sect__label {
      display: block;
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-muted);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin-bottom: var(--space-2xs);
    }
    .sect__input {
      width: 100%;
      height: var(--ctl-h);
      background: var(--color-paper-2);
      border: 1px solid var(--color-paper-3);
      color: var(--color-ink);
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      padding: 0 var(--space-md);
      transition: border-color var(--dur-short) var(--ease-out);
    }
    .sect__input:focus { outline: none; border-color: var(--color-accent); }
    .sect__input::placeholder { color: var(--color-dim); }
    .sect__input-row { display: flex; align-items: center; gap: var(--space-md); }
    .sect__input--flex { flex: 1; }
    .sect__validate-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      height: var(--ctl-h);
      background: none;
      border: 1px solid var(--color-accent);
      color: var(--color-accent);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: 0 var(--space-sm);
      cursor: pointer;
      white-space: nowrap;
      flex-shrink: 0;
      transition: background var(--dur-short) var(--ease-out), color var(--dur-short) var(--ease-out);
    }
    .sect__validate-btn:hover { background: var(--color-accent); color: var(--color-paper); }
    .sect__validate-btn:disabled { opacity: 0.3; cursor: not-allowed; }
    .sect__status {
      display: inline-block;
      margin-top: var(--space-2xs);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .sect__status--ok { color: var(--color-success); }
    .sect__status--err { color: var(--color-danger); }
    .sect__status--loading { color: var(--color-warning); }
    @media (max-width: 640px) {
      .sect__input-row { flex-direction: column; align-items: stretch; }
    }
  `],
})
export class SettingsSectorsSectionComponent {
  @Input() sectorsApiKey: string | undefined = '';
  @Input() boundEmail: string | null = null;
  @Output() fieldChange = new EventEmitter<{ field: string; value: string }>();

  sectorsValidating = signal(false);
  sectorsValidation = signal<SectorsValidateResult | null>(null);

  private settingsService = inject(SettingsService);

  sectorsKeyPresent(): boolean {
    return !!(this.sectorsApiKey && this.sectorsApiKey.trim());
  }

  validateSectorsKey() {
    if (!this.sectorsApiKey) return;
    this.sectorsValidating.set(true);
    this.sectorsValidation.set(null);
    this.settingsService.validateSectors(this.sectorsApiKey).subscribe({
      next: (result: any) => {
        this.sectorsValidation.set(result);
        this.sectorsValidating.set(false);
      },
      error: () => {
        this.sectorsValidation.set({ ok: false, error: 'Request failed' });
        this.sectorsValidating.set(false);
      },
    });
  }
}
