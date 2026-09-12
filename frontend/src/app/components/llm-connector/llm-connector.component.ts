import { Component, OnInit, OnDestroy, inject, signal, computed } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Subscription, Subject, debounceTime, switchMap, tap } from 'rxjs';
import { SettingsService, RuntimeSettings, ValidateResult } from '../../services/settings.service';
import { I18nService } from '../../services/i18n.service';
import { TPipe } from '../../pipes/t.pipe';
import { SecretKeyInputComponent } from '../../components/masked-key-input/secret-key-input.component';
import { LlmProviderPickerComponent } from '../../components/llm-provider-picker/llm-provider-picker.component';
import {
  LLM_PROVIDERS,
  LlmProvider,
  getProvider,
  DEFAULT_PROVIDER,
} from '../../services/llm-providers';

@Component({
  selector: 'app-llm-connector',
  standalone: true,
  imports: [FormsModule, TPipe, SecretKeyInputComponent, LlmProviderPickerComponent],
  template: `
    <div class="conn">
      <div class="conn__inner">
        <button (click)="goBack()" class="conn__back">&larr; {{ 'connector.back' | t }}</button>
        <h1 class="conn__title">{{ 'connector.title' | t }}</h1>
        <p class="conn__sub">{{ 'connector.sub' | t }}</p>

        @if (saved()) {
          <div class="conn__toast">{{ 'connector.saved' | t }}</div>
        }

        <section class="conn__section">
          <label class="conn__label">{{ 'connector.field_provider' | t }}</label>
          <app-llm-provider-picker
            [providers]="providers"
            [selectedId]="selectedProvider()"
            (select)="selectProvider($event)"/>
        </section>

        <section class="conn__section">
          <div class="conn__field">
            <label class="conn__label">{{ 'connector.field_endpoint' | t }}</label>
            <div class="conn__endpoint-row">
              @if (showEndpoint()) {
                <input [ngModel]="form().llm_endpoint"
                  (ngModelChange)="onEndpointChange($event)"
                  class="conn__input conn__input--flex"
                  [placeholder]="activeProvider().baseUrl || ('connector.endpoint_placeholder' | t)">
              } @else {
                <div class="conn__masked-display"
                  [class.conn__masked-display--empty]="!maskedEndpoint()">
                  {{ maskedEndpoint() || ('connector.endpoint_placeholder' | t) }}
                </div>
              }
              <button type="button" class="conn__reveal-btn"
                (click)="showEndpoint.set(!showEndpoint())">
                {{ (showEndpoint() ? 'settings.key_hide' : 'settings.key_show') | t }}
              </button>
            </div>
            <span class="conn__status"
              [class.conn__status--ok]="validation()?.ok === true"
              [class.conn__status--err]="validation()?.ok === false"
              [class.conn__status--loading]="validating()">
              @if (validating()) {
                {{ 'connector.validating' | t }}
              } @else if (validation()?.ok === true) {
                {{ 'connector.valid_ok' | t:{count: validation()!.models.length} }}
              } @else if (validation()?.ok === false) {
                {{ 'connector.valid_error' | t }}
              }
            </span>
            @if (validation()?.ok === false && activeProvider().tokenUrl) {
              <div class="conn__token-hint">
                <span>{{ 'connector.token_hint' | t }}</span>
                <a [href]="activeProvider().tokenUrl" target="_blank" rel="noopener" class="conn__token-link">
                  {{ 'connector.generate_token' | t }} &rarr;
                </a>
              </div>
            }
          </div>
        </section>

        @if (activeProvider().requiresKey || form().llm_provider === 'custom') {
          <section class="conn__section">
            <div class="conn__field">
              <label class="conn__label">{{ 'connector.field_api_key' | t }}</label>
              <app-secret-key-input
                [value]="form().llm_api_key"
                (valueChange)="onFieldChange('llm_api_key', $event)"
                inputClass="conn__input conn__input--wide"
                [placeholder]="'connector.api_key_placeholder' | t"/>
            </div>
          </section>
        }

        <section class="conn__section">
          <div class="conn__field">
            <label class="conn__label">{{ 'connector.field_model' | t }}</label>
            @if (availableModels().length) {
              <p class="conn__hint">{{ 'connector.pick_model' | t }}</p>
              <div class="conn__models">
                @for (model of availableModels(); track model) {
                  <button class="conn__model-btn"
                    [class.conn__model-btn--active]="form().llm_model === model"
                    (click)="onFieldChange('llm_model', model)">
                    {{ model }}
                  </button>
                }
              </div>
            } @else {
              <input [ngModel]="form().llm_model"
                (ngModelChange)="onFieldChange('llm_model', $event)"
                class="conn__input"
                [placeholder]="'connector.model_placeholder' | t">
            }
          </div>
        </section>

        <section class="conn__section conn__actions">
          <button class="conn__btn conn__btn--validate"
            [disabled]="validating() || !form().llm_endpoint"
            (click)="validateNow()">
            {{ 'connector.validate_btn' | t }}
          </button>
          @if (!isDefaultActive()) {
            <button class="conn__btn conn__btn--reset"
              (click)="disconnectProvider()">
              {{ 'connector.disconnect_btn' | t }}
            </button>
          }
          @if (isDefaultActive()) {
            <small class="conn__immutable">{{ 'connector.immutable_hint' | t }}</small>
          }
        </section>
      </div>
    </div>
  `,
  styles: [`
    .conn { padding: var(--space-2xl) var(--space-lg); }
    .conn__inner { max-width: 48rem; margin: 0 auto; }

    .conn__back {
      background: none; border: none;
      color: var(--color-muted);
      font-family: var(--font-mono); font-size: var(--text-sm);
      cursor: pointer; padding: 0;
      margin-bottom: var(--space-xl);
      transition: color var(--dur-short) var(--ease-out);
    }
    .conn__back:hover { color: var(--color-ink); }

    .conn__title {
      font-family: var(--font-display);
      font-size: var(--text-2xl);
      text-transform: uppercase;
      margin-bottom: var(--space-xs);
    }
    .conn__sub {
      font-size: var(--text-sm);
      color: var(--color-muted);
      margin-bottom: var(--space-2xl);
    }

    .conn__toast {
      padding: var(--space-sm) var(--space-md);
      background: oklch(20% 0.02 145);
      color: var(--color-success);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-bottom: var(--space-lg);
    }

    .conn__section { margin-bottom: var(--space-xl); }
    .conn__field { margin-bottom: var(--space-md); }
    .conn__label {
      display: block;
      font-family: var(--font-mono); font-size: var(--text-xs);
      color: var(--color-muted);
      text-transform: uppercase; letter-spacing: 0.06em;
      margin-bottom: var(--space-2xs);
    }
    .conn__input,
    .conn__masked-display {
      width: 100%;
      background: var(--color-paper-2);
      border: 1px solid var(--color-paper-3);
      color: var(--color-ink);
      font-family: var(--font-mono); font-size: var(--text-sm);
      padding: var(--space-sm) var(--space-md);
      transition: border-color var(--dur-short) var(--ease-out);
    }
    .conn__input:focus { outline: none; border-color: var(--color-accent); }
    .conn__input::placeholder { color: var(--color-dim); }
    .conn__input--wide { min-width: 0; }
    .conn__input--flex { flex: 1; min-width: 0; }
    .conn__masked-display { flex: 1; min-width: 0; color: var(--color-dim); }
    .conn__masked-display--empty { color: var(--color-dim); }
    .conn__reveal-btn {
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
    .conn__reveal-btn:hover { color: var(--color-ink); }
    .conn__hint {
      font-size: var(--text-xs); color: var(--color-dim);
      margin-bottom: var(--space-xs);
    }
    .conn__status {
      display: block; margin-top: var(--space-2xs);
      font-family: var(--font-mono); font-size: var(--text-xs);
      color: var(--color-dim);
      text-transform: uppercase; letter-spacing: 0.04em;
    }
    .conn__status--ok { color: var(--color-success); }
    .conn__status--err { color: var(--color-danger); }
    .conn__status--loading { color: var(--color-warning); }

    .conn__models {
      display: flex; flex-wrap: wrap; gap: var(--space-xs);
    }
    .conn__model-btn {
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
    .conn__model-btn:hover { border-color: var(--color-dim); color: var(--color-ink); }
    .conn__model-btn--active {
      background: var(--color-accent);
      border-color: var(--color-accent);
      color: var(--color-paper);
    }

    .conn__actions {
      display: flex; gap: var(--space-sm);
      border-top: 1px solid var(--color-rule);
      padding-top: var(--space-xl);
      margin-top: var(--space-xl);
    }
    .conn__btn {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: var(--space-2xs) var(--space-sm);
      cursor: pointer;
      border: 1px solid var(--color-rule);
      background: none;
      color: var(--color-muted);
      transition: all var(--dur-short) var(--ease-out);
    }
    .conn__btn:hover { color: var(--color-ink); border-color: var(--color-dim); }
    .conn__btn--validate {
      background: var(--color-accent);
      border-color: var(--color-accent);
      color: var(--color-paper);
    }
    .conn__btn--validate:hover { opacity: 0.9; color: var(--color-paper); }
    .conn__btn--validate:disabled { opacity: 0.3; cursor: not-allowed; }
    .conn__btn--reset { color: var(--color-danger); border-color: var(--color-danger); }
    .conn__btn--reset:hover { background: var(--color-danger); color: var(--color-paper); }

    @media (max-width: 640px) {
      .conn { padding: var(--space-lg) var(--space-md); }
    }
  `],
})
export class LlmConnectorComponent implements OnInit, OnDestroy {
  private settingsService = inject(SettingsService);
  private router = inject(Router);
  private i18n = inject(I18nService);

