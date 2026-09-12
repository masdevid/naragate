import { Component, Input, Output, EventEmitter, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RuntimeSettings, ValidateResult } from '../../services/settings.service';
import { TPipe } from '../../pipes/t.pipe';

/**
 * LLM provider fields for the setup wizard: endpoint, API key and default model.
 * The wizard owners form state and validation; this component only surfaces
 * fields and forwards changes.
 */
@Component({
  selector: 'app-setup-llm-step',
  standalone: true,
  imports: [FormsModule, TPipe],
  template: `
    <div class="setup__llm">
      <div class="setup__field">
        <label class="setup__label">{{ 'settings.field_endpoint' | t }}</label>
        <div class="setup__input-row">
          @if (showEndpoint()) {
            <input [ngModel]="form().llm_endpoint" (ngModelChange)="endpointChange.emit($event)"
              class="setup__input setup__input--flex"
              [placeholder]="'settings.endpoint_placeholder' | t">
          } @else {
            <div class="setup__masked-display"
              [class.setup__masked-display--empty]="!maskedEndpoint()">
              {{ maskedEndpoint() || ('settings.endpoint_placeholder' | t) }}
            </div>
          }
          <button type="button" class="setup__reveal-btn"
            (click)="showEndpoint.set(!showEndpoint())">
            {{ (showEndpoint() ? 'settings.key_hide' : 'settings.key_show') | t }}
          </button>
          <span class="setup__status" [class.setup__status--ok]="validation()?.ok === true"
            [class.setup__status--err]="validation()?.ok === false"
            [class.setup__status--loading]="validating()">
            @if (validating()) {
              {{ 'settings.validating' | t }}
            } @else if (validation()?.ok === true) {
              {{ 'settings.valid_ok' | t:{count: validation()!.models.length} }}
            } @else if (validation()?.ok === false) {
              {{ 'settings.valid_error' | t }}
            }
          </span>
        </div>
      </div>

      <div class="setup__field">
        <label class="setup__label">{{ 'settings.field_api_key' | t }}</label>
        <div class="setup__masked-row">
          @if (showLlmKey()) {
            <input [ngModel]="form().llm_api_key" (ngModelChange)="fieldChange.emit({ field: 'llm_api_key', value: $event })"
              class="setup__input"
              placeholder="••••••••••••••••••••••••"
              autocomplete="new-password">
          } @else {
            <div class="setup__masked-display"
              [class.setup__masked-display--empty]="!maskedLlmKey()">
              {{ maskedLlmKey() || ('settings.api_key_placeholder' | t) }}
            </div>
          }
          <button type="button" class="setup__reveal-btn"
            (click)="showLlmKey.set(!showLlmKey())">
            {{ (showLlmKey() ? 'settings.key_hide' : 'settings.key_show') | t }}
          </button>
        </div>
      </div>

      <div class="setup__field">
        <label class="setup__label">{{ 'settings.field_model' | t }}</label>
        @if (availableModels().length) {
          <div class="setup__models">
            @for (model of availableModels(); track model) {
              <button class="setup__model-btn"
                [class.setup__model-btn--active]="form().llm_model === model"
                (click)="fieldChange.emit({ field: 'llm_model', value: model })">
                {{ model }}
              </button>
            }
          </div>
        } @else {
          <input [ngModel]="form().llm_model" (ngModelChange)="fieldChange.emit({ field: 'llm_model', value: $event })"
            class="setup__input"
            [placeholder]="'settings.field_model_placeholder' | t">
        }
      </div>
    </div>
  `,
  styles: [`
    .setup__field {
      margin-bottom: var(--space-lg);
    }
    .setup__label {
      display: block;
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-muted);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin-bottom: var(--space-2xs);
    }
    .setup__input {
      width: 100%;
      background: var(--color-paper-2);
      border: 1px solid var(--color-paper-3);
      color: var(--color-ink);
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      padding: var(--space-sm) var(--space-md);
      transition: border-color var(--dur-short) var(--ease-out);
    }
    .setup__input:focus {
      outline: none;
      border-color: var(--color-accent);
    }
    .setup__input::placeholder { color: var(--color-dim); }
    .setup__input-row {
      display: flex;
      align-items: center;
      gap: var(--space-md);
    }
    .setup__input--flex { flex: 1; }
    .setup__masked-display {
      flex: 1;
      min-width: 0;
      background: var(--color-paper-2);
      border: 1px solid var(--color-paper-3);
      color: var(--color-ink);
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      padding: var(--space-sm) var(--space-md);
      letter-spacing: 0.12em;
      display: flex;
      align-items: center;
      min-height: 2.6rem;
    }
    .setup__masked-display--empty {
      color: var(--color-dim);
      letter-spacing: 0.02em;
    }
    .setup__reveal-btn {
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
      padding: var(--space-2xs) var(--space-sm);
    }
    .setup__reveal-btn:hover { color: var(--color-ink); }
    .setup__masked-row {
      display: flex;
      align-items: center;
      gap: var(--space-sm);
    }
    .setup__status {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      white-space: nowrap;
      flex-shrink: 0;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .setup__status--ok { color: var(--color-success); }
    .setup__status--err { color: var(--color-danger); }
    .setup__status--loading { color: var(--color-warning); }
    .setup__models {
      display: flex;
      flex-wrap: wrap;
      gap: var(--space-xs);
    }
    .setup__model-btn {
      background: var(--color-paper-2);
      border: 1px solid var(--color-paper-3);
      color: var(--color-muted);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      padding: var(--space-2xs) var(--space-sm);
      cursor: pointer;
      transition: all var(--dur-short) var(--ease-out);
      letter-spacing: 0.02em;
    }
    .setup__model-btn:hover {
      border-color: var(--color-dim);
      color: var(--color-ink);
    }
    .setup__model-btn--active {
      background: var(--color-accent);
      border-color: var(--color-accent);
      color: var(--color-paper);
    }
  `],
})
export class SetupLlmStepComponent {
  @Input() form: () => RuntimeSettings = () => ({});
  @Input() availableModels: () => string[] = () => [];
  @Input() validating: () => boolean = () => false;
  @Input() validation: () => ValidateResult | null = () => null;
  @Output() fieldChange = new EventEmitter<{ field: string; value: string }>();
  @Output() endpointChange = new EventEmitter<string>();

  showEndpoint = signal(false);
  showLlmKey = signal(false);

  maskedEndpoint = computed(() => {
    const v = this.form().llm_endpoint || '';
    if (!v || v.length <= 8) return v;
    try {
      const url = new URL(v);
      const host = url.hostname;
      const maskedHost = host.length > 4 ? host.slice(0, 2) + '*'.repeat(host.length - 4) + host.slice(-2) : '****';
      return url.protocol + '//' + maskedHost + (url.port ? ':' + url.port : '') + url.pathname;
    } catch {
      return v.slice(0, 2) + '*'.repeat(v.length - 4) + v.slice(-2);
    }
  });

  maskedLlmKey = computed(() => {
    const v = this.form().llm_api_key || '';
    if (!v) return '';
    return '•'.repeat(Math.min(v.length, 20));
  });
}