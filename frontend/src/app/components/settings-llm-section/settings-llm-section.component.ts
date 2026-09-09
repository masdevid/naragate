import { Component, Input, Output, EventEmitter, OnDestroy, inject, signal, computed } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subscription, Subject, debounceTime, switchMap, tap } from 'rxjs';
import { SettingsService, RuntimeSettings, ValidateResult } from '../../services/settings.service';
import { TPipe } from '../../pipes/t.pipe';

/**
 * Settings section for the LLM provider: endpoint (with live validation and
 * model discovery), API key, and the global default model.
 */
@Component({
  selector: 'app-settings-llm-section',
  standalone: true,
  imports: [FormsModule, TPipe],
  template: `
    <section class="sect">
      <h2 class="sect__heading">{{ 'settings.section_llm' | t }}</h2>
      <p class="sect__hint">{{ 'settings.section_llm_hint' | t }}</p>

      <div class="sect__field">
        <label class="sect__label">{{ 'settings.field_endpoint' | t }}</label>
        <div class="sect__input-row">
          @if (showEndpoint()) {
            <input [ngModel]="endpoint" (ngModelChange)="onEndpointChange($event)"
              class="sect__input sect__input--flex"
              [placeholder]="'settings.endpoint_placeholder' | t">
          } @else {
            <div class="sect__masked-display"
              [class.sect__masked-display--empty]="!maskedEndpoint()">
              {{ maskedEndpoint() || ('settings.endpoint_placeholder' | t) }}
            </div>
          }
          <button type="button" class="sect__reveal-btn"
            (click)="showEndpoint.set(!showEndpoint())">
            {{ (showEndpoint() ? 'settings.key_hide' : 'settings.key_show') | t }}
          </button>
          <span class="sect__status" [class.sect__status--ok]="validation()?.ok === true"
            [class.sect__status--err]="validation()?.ok === false"
            [class.sect__status--loading]="validating()">
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

      <div class="sect__field">
        <label class="sect__label">{{ 'settings.field_api_key' | t }}</label>
        <div class="sect__masked-row">
          @if (showLlmKey()) {
            <input [ngModel]="apiKey" (ngModelChange)="onFieldChange('llm_api_key', $event)"
              class="sect__input"
              placeholder="••••••••••••••••••••••••"
              autocomplete="new-password">
          } @else {
            <div class="sect__masked-display"
              [class.sect__masked-display--empty]="!maskedLlmKey()">
              {{ maskedLlmKey() || ('settings.api_key_placeholder' | t) }}
            </div>
          }
          <button type="button" class="sect__reveal-btn"
            (click)="showLlmKey.set(!showLlmKey())">
            {{ (showLlmKey() ? 'settings.key_hide' : 'settings.key_show') | t }}
          </button>
        </div>
      </div>

      <div class="sect__field">
        <label class="sect__label">{{ 'settings.field_model' | t }}</label>
        @if (availableModels().length) {
          <p class="sect__hint" style="margin-bottom: var(--space-xs)">{{ 'settings.pick_model' | t }}</p>
          <div class="sect__models">
            @for (model of availableModels(); track model) {
              <button class="sect__model-btn"
                [class.sect__model-btn--active]="selectedModel === model"
                (click)="onFieldChange('llm_model', model)">
                {{ model }}
              </button>
            }
          </div>
        } @else {
          <input [ngModel]="selectedModel" (ngModelChange)="onFieldChange('llm_model', $event)"
            class="sect__input"
            [placeholder]="'settings.field_model_placeholder' | t">
        }
      </div>
    </section>
  `,
  styles: [`
    .sect {
      display: block;
      border-top: 1px solid var(--color-rule);
      padding: var(--space-xl) 0;
    }
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
      background: var(--color-paper-2);
      border: 1px solid var(--color-paper-3);
      color: var(--color-ink);
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      padding: var(--space-sm) var(--space-md);
      transition: border-color var(--dur-short) var(--ease-out);
    }
    .sect__input:focus { outline: none; border-color: var(--color-accent); }
    .sect__input::placeholder { color: var(--color-dim); }
    .sect__input-row {
      display: flex;
      align-items: center;
      gap: var(--space-md);
    }
    .sect__input--flex { flex: 1; }
    .sect__masked-display {
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
    .sect__masked-display--empty {
      color: var(--color-dim);
      letter-spacing: 0.02em;
    }
    .sect__reveal-btn {
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
    .sect__reveal-btn:hover { color: var(--color-ink); }
    .sect__masked-row {
      display: flex;
      align-items: center;
      gap: var(--space-sm);
    }
    .sect__status {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      white-space: nowrap;
      flex-shrink: 0;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .sect__status--ok { color: var(--color-success); }
    .sect__status--err { color: var(--color-danger); }
    .sect__status--loading { color: var(--color-warning); }
    .sect__models {
      display: flex;
      flex-wrap: wrap;
      gap: var(--space-xs);
    }
    .sect__model-btn {
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
    .sect__model-btn:hover { border-color: var(--color-dim); color: var(--color-ink); }
    .sect__model-btn--active {
      background: var(--color-accent);
      border-color: var(--color-accent);
      color: var(--color-paper);
    }

    @media (max-width: 640px) {
      .sect__input-row { flex-direction: column; align-items: stretch; }
    }
  `],
})
export class SettingsLlmSectionComponent implements OnDestroy {
  @Input() endpoint = '';
  @Input() apiKey = '';
  @Input() selectedModel = '';
  @Output() fieldChange = new EventEmitter<{ field: string; value: string }>();

  validating = signal(false);
  validation = signal<ValidateResult | null>(null);
  availableModels = signal<string[]>([]);
  showEndpoint = signal(false);
  showLlmKey = signal(false);

  private settingsService = inject(SettingsService);
  private endpoint$ = new Subject<string>();
  private subs: Subscription[] = [];

  maskedEndpoint = computed(() => {
    const v = this.endpoint || '';
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
    const v = this.apiKey || '';
    if (!v) return '';
    return '•'.repeat(Math.min(v.length, 20));
  });

  constructor() {
    this.subs.push(
      this.endpoint$.pipe(
        debounceTime(500),
        tap(() => { this.validating.set(true); this.validation.set(null); }),
        switchMap(endpoint => this.settingsService.validateEndpoint(endpoint, this.apiKey)),
      ).subscribe({
        next: (result: any) => {
          this.validation.set(result);
          this.validating.set(false);
          this.availableModels.set(result.ok ? result.models : []);
        },
        error: () => {
          this.validating.set(false);
          this.validation.set({ ok: false, endpoint: '', models: [], error: 'Request failed' });
        },
      }),
    );
  }

  ngOnDestroy() {
    this.subs.forEach(s => s.unsubscribe());
  }

  onEndpointChange(endpoint: string) {
    this.fieldChange.emit({ field: 'llm_endpoint', value: endpoint });
    if (endpoint.trim()) {
      this.endpoint$.next(endpoint);
    } else {
      this.validation.set(null);
      this.availableModels.set([]);
    }
  }

  onFieldChange(field: string, value: string) {
    this.fieldChange.emit({ field, value: value || '' });
  }

  /** Validate a pre-existing endpoint on page load so models are discoverable. */
  validateExisting() {
    if (!this.endpoint) return;
    this.validating.set(true);
    this.settingsService.validateEndpoint(this.endpoint, this.apiKey).subscribe({
      next: (result: any) => {
        this.validation.set(result);
        this.validating.set(false);
        this.availableModels.set(result.ok ? result.models : []);
      },
      error: () => {
        this.validating.set(false);
      },
    });
  }
}
