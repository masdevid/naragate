import { Component, OnInit, OnDestroy, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Subscription, Subject, debounceTime, switchMap, tap } from 'rxjs';
import { SettingsService, RuntimeSettings, ValidateResult, SectorsValidateResult } from '../../services/settings.service';
import { I18nService } from '../../services/i18n.service';
import { TPipe } from '../../pipes/t.pipe';
import { SecretKeyInputComponent } from '../../components/masked-key-input/secret-key-input.component';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [FormsModule, TPipe, SecretKeyInputComponent],
  template: `
    <div class="settings">
      <div class="settings__inner">
        <button (click)="goBack()" class="settings__back">&larr; {{ 'settings.back' | t }}</button>
        <h1 class="settings__title">{{ 'settings.title' | t }}</h1>
        <p class="settings__sub">{{ 'settings.sub' | t }}</p>

        @if (saved()) {
          <div class="settings__toast">{{ 'settings.auto_saved' | t }}</div>
        }

        <!-- LLM Provider -->
        <section class="settings__section">
          <h2 class="settings__heading">{{ 'settings.section_llm' | t }}</h2>
          <p class="settings__hint">{{ 'settings.section_llm_hint' | t }}</p>

          <div class="settings__field">
            <label class="settings__label">{{ 'settings.field_endpoint' | t }}</label>
            <div class="settings__input-row">
              <input [ngModel]="form().llm_endpoint" (ngModelChange)="onEndpointChange($event)"
                class="settings__input settings__input--flex"
                [placeholder]="'settings.endpoint_placeholder' | t">
              <span class="settings__status" [class.settings__status--ok]="validation()?.ok === true"
                [class.settings__status--err]="validation()?.ok === false"
                [class.settings__status--loading]="validating()">
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

          <div class="settings__field">
            <label class="settings__label">{{ 'settings.field_api_key' | t }}</label>
            <input [ngModel]="form().llm_api_key" (ngModelChange)="onFieldChange('llm_api_key', $event)"
              class="settings__input" type="password"
              [placeholder]="'settings.api_key_placeholder' | t">
          </div>

          <div class="settings__field">
            <label class="settings__label">{{ 'settings.field_model' | t }}</label>
            @if (availableModels().length) {
              <p class="settings__hint" style="margin-bottom: var(--space-xs)">{{ 'settings.pick_model' | t }}</p>
              <div class="settings__models">
                @for (model of availableModels(); track model) {
                  <button class="settings__model-btn"
                    [class.settings__model-btn--active]="form().llm_model === model"
                    (click)="onFieldChange('llm_model', model)">
                    {{ model }}
                  </button>
                }
              </div>
            } @else {
              <input [ngModel]="form().llm_model" (ngModelChange)="onFieldChange('llm_model', $event)"
                class="settings__input"
                [placeholder]="'settings.field_model_placeholder' | t">
            }
          </div>
        </section>

        <!-- Per-Agent Models -->
        <section class="settings__section">
          <h2 class="settings__heading">{{ 'settings.section_agents' | t }}</h2>
          <p class="settings__hint">{{ 'settings.section_agents_hint' | t }}</p>

          <div class="settings__field">
            <label class="settings__label">{{ 'settings.field_claim_parser' | t }}</label>
            @if (availableModels().length) {
              <div class="settings__models">
                <button class="settings__model-btn settings__model-btn--sm"
                  [class.settings__model-btn--active]="!form().claim_parser_model"
                  (click)="onFieldChange('claim_parser_model', '')">
                  {{ 'settings.model_placeholder' | t }}
                </button>
                @for (model of availableModels(); track model) {
                  <button class="settings__model-btn settings__model-btn--sm"
                    [class.settings__model-btn--active]="form().claim_parser_model === model"
                    (click)="onFieldChange('claim_parser_model', model)">
                    {{ model }}
                  </button>
                }
              </div>
            } @else {
              <input [ngModel]="form().claim_parser_model" (ngModelChange)="onFieldChange('claim_parser_model', $event)"
                class="settings__input"
                [placeholder]="'settings.model_placeholder' | t">
            }
          </div>

          <div class="settings__field">
            <label class="settings__label">{{ 'settings.field_skeptic' | t }}</label>
            @if (availableModels().length) {
              <div class="settings__models">
                <button class="settings__model-btn settings__model-btn--sm"
                  [class.settings__model-btn--active]="!form().skeptic_model"
                  (click)="onFieldChange('skeptic_model', '')">
                  {{ 'settings.model_placeholder' | t }}
                </button>
                @for (model of availableModels(); track model) {
                  <button class="settings__model-btn settings__model-btn--sm"
                    [class.settings__model-btn--active]="form().skeptic_model === model"
                    (click)="onFieldChange('skeptic_model', model)">
                    {{ model }}
                  </button>
                }
              </div>
            } @else {
              <input [ngModel]="form().skeptic_model" (ngModelChange)="onFieldChange('skeptic_model', $event)"
                class="settings__input"
                [placeholder]="'settings.model_placeholder' | t">
            }
          </div>

          <div class="settings__field">
            <label class="settings__label">{{ 'settings.field_scorer' | t }}</label>
            @if (availableModels().length) {
              <div class="settings__models">
                <button class="settings__model-btn settings__model-btn--sm"
                  [class.settings__model-btn--active]="!form().scorer_model"
                  (click)="onFieldChange('scorer_model', '')">
                  {{ 'settings.model_placeholder' | t }}
                </button>
                @for (model of availableModels(); track model) {
                  <button class="settings__model-btn settings__model-btn--sm"
                    [class.settings__model-btn--active]="form().scorer_model === model"
                    (click)="onFieldChange('scorer_model', model)">
                    {{ model }}
                  </button>
                }
              </div>
            } @else {
              <input [ngModel]="form().scorer_model" (ngModelChange)="onFieldChange('scorer_model', $event)"
                class="settings__input"
                [placeholder]="'settings.model_placeholder' | t">
            }
          </div>
        </section>

        <!-- Sectors API -->
        <section class="settings__section">
          <h2 class="settings__heading">{{ 'settings.section_sectors' | t }}</h2>

          <div class="settings__field">
            <label class="settings__label">{{ 'settings.field_sectors_key' | t }}</label>
            <div class="settings__input-row">
              <app-secret-key-input [value]="form().sectors_api_key"
                (valueChange)="onFieldChange('sectors_api_key', $event)"
                inputClass="settings__input settings__input--flex"
                [placeholder]="'settings.sectors_key_placeholder' | t"/>
              <button (click)="validateSectorsKey()" [disabled]="!sectorsKeyPresent() || sectorsValidating()"
                class="settings__validate-btn">
                {{ 'settings.sectors_validate' | t }}
              </button>
            </div>
            @if (clientIp()) {
              <p class="settings__hint" style="margin-top: var(--space-sm)">
                {{ 'settings.sectors_bound_ip' | t:{ip: clientIp()!} }}
              </p>
            }
            <span class="settings__status" [class.settings__status--ok]="sectorsValidation()?.ok === true"
              [class.settings__status--err]="sectorsValidation()?.ok === false"
              [class.settings__status--loading]="sectorsValidating()">
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
      </div>
    </div>
  `,
  styles: [`
    .settings {
      padding: var(--space-2xl) var(--space-lg);
    }
    .settings__inner {
      max-width: 36rem;
      margin: 0 auto;
    }
    .settings__back {
      background: none;
      border: none;
      color: var(--color-muted);
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      cursor: pointer;
      padding: 0;
      margin-bottom: var(--space-xl);
      transition: color var(--dur-short) var(--ease-out);
    }
    .settings__back:hover { color: var(--color-ink); }

    .settings__title {
      font-family: var(--font-display);
      font-size: var(--text-2xl);
      text-transform: uppercase;
      margin-bottom: var(--space-xs);
    }
    .settings__sub {
      font-size: var(--text-sm);
      color: var(--color-muted);
      margin-bottom: var(--space-2xl);
    }
    .settings__toast {
      padding: var(--space-sm) var(--space-md);
      background: oklch(20% 0.02 145);
      color: var(--color-success);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-bottom: var(--space-lg);
    }

    .settings__section {
      border-top: 1px solid var(--color-rule);
      padding: var(--space-xl) 0;
    }
    .settings__heading {
      font-family: var(--font-display);
      font-size: var(--text-md);
      text-transform: uppercase;
      margin-bottom: var(--space-xs);
    }
    .settings__hint {
      font-size: var(--text-xs);
      color: var(--color-dim);
      margin-bottom: var(--space-lg);
    }

    .settings__field {
      margin-bottom: var(--space-md);
    }
    .settings__label {
      display: block;
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-muted);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin-bottom: var(--space-2xs);
    }
    .settings__input {
      width: 100%;
      background: var(--color-paper-2);
      border: 1px solid var(--color-paper-3);
      color: var(--color-ink);
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      padding: var(--space-sm) var(--space-md);
      transition: border-color var(--dur-short) var(--ease-out);
    }
    .settings__input:focus {
      outline: none;
      border-color: var(--color-accent);
    }
    .settings__input::placeholder {
      color: var(--color-dim);
    }
    .settings__input-row {
      display: flex;
      align-items: center;
      gap: var(--space-md);
    }
    .settings__input--flex {
      flex: 1;
    }
    .settings__status {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      white-space: nowrap;
      flex-shrink: 0;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .settings__status--ok { color: var(--color-success); }
    .settings__status--err { color: var(--color-danger); }
    .settings__status--loading { color: var(--color-warning); }

    .settings__models {
      display: flex;
      flex-wrap: wrap;
      gap: var(--space-xs);
    }
    .settings__model-btn {
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
    .settings__model-btn:hover {
      border-color: var(--color-dim);
      color: var(--color-ink);
    }
    .settings__model-btn--active {
      background: var(--color-accent);
      border-color: var(--color-accent);
      color: var(--color-paper);
    }
    .settings__model-btn--sm {
      font-size: 0.6rem;
      padding: var(--space-3xs) var(--space-xs);
    }
    .settings__validate-btn {
      background: none;
      border: 1px solid var(--color-accent);
      color: var(--color-accent);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: var(--space-2xs) var(--space-sm);
      cursor: pointer;
      white-space: nowrap;
      flex-shrink: 0;
      transition: background var(--dur-short) var(--ease-out), color var(--dur-short) var(--ease-out);
    }
    .settings__validate-btn:hover {
      background: var(--color-accent);
      color: var(--color-paper);
    }
    .settings__validate-btn:disabled {
      opacity: 0.3;
      cursor: not-allowed;
    }

    @media (max-width: 640px) {
      .settings { padding: var(--space-lg) var(--space-md); }
      .settings__input-row { flex-direction: column; align-items: stretch; }
    }
  `],
})
export class SettingsComponent implements OnInit, OnDestroy {
  private settingsService = inject(SettingsService);
  private router = inject(Router);
  private i18n = inject(I18nService);

