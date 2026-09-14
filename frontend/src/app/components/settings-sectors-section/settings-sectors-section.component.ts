import { Component, Input, Output, EventEmitter, inject, signal, computed } from '@angular/core';
import { SettingsService, SectorsValidateResult } from '../../services/settings.service';
import { I18nService } from '../../services/i18n.service';
import { TPipe } from '../../pipes/t.pipe';
import { SecretKeyInputComponent } from '../masked-key-input/secret-key-input.component';

/**
 * Settings section for the Sectors API key: key input + validation plus,
 * for the key owner, the per-IP allowlist management.
 */
@Component({
  selector: 'app-settings-sectors-section',
  standalone: true,
  imports: [TPipe, SecretKeyInputComponent],
  template: `
    <section class="sect">
      <h2 class="sect__heading">{{ 'settings.section_sectors' | t }}</h2>

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
        @if (clientIp) {
          <div class="sect__hint-row">
            <p class="sect__hint sect__hint--inline">
              @if (isOwner) {
                {{ 'settings.sectors_owner_info' | t:{ip: showIps() ? clientIp : maskedClientIp()} }}
              } @else {
                {{ 'settings.sectors_non_owner_info' | t:{owner: showIps() ? (ownerIp || '—') : maskedOwnerIp() || '—', ips: showIps() ? authorizedIps.join(', ') : maskedAuthorizedIps().join(', ')} }}
              }
            </p>
            @if (!isOwner) {
              <button type="button" class="sect__reveal-btn" (click)="showIps.set(!showIps())">
                {{ (showIps() ? 'settings.key_hide' : 'settings.key_show') | t }}
              </button>
            }
          </div>
        }
        @if (isOwner) {
          <div class="sect__ips">
            <div class="sect__ips-header">
              <p class="sect__label sect__ips-title">{{ 'settings.sectors_ips_title' | t }}</p>
              <button type="button" class="sect__reveal-btn" (click)="showIps.set(!showIps())">
                {{ (showIps() ? 'settings.key_hide' : 'settings.key_show') | t }}
              </button>
            </div>
            <ul class="sect__ips-list">
              @for (aip of authorizedIps; track aip) {
                <li class="sect__ip">
                  <span>{{ showIps() ? aip : maskIp(aip) }}</span>
                  @if (aip !== clientIp) {
                    <button type="button" class="sect__ip-remove" (click)="removeSectorsIp(aip)">
                      {{ 'settings.sectors_remove_ip' | t }}
                    </button>
                  }
                </li>
              }
            </ul>
            <div class="sect__ips-add">
              <input #ipInput class="sect__input sect__ips-input"
                [placeholder]="'settings.sectors_add_ip_placeholder' | t"
                (keydown.enter)="addSectorsIp(ipInput); ipInput.value = ''"/>
              <button type="button" class="sect__ip-add-btn"
                (click)="addSectorsIp(ipInput); ipInput.value = ''">
                {{ 'settings.sectors_add_ip' | t }}
              </button>
            </div>
            @if (ipsMessage()) {
              <span class="sect__status" [class.sect__status--err]="ipsError()">
                {{ ipsMessage() }}
              </span>
            }
          </div>
        }
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
    .sect__input-row {
      display: flex;
      align-items: center;
      gap: var(--space-md);
    }
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
    .sect__hint-row {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: var(--space-sm);
      margin-top: var(--space-sm);
    }
    .sect__hint--inline { margin-bottom: 0; }
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
    .sect__ips {
      margin-top: var(--space-md);
      padding-left: var(--space-sm);
      border-left: 1px solid var(--color-rule);
    }
    .sect__ips-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--space-sm);
    }
    .sect__ips-header .sect__ips-title { margin-top: 0; }
    .sect__ips-title { margin-top: 0; }
    .sect__ips-list {
      list-style: none;
      margin: 0 0 var(--space-sm) 0;
      padding: 0;
    }
    .sect__ip {
      display: flex;
      align-items: center;
      gap: var(--space-sm);
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      color: var(--color-ink);
      padding: var(--space-3xs) 0;
    }
    .sect__ip-remove {
      background: none;
      border: none;
      color: var(--color-danger);
      font-family: var(--font-mono);
      font-size: var(--text-2xs);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      cursor: pointer;
      padding: 0;
    }
    .sect__ips-add {
      display: flex;
      gap: var(--space-2xs);
      align-items: center;
    }
    .sect__ips-input { flex: 1; }
    .sect__ip-add-btn {
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
      transition: background var(--dur-short) var(--ease-out), color var(--dur-short) var(--ease-out);
    }
    .sect__ip-add-btn:hover { background: var(--color-accent); color: var(--color-paper); }

    @media (max-width: 640px) {
      .sect__input-row { flex-direction: column; align-items: stretch; }
      .sect__ips-add { flex-direction: column; align-items: stretch; }
    }
  `],
})
export class SettingsSectorsSectionComponent {
  @Input() sectorsApiKey: string | undefined = '';
  @Input() keyBoundTo: string | null | undefined = '';
  @Input() clientIp: string | null = null;
  @Input() ownerIp: string | null = null;
  @Input() authorizedIps: string[] = [];
  @Input() isOwner = false;
  @Output() authorizedIpsChange = new EventEmitter<string[]>();
  @Output() fieldChange = new EventEmitter<{ field: string; value: string }>();

  sectorsValidating = signal(false);
  sectorsValidation = signal<SectorsValidateResult | null>(null);
  ipsMessage = signal('');
  ipsError = signal(false);
  showIps = signal(false);

  private settingsService = inject(SettingsService);
  private i18n = inject(I18nService);

  maskIp = (ip: string): string => {
    if (!ip) return '';
    const parts = ip.split('.');
    if (parts.length !== 4) return '***';
    return `${parts[0]}.***.***.${parts[3]}`;
  };

  maskedClientIp = computed(() => this.maskIp(this.clientIp || ''));
  maskedOwnerIp = computed(() => this.maskIp(this.ownerIp || ''));
  maskedAuthorizedIps = computed(() => this.authorizedIps.map(ip => this.maskIp(ip)));

  sectorsKeyPresent(): boolean {
    return !!(this.sectorsApiKey && this.sectorsApiKey.trim()) || !!this.keyBoundTo;
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

  addSectorsIp(input: HTMLInputElement) {
    const ip = (input.value || '').trim();
    if (!ip) return;
    this.settingsService.updateSectorsIp(ip, 'add').subscribe({
      next: (data: any) => {
        this.authorizedIpsChange.emit(data.sectors_authorized_ips || []);
        this.ipsMessage.set(this.i18n.t('settings.sectors_ip_added'));
        this.ipsError.set(false);
      },
      error: () => {
        this.ipsMessage.set(this.i18n.t('settings.sectors_ip_error'));
        this.ipsError.set(true);
      },
    });
  }

  removeSectorsIp(ip: string) {
    this.settingsService.updateSectorsIp(ip, 'remove').subscribe({
      next: (data: any) => {
        this.authorizedIpsChange.emit(data.sectors_authorized_ips || []);
        this.ipsMessage.set(this.i18n.t('settings.sectors_ip_removed'));
        this.ipsError.set(false);
      },
      error: () => {
        this.ipsMessage.set(this.i18n.t('settings.sectors_ip_error'));
        this.ipsError.set(true);
      },
    });
  }
}
