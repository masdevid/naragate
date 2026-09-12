import { Component, OnInit, OnDestroy, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Subscription, Subject, debounceTime, switchMap, tap } from 'rxjs';
import { SettingsService, RuntimeSettings, ValidateResult, SectorsValidateResult, SetupStatus } from '../../services/settings.service';
import { TPipe } from '../../pipes/t.pipe';
import { SecretKeyInputComponent } from '../../components/masked-key-input/secret-key-input.component';
import { SetupLlmStepComponent } from '../../components/setup-llm-step/setup-llm-step.component';

const DISMISS_KEY = 'naragate_setup_dismissed';

@Component({
  selector: 'app-setup',
  standalone: true,
  imports: [FormsModule, TPipe, SecretKeyInputComponent, SetupLlmStepComponent],
  template: `
    <div class="setup">
      <div class="setup__inner">
        <div class="setup__brand">Naragate</div>

        <div class="setup__progress">
          @for (s of stepList; track s) {
            <span class="setup__dot"
              [class.setup__dot--active]="step() === s"
              [class.setup__dot--done]="step() > s"></span>
          }
        </div>

        <!-- Step 1: Welcome -->
        @if (step() === 1) {
          <div class="setup__panel">
            <h1 class="setup__title">{{ 'setup.welcome_title' | t }}</h1>
            <p class="setup__text">{{ 'setup.welcome_text' | t }}</p>
            <p class="setup__text">{{ 'setup.welcome_need' | t }}</p>
            <ul class="setup__list">
              <li>{{ 'setup.need_llm' | t }}</li>
              <li>{{ 'setup.need_sectors' | t }}</li>
            </ul>
            <div class="setup__actions">
              <button (click)="skip()" class="setup__btn setup__btn--ghost">{{ 'setup.skip' | t }}</button>
              <button (click)="next()" class="setup__btn">{{ 'setup.start' | t }}</button>
            </div>
          </div>
        }

        <!-- Step 2: LLM provider -->
        @if (step() === 2) {
          <div class="setup__panel">
            <h1 class="setup__title">{{ 'setup.llm_title' | t }}</h1>
            <p class="setup__text">{{ 'setup.llm_text' | t }}</p>

            <app-setup-llm-step
              [form]="form"
              [availableModels]="availableModels"
              [validating]="validating"
              [validation]="validation"
              (fieldChange)="onFieldChange($event.field, $event.value)"
              (endpointChange)="onEndpointChange($event)"/>

            <div class="setup__actions">
              <button (click)="skip()" class="setup__btn setup__btn--ghost">{{ 'setup.skip' | t }}</button>
              <button (click)="next()" class="setup__btn">{{ 'setup.next' | t }}</button>
            </div>
          </div>
        }

        <!-- Step 3: Sectors API -->
        @if (step() === 3) {
          <div class="setup__panel">
            <h1 class="setup__title">{{ 'setup.sectors_title' | t }}</h1>
            <p class="setup__text">{{ 'setup.sectors_text' | t }}</p>

            <div class="setup__field">
              <label class="setup__label">{{ 'settings.field_sectors_key' | t }}</label>
              <div class="setup__input-row">
                <app-secret-key-input [value]="form().sectors_api_key"
                  (valueChange)="onFieldChange('sectors_api_key', $event)"
                  inputClass="setup__input setup__input--flex"
                  [placeholder]="'settings.sectors_key_placeholder' | t"/>
                <button (click)="validateSectorsKey()" [disabled]="!sectorsKeyPresent() || sectorsValidating()"
                  class="setup__validate-btn">
                  {{ 'settings.sectors_validate' | t }}
                </button>
              </div>
              @if (form().client_ip) {
                <p class="setup__hint" style="margin-top: var(--space-sm)">
                  {{ 'settings.sectors_bound_ip' | t:{ip: maskedIp(form().client_ip || '')} }}
                </p>
              }
              <span class="setup__status" [class.setup__status--ok]="sectorsValidation()?.ok === true"
                [class.setup__status--err]="sectorsValidation()?.ok === false"
                [class.setup__status--loading]="sectorsValidating()">
                @if (sectorsValidating()) {
                  {{ 'settings.validating' | t }}
                } @else if (sectorsValidation()?.ok === true) {
                  {{ 'settings.sectors_valid_ok' | t }}
                } @else if (sectorsValidation()?.ok === false) {
                  {{ 'settings.sectors_valid_error' | t }}
                }
              </span>
            </div>

            <div class="setup__actions">
              <button (click)="back()" class="setup__btn setup__btn--ghost">{{ 'setup.back' | t }}</button>
              <button (click)="next()" class="setup__btn">{{ 'setup.next' | t }}</button>
            </div>
          </div>
        }

        <!-- Step 4: Done -->
        @if (step() === 4) {
          <div class="setup__panel">
            <h1 class="setup__title">{{ 'setup.done_title' | t }}</h1>
            <p class="setup__text">{{ 'setup.done_text' | t }}</p>
            <div class="setup__actions">
              <button (click)="finish()" class="setup__btn">{{ 'setup.finish' | t }}</button>
            </div>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .setup {
      min-height: 100vh;
      padding: var(--space-2xl) var(--space-lg);
    }
    .setup__inner {
      max-width: 32rem;
      margin: 0 auto;
    }
    .setup__brand {
      font-family: var(--font-display);
      font-size: var(--text-md);
      text-transform: uppercase;
      letter-spacing: 0.02em;
      color: var(--color-ink);
      margin-bottom: var(--space-2xl);
    }
    .setup__progress {
      display: flex;
      gap: var(--space-xs);
      margin-bottom: var(--space-3xl);
    }
    .setup__dot {
      width: 2rem;
      height: 2px;
      background: var(--color-paper-3);
      transition: background var(--dur-short) var(--ease-out);
    }
    .setup__dot--active { background: var(--color-accent); }
    .setup__dot--done { background: var(--color-muted); }

    .setup__title {
      font-family: var(--font-display);
      font-size: var(--text-2xl);
      text-transform: uppercase;
      margin-bottom: var(--space-md);
    }
    .setup__text {
      font-size: var(--text-sm);
      color: var(--color-muted);
      line-height: 1.6;
      margin-bottom: var(--space-md);
    }
    .setup__list {
      margin: 0 0 var(--space-xl) var(--space-lg);
      color: var(--color-muted);
      font-size: var(--text-sm);
      line-height: 1.7;
    }

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
    .setup__status {
      display: block;
      margin-top: var(--space-2xs);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .setup__status--ok { color: var(--color-success); }
    .setup__status--err { color: var(--color-danger); }
    .setup__status--loading { color: var(--color-warning); }

    .setup__validate-btn {
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
    .setup__validate-btn:hover {
      background: var(--color-accent);
      color: var(--color-paper);
    }
    .setup__validate-btn:disabled {
      opacity: 0.3;
      cursor: not-allowed;
    }

    .setup__actions {
      display: flex;
      justify-content: flex-end;
      gap: var(--space-md);
      margin-top: var(--space-2xl);
    }
    .setup__btn {
      padding: var(--space-md) var(--space-xl);
      background: var(--color-accent);
      color: var(--color-paper);
      border: none;
      font-family: var(--font-display);
      font-size: var(--text-md);
      text-transform: uppercase;
      letter-spacing: 0.02em;
      cursor: pointer;
      transition: opacity var(--dur-short) var(--ease-out);
    }
    .setup__btn:hover { opacity: 0.9; }
    .setup__btn--ghost {
      background: none;
      color: var(--color-muted);
      border: 1px solid var(--color-rule);
    }

    @media (max-width: 640px) {
      .setup { padding: var(--space-lg) var(--space-md); }
      .setup__input-row { flex-direction: column; align-items: stretch; }
    }
  `],
})
export class SetupComponent implements OnInit, OnDestroy {
  step = signal(1);
  stepList = [1, 2, 3, 4];
  form = signal<RuntimeSettings>({});
  validating = signal(false);
  validation = signal<ValidateResult | null>(null);
  availableModels = signal<string[]>([]);
  sectorsValidating = signal(false);
  sectorsValidation = signal<SectorsValidateResult | null>(null);
  setupStatus = signal<SetupStatus | null>(null);