  form = signal<RuntimeSettings>({});
  saved = signal(false);
  validating = signal(false);
  validation = signal<ValidateResult | null>(null);
  availableModels = signal<string[]>([]);
  sectorsValidating = signal(false);
  sectorsValidation = signal<SectorsValidateResult | null>(null);
  clientIp = signal<string | null>(null);

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
          this.clientIp.set(data.client_ip || null);
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
        switchMap(endpoint => this.settingsService.validateEndpoint(endpoint, this.form().llm_api_key)),
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

  private emitSave(patch: RuntimeSettings) {
    this.pendingSave = { ...this.pendingSave, ...patch };
    this.queueSave();
  }

  private queueSave() {
    if (this.saveInFlight) {
      this.saveQueued = true;
      return;
    }
    this.saveInFlight = true;
    const payload = { ...this.pendingSave };
    this.settingsService.updateSettings(payload).subscribe({
      next: () => {
        this.saveInFlight = false;
        this.saved.set(true);
        setTimeout(() => this.saved.set(false), 2000);
        if (this.saveQueued) {
          this.saveQueued = false;
          this.queueSave();
        }
      },
      error: () => {
        this.saveInFlight = false;
        if (this.saveQueued) {
          this.saveQueued = false;
          this.queueSave();
        }
      },
    });
  }

  validateEndpoint(endpoint: string, apiKey?: string) {
    this.validating.set(true);
    this.settingsService.validateEndpoint(endpoint, apiKey).subscribe({
      next: (result) => {
        this.validation.set(result);
        this.validating.set(false);
        this.availableModels.set(result.ok ? result.models : []);
      },
      error: () => {
        this.validating.set(false);
      },
    });
  }

  sectorsKeyPresent(): boolean {
    const k = this.form().sectors_api_key;
    return !!(k && k.trim()) || !!this.form().sectors_key_bound_to;
  }

  validateSectorsKey() {
    const key = this.form().sectors_api_key;
    if (!key) return;
    this.sectorsValidating.set(true);
    this.sectorsValidation.set(null);
    this.settingsService.validateSectors(key).subscribe({
      next: (result) => {
        this.sectorsValidation.set(result);
        this.sectorsValidating.set(false);
      },
      error: () => {
        this.sectorsValidation.set({ ok: false, error: 'Request failed' });
        this.sectorsValidating.set(false);
      },
    });
  }

  goBack() {
    this.router.navigate(['/dashboard']);
  }
}