  providers = LLM_PROVIDERS;

  form = signal<RuntimeSettings>({});
  saved = signal(false);
  validating = signal(false);
  validation = signal<ValidateResult | null>(null);
  availableModels = signal<string[]>([]);
  showEndpoint = signal(false);

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

  selectedProvider = computed(() => {
    const p = this.form().llm_provider;
    if (p && this.providers.some(pr => pr.id === p)) return p;
    return DEFAULT_PROVIDER;
  });

  activeProvider = computed((): LlmProvider => {
    return getProvider(this.selectedProvider());
  });

  /** The built-in default provider (localhost Ollama) is always active and cannot be deleted/disconnected. */
  isDefaultActive = computed(() => {
    return getProvider(this.selectedProvider()).default === true;
  });

  private endpoint$ = new Subject<string>();
  private pendingSave: RuntimeSettings | null = null;
  private saveInFlight = false;
  private saveQueued = false;
  private subs: Subscription[] = [];

  ngOnInit() {
    this.subs.push(
      this.settingsService.getSettings().subscribe({
        next: (data) => {
          this.form.set(data);
          if (data.llm_endpoint) {
            this.validateEndpoint(data.llm_endpoint, data.llm_api_key);
          }
        },
        error: () => {},
      }),
    );

    this.subs.push(
      this.endpoint$.pipe(
        debounceTime(500),
        tap(() => { this.validating.set(true); this.validation.set(null); }),
        switchMap(ep => this.settingsService.validateEndpoint(ep, this.form().llm_api_key)),
      ).subscribe({
        next: (result) => {
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
    if (this.pendingSave && Object.keys(this.pendingSave).length) {
      this.queueSave();
    }
  }

  selectProvider(id: string) {
    const p = getProvider(id);
    this.form.update(f => ({
      ...f,
      llm_provider: id,
      llm_endpoint: f.llm_endpoint || p.baseUrl,
    }));
    this.emitSave({ llm_provider: id });
    const ep = this.form().llm_endpoint || p.baseUrl;
    if (ep) {
      this.endpoint$.next(ep);
    }
  }

  onEndpointChange(endpoint: string) {
    this.form.update(f => ({ ...f, llm_endpoint: endpoint }));
    if (endpoint.trim()) {
      this.endpoint$.next(endpoint);
    } else {
      this.validation.set(null);
      this.availableModels.set([]);
    }
    this.emitSave({ llm_endpoint: endpoint });
  }

  onFieldChange(field: string, value: string) {
    this.form.update(f => ({ ...f, [field]: value || '' }));
    this.emitSave({ [field]: value || '' });
  }

  validateNow() {
    const ep = this.form().llm_endpoint;
    if (!ep) return;
    this.validating.set(true);
    this.validation.set(null);
    this.settingsService.validateEndpoint(ep, this.form().llm_api_key).subscribe({
      next: (result) => {
        this.validation.set(result);
        this.validating.set(false);
        this.availableModels.set(result.ok ? result.models : []);
      },
      error: () => { this.validating.set(false); },
    });
  }

  disconnectProvider() {
    this.settingsService.clearLlmProvider().subscribe({
      next: () => {
        this.form.set({});
        this.validation.set(null);
        this.availableModels.set([]);
        this.saved.set(true);
        setTimeout(() => this.saved.set(false), 2000);
        this.validateEndpoint('http://localhost:11434', undefined);
      },
      error: () => {},
    });
  }

  private validateEndpoint(endpoint: string, apiKey?: string) {
    this.validating.set(true);
    this.settingsService.validateEndpoint(endpoint, apiKey).subscribe({
      next: (result) => {
        this.validation.set(result);
        this.validating.set(false);
        this.availableModels.set(result.ok ? result.models : []);
      },
      error: () => { this.validating.set(false); },
    });
  }

  private emitSave(patch: RuntimeSettings) {
    this.pendingSave = { ...this.pendingSave, ...patch };
    this.queueSave();
  }

  private queueSave() {
    if (this.saveInFlight) { this.saveQueued = true; return; }
    if (!this.pendingSave || !Object.keys(this.pendingSave).length) { return; }
    this.saveInFlight = true;
    const payload = { ...this.pendingSave };
    this.pendingSave = null;
    this.settingsService.updateSettings(payload).subscribe({
      next: () => {
        this.saveInFlight = false;
        this.saved.set(true);
        setTimeout(() => this.saved.set(false), 2000);
        if (this.saveQueued) { this.saveQueued = false; this.queueSave(); }
      },
      error: () => {
        this.saveInFlight = false;
        if (this.saveQueued) { this.saveQueued = false; this.queueSave(); }
      },
    });
  }

  goBack() {
    this.router.navigate(['/settings']);
  }
}