  maskedIp = (ip: string): string => {
    if (!ip) return '';
    const parts = ip.split('.');
    if (parts.length !== 4) return '***';
    return `${parts[0]}.***.***.${parts[3]}`;
  };

  private settingsService = inject(SettingsService);
  private router = inject(Router);

  private endpoint$ = new Subject<string>();
  private subs: Subscription[] = [];

  ngOnInit() {
    this.subs.push(
      this.settingsService.getSettings().subscribe({
        next: (settings) => {
          this.form.set(settings);
          this.settingsService.getSetupStatus().subscribe({
            next: (status) => {
              this.setupStatus.set(status);
              this.computeStartStep();
            },
            error: () => this.computeStartStep(),
          });
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
  }

  private computeStartStep() {
    const f = this.form();
    const llmDone = !!(f.llm_endpoint && f.llm_model);
    const sectorsDone = !!(f.sectors_api_key);
    if (llmDone && sectorsDone) {
      this.step.set(4);
    } else if (!llmDone && !sectorsDone) {
      this.step.set(1);
    } else if (!llmDone) {
      this.step.set(2);
    } else {
      this.step.set(3);
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
  }

  onFieldChange(field: string, value: string) {
    this.form.update(f => ({ ...f, [field]: value || '' }));
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

  private saveStep() {
    const f = this.form();
    const patch: RuntimeSettings = {};
    if (this.step() === 2) {
      patch.llm_endpoint = f.llm_endpoint;
      patch.llm_api_key = f.llm_api_key;
      patch.llm_model = f.llm_model;
    } else if (this.step() === 3) {
      const sectors = (f.sectors_api_key || '').trim();
      if (sectors && !sectors.includes('...') && !sectors.includes('••••')) {
        patch.sectors_api_key = sectors;
      }
    }
    if (Object.keys(patch).length) {
      this.settingsService.updateSettings(patch).subscribe({ error: () => {} });
    }
  }

  next() {
    this.saveStep();
    this.step.update(s => Math.min(s + 1, 4));
  }

  back() {
    this.step.update(s => Math.max(s - 1, 1));
  }

  skip() {
    try { localStorage.setItem(DISMISS_KEY, '1'); } catch {}
    this.router.navigate(['/dashboard']);
  }

  finish() {
    this.saveStep();
    this.router.navigate(['/dashboard']);
  }
}