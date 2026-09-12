import { Component, OnInit, OnDestroy, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { SettingsService, RuntimeSettings, ValidateResult } from '../../services/settings.service';
import { TPipe } from '../../pipes/t.pipe';
import { SettingsSectorsSectionComponent } from '../../components/settings-sectors-section/settings-sectors-section.component';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [FormsModule, TPipe, SettingsSectorsSectionComponent],
  template: `
    <div class="settings">
      <div class="settings__inner">
        <button (click)="goBack()" class="settings__back">&larr; {{ 'settings.back' | t }}</button>
        <h1 class="settings__title">{{ 'settings.title' | t }}</h1>
        <p class="settings__sub">{{ 'settings.sub' | t }}</p>

        @if (saved()) {
          <div class="settings__toast">{{ 'settings.auto_saved' | t }}</div>
        }

        @if (saveError()) {
          <div class="settings__save-error">{{ 'settings.save_error' | t:{detail: saveError()!} }}</div>
        }

        <!-- Sectors API -->
        <app-settings-sectors-section
          [sectorsApiKey]="form().sectors_api_key"
          [keyBoundTo]="form().sectors_key_bound_to"
          [clientIp]="clientIp()"
          [ownerIp]="ownerIp()"
          [authorizedIps]="authorizedIps()"
          [isOwner]="isOwner()"
          (fieldChange)="onFieldChange($event.field, $event.value)"
          (authorizedIpsChange)="authorizedIps.set($event)"/>

        <!-- LLM Provider: default model only; manage the connection in the LLM Connector -->
        <section class="settings__section">
          <h2 class="settings__heading">{{ 'settings.section_llm' | t }}</h2>
          <p class="settings__hint">{{ 'settings.section_llm_hint' | t }}</p>
          <button class="settings__connector-link" routerLink="/llm-connector">
            {{ 'settings.open_connector' | t }} &rarr;
          </button>

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

          <div class="settings__field">
            <label class="settings__label">{{ 'settings.field_news' | t }}</label>
            @if (availableModels().length) {
              <div class="settings__models">
                <button class="settings__model-btn settings__model-btn--sm"
                  [class.settings__model-btn--active]="!form().news_model"
                  (click)="onFieldChange('news_model', '')">
                  {{ 'settings.model_placeholder' | t }}
                </button>
                @for (model of availableModels(); track model) {
                  <button class="settings__model-btn settings__model-btn--sm"
                    [class.settings__model-btn--active]="form().news_model === model"
                    (click)="onFieldChange('news_model', model)">
                    {{ model }}
                  </button>
                }
              </div>
            } @else {
              <input [ngModel]="form().news_model" (ngModelChange)="onFieldChange('news_model', $event)"
                class="settings__input"
                [placeholder]="'settings.model_placeholder' | t">
            }
          </div>

          <div class="settings__field">
            <label class="settings__label">{{ 'settings.field_chat' | t }}</label>
            @if (availableModels().length) {
              <div class="settings__models">
                <button class="settings__model-btn settings__model-btn--sm"
                  [class.settings__model-btn--active]="!form().chat_model"
                  (click)="onFieldChange('chat_model', '')">
                  {{ 'settings.model_placeholder' | t }}
                </button>
                @for (model of availableModels(); track model) {
                  <button class="settings__model-btn settings__model-btn--sm"
                    [class.settings__model-btn--active]="form().chat_model === model"
                    (click)="onFieldChange('chat_model', model)">
                    {{ model }}
                  </button>
                }
              </div>
            } @else {
              <input [ngModel]="form().chat_model" (ngModelChange)="onFieldChange('chat_model', $event)"
                class="settings__input"
                [placeholder]="'settings.model_placeholder' | t">
            }
          </div>

          <div class="settings__field">
            <label class="settings__label">{{ 'settings.field_follow_up' | t }}</label>
            @if (availableModels().length) {
              <div class="settings__models">
                <button class="settings__model-btn settings__model-btn--sm"
                  [class.settings__model-btn--active]="!form().follow_up_model"
                  (click)="onFieldChange('follow_up_model', '')">
                  {{ 'settings.model_placeholder' | t }}
                </button>
                @for (model of availableModels(); track model) {
                  <button class="settings__model-btn settings__model-btn--sm"
                    [class.settings__model-btn--active]="form().follow_up_model === model"
                    (click)="onFieldChange('follow_up_model', model)">
                    {{ model }}
                  </button>
                }
              </div>
            } @else {
              <input [ngModel]="form().follow_up_model" (ngModelChange)="onFieldChange('follow_up_model', $event)"
                class="settings__input"
                [placeholder]="'settings.model_placeholder' | t">
            }
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
      max-width: 48rem;
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
    .settings__save-error {
      padding: var(--space-sm) var(--space-md);
      background: oklch(24% 0.05 20);
      color: var(--color-danger);
      font-size: var(--text-xs);
      line-height: 1.5;
      margin-bottom: var(--space-lg);
    }
    .settings__connector-link {
      display: inline-block;
      background: none;
      border: 1px solid var(--color-paper-3);
      color: var(--color-muted);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: var(--space-2xs) var(--space-sm);
      cursor: pointer;
      margin-bottom: var(--space-lg);
      transition: all var(--dur-short) var(--ease-out);
    }
    .settings__connector-link:hover {
      border-color: var(--color-accent);
      color: var(--color-accent);
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

    @media (max-width: 640px) {
      .settings { padding: var(--space-lg) var(--space-md); }
    }
  `],
})
export class SettingsComponent implements OnInit, OnDestroy {
  private settingsService = inject(SettingsService);
  private router = inject(Router);

  form = signal<RuntimeSettings>({});
  saved = signal(false);
  saveError = signal<string | null>(null);
  validating = signal(false);
  validation = signal<ValidateResult | null>(null);
  availableModels = signal<string[]>([]);
  clientIp = signal<string | null>(null);
  ownerIp = signal<string | null>(null);
  authorizedIps = signal<string[]>([]);
  isOwner = signal(false);
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
          this.ownerIp.set(data.sectors_key_owner_ip || null);
          this.authorizedIps.set(data.sectors_authorized_ips || []);
          this.isOwner.set(!!data.sectors_key_is_owner);
          if (data.llm_endpoint) {
            this.validateEndpoint(data.llm_endpoint, data.llm_api_key);
          }
        },
        error: () => {},
      }),
    );
  }

  ngOnDestroy() {
    this.subs.forEach(s => s.unsubscribe());
    if (this.pendingSave && Object.keys(this.pendingSave).length) {
      this.queueSave();
    }
  }

  onFieldChange(field: string, value: string) {
    this.form.update(f => ({ ...f, [field]: value || '' }));
    this.saveError.set(null);
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
    if (!this.pendingSave || !Object.keys(this.pendingSave).length) {
      return;
    }
    this.saveInFlight = true;
    const payload = { ...this.pendingSave };
    this.pendingSave = null;
    this.settingsService.updateSettings(payload).subscribe({
      next: () => {
        this.saveInFlight = false;
        this.saveError.set(null);
        this.saved.set(true);
        setTimeout(() => this.saved.set(false), 2000);
        if (this.saveQueued) {
          this.saveQueued = false;
          this.queueSave();
        }
      },
      error: (err: Error) => {
        this.saveInFlight = false;
        this.saveError.set(err?.message || 'Request failed');
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

  goBack() {
    this.router.navigate(['/dashboard']);
  }
}
