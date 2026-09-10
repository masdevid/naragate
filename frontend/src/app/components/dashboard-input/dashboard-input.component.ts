import { Component, Input, Output, EventEmitter, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { I18nService } from '../../services/i18n.service';
import { NarrativeService } from '../../services/narrative.service';
import { TPipe } from '../../pipes/t.pipe';

interface BulkItem {
  narrative: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'duplicate';
  score?: number;
  verdict?: string;
}

type ScanMode = 'single' | 'bulk';

@Component({
  selector: 'app-dashboard-input',
  standalone: true,
  imports: [FormsModule, TPipe],
  template: `
    <section class="input-section reveal" style="--i: 4">
      <div class="input-section__head">
        <h2 class="input-section__title">{{ 'scanner.title' | t }}</h2>
        <div class="input-section__toggle" role="tablist">
          <button
            type="button"
            role="tab"
            class="input-section__toggle-btn"
            [class.input-section__toggle-btn--active]="mode() === 'single'"
            [attr.aria-selected]="mode() === 'single'"
            [disabled]="running()"
            data-mode="single"
            (click)="setMode('single')">
            {{ 'scanner.mode_single' | t }}
          </button>
          <button
            type="button"
            role="tab"
            class="input-section__toggle-btn"
            [class.input-section__toggle-btn--active]="mode() === 'bulk'"
            [attr.aria-selected]="mode() === 'bulk'"
            [disabled]="running()"
            data-mode="bulk"
            (click)="setMode('bulk')">
            {{ 'scanner.mode_bulk' | t }}
          </button>
        </div>
      </div>

      <textarea
        [(ngModel)]="text"
        class="input-section__field"
        [attr.rows]="mode() === 'single' ? 4 : 6"
        [placeholder]="mode() === 'single' ? ('dashboard.textarea_placeholder' | t) : ('bulk.placeholder' | t)"></textarea>

      @if (mode() === 'single') {
        <button
          (click)="analyze.emit(text)"
          [disabled]="!text.trim() || analyzing"
          class="input-section__btn">
          {{ analyzing ? ('dashboard.analyzing' | t) : ('dashboard.analyze_btn' | t) }}
        </button>
      } @else {
        <div class="bulk__actions">
          <button
            (click)="start()"
            [disabled]="!lines().length || running()"
            class="input-section__btn">
            {{ running() ? ('bulk.running' | t) : ('bulk.scan_btn' | t) }}
          </button>
          @if (running()) {
            <span class="bulk__progress">{{ 'bulk.progress' | t: { current: doneCount(), total: lines().length } }}</span>
          }
        </div>
        @if (running()) {
          <div class="bulk__bar">
            <div class="bulk__bar-fill" [style.width.%]="progressPct()"></div>
          </div>
        }
        @if (items().length) {
          <div class="bulk__items">
            @for (item of items(); track $index) {
              <div class="bulk__item" [class.bulk__item--failed]="item.status === 'failed'">
                <span class="bulk__item-index">{{ $index + 1 }}</span>
                <span class="bulk__item-text">{{ item.narrative }}</span>
                <span class="bulk__item-status">
                  @switch (item.status) {
                    @case ('running') { {{ 'bulk.status_running' | t }} }
                    @case ('completed') { {{ 'bulk.status_done' | t }} — {{ item.score }} }
                    @case ('duplicate') { {{ 'bulk.status_duplicate' | t }} }
                    @case ('failed') { {{ 'bulk.status_failed' | t }} }
                    @default { {{ 'bulk.status_pending' | t }} }
                  }
                </span>
              </div>
            }
          </div>
        }
      }

      @if (mode() === 'single') {
        <div class="input-section__examples">
          <p class="input-section__examples-title">{{ 'dashboard.examples_title' | t }}</p>
          <div class="input-section__examples-grid">
            @for (ex of examples(); track ex.narrative) {
              <button class="input-section__example-card" (click)="useExample(ex.narrative)">
                <span class="input-section__example-tag">{{ ex.tag }}</span>
                <span class="input-section__example-text">{{ ex.narrative }}</span>
              </button>
            }
          </div>
        </div>
      }
    </section>
  `,
  styles: [`
    :host { display: block; }
    .input-section {
      padding: 0 var(--space-lg) var(--space-3xl);
      max-width: 52rem;
      margin: 0 auto;
    }
    .input-section__head {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: var(--space-lg);
      margin-bottom: var(--space-md);
    }
    .input-section__title {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin: 0;
    }
    .input-section__toggle {
      display: inline-flex;
      border: 1px solid var(--color-paper-3);
    }
    .input-section__toggle-btn {
      background: none;
      border: none;
      color: var(--color-muted);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: var(--space-sm) var(--space-lg);
      cursor: pointer;
      transition: all var(--dur-short) var(--ease-out);
    }
    .input-section__toggle-btn:hover:not(:disabled) { color: var(--color-accent); }
    .input-section__toggle-btn--active {
      background: var(--color-accent);
      color: var(--color-paper);
    }
    .input-section__toggle-btn--active:hover:not(:disabled) { color: var(--color-paper); }
    .input-section__toggle-btn:disabled { opacity: 0.4; cursor: not-allowed; }
    .input-section__field {
      width: 100%;
      background: var(--color-paper-2);
      border: none;
      border-top: 1px solid var(--color-rule);
      color: var(--color-ink);
      font-family: var(--font-body);
      font-size: var(--text-base);
      font-weight: 350;
      padding: var(--space-lg);
      resize: none;
      line-height: 1.55;
    }
    .input-section__field::placeholder {
      color: var(--color-dim);
    }
    .input-section__field:focus {
      outline: none;
      border-top-color: var(--color-accent);
    }
    .input-section__btn {
      display: inline-block;
      margin-top: var(--space-lg);
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
    .input-section__btn:hover { opacity: 0.9; }
    .input-section__btn:disabled { opacity: 0.3; cursor: not-allowed; }
    .input-section__examples {
      margin-top: var(--space-xl);
      display: flex;
      flex-direction: column;
      gap: var(--space-sm);
    }
    .input-section__examples-title {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .input-section__examples-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
      gap: var(--space-sm);
    }
    .input-section__example-card {
      display: flex;
      flex-direction: column;
      gap: var(--space-2xs);
      text-align: left;
      background: none;
      border: 1px solid var(--color-paper-3);
      color: var(--color-ink);
      padding: var(--space-md);
      cursor: pointer;
      transition: border-color var(--dur-short) var(--ease-out);
    }
    .input-section__example-card:hover { border-color: var(--color-accent); }
    .input-section__example-tag {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-accent);
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .input-section__example-text {
      font-size: var(--text-sm);
      color: var(--color-muted);
      line-height: 1.5;
    }
    .bulk__actions {
      display: flex;
      align-items: center;
      gap: var(--space-lg);
      margin-top: var(--space-lg);
    }
    .bulk__progress {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-muted);
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .bulk__bar {
      margin-top: var(--space-xl);
      height: 0.5rem;
      background: var(--color-paper-3);
    }
    .bulk__bar-fill {
      height: 100%;
      background: var(--color-accent);
      transition: width var(--dur-med) var(--ease-out);
    }
    .bulk__items {
      margin-top: var(--space-lg);
      display: flex;
      flex-direction: column;
      gap: var(--space-2xs);
    }
    .bulk__item {
      display: flex;
      align-items: center;
      gap: var(--space-md);
      padding: var(--space-sm) var(--space-md);
      border: 1px solid var(--color-paper-3);
      font-size: var(--text-sm);
    }
    .bulk__item--failed { border-color: var(--color-danger); }
    .bulk__item-index {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      width: 1.5rem;
      text-align: right;
    }
    .bulk__item-text {
      flex: 1;
      color: var(--color-ink);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .bulk__item-status {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-muted);
      white-space: nowrap;
    }
    @media (max-width: 640px) {
      .input-section { padding-left: var(--space-md); padding-right: var(--space-md); }
      .input-section__head { flex-direction: column; align-items: flex-start; }
    }
  `],
})
export class DashboardInputComponent {
  text = '';
  @Input() analyzing = false;

  @Output() analyze = new EventEmitter<string>();
  @Output() complete = new EventEmitter<void>();

  mode = signal<ScanMode>('single');
  running = signal(false);
  items = signal<BulkItem[]>([]);
  doneCount = signal(0);

  private i18n = inject(I18nService);
  private narrativeService = inject(NarrativeService);

  setMode(mode: ScanMode) {
    if (this.running()) return;
    this.mode.set(mode);
    this.items.set([]);
    this.doneCount.set(0);
  }

  lines(): string[] {
    return this.text
      .split('\n')
      .map(l => l.trim())
      .filter(l => l.length > 0);
  }

  progressPct(): number {
    const total = this.lines().length;
    return total ? Math.round((this.doneCount() / total) * 100) : 0;
  }

  examples(): { tag: string; narrative: string }[] {
    const en = this.i18n.language() === 'en';
    const t = (key: string) => this.i18n.t(key);
    return [
      { tag: en ? 'Valuation' : 'Valuasi', narrative: t('dashboard.examples.valuation') },
      { tag: en ? 'Fundamental' : 'Fundamental', narrative: t('dashboard.examples.fundamental') },
      { tag: en ? 'Market' : 'Pasar', narrative: t('dashboard.examples.market') },
      { tag: en ? 'News' : 'Berita', narrative: t('dashboard.examples.news') },
      { tag: en ? 'Policy \u00b7 BBM' : 'Kebijakan \u00b7 BBM', narrative: t('dashboard.examples.policy_bbm') },
      { tag: en ? 'Policy \u00b7 HBA' : 'Kebijakan \u00b7 HBA', narrative: t('dashboard.examples.policy_hba') },
      { tag: en ? 'Policy \u00b7 Nickel' : 'Kebijakan \u00b7 Nikel', narrative: t('dashboard.examples.policy_nickel') },
      { tag: en ? 'Needs ticker' : 'Butuh kode', narrative: t('dashboard.examples.no_ticker') },
      { tag: en ? 'Contradiction' : 'Kontradiksi', narrative: t('dashboard.examples.contradiction') },
      { tag: en ? 'Future price' : 'Harga masa depan', narrative: t('dashboard.examples.future_price') },
      { tag: en ? 'Below' : 'Turun', narrative: t('dashboard.examples.below_cpo') },
      { tag: en ? 'Below' : 'Turun', narrative: t('dashboard.examples.below_auto') },
    ];
  }

  useExample(narrative: string) {
    this.text = narrative;
  }

  start() {
    const narratives = this.lines();
    if (!narratives.length || this.running()) return;

    this.running.set(true);
    this.doneCount.set(0);
    this.items.set(narratives.map(narrative => ({ narrative, status: 'pending' as const })));

    this.narrativeService.analyzeBulk(narratives).subscribe({
      next: (event) => {
        if (event.event_type === 'bulk_item_started') {
          const index = event.data?.index ?? 0;
          this.items.update(items => items.map((item, i) => i === index ? { ...item, status: 'running' as const } : item));
        } else if (event.event_type === 'bulk_item_completed') {
          const index = event.data?.index ?? 0;
          this.items.update(items => items.map((item, i) => i === index ? {
            ...item,
            status: (event.data?.status || 'completed') as BulkItem['status'],
            score: event.data?.score,
            verdict: event.data?.verdict,
          } : item));
          this.doneCount.update(c => c + 1);
        }
      },
      error: () => {
        this.running.set(false);
        this.complete.emit();
      },
      complete: () => {
        this.running.set(false);
        this.complete.emit();
      },
    });
  }
}