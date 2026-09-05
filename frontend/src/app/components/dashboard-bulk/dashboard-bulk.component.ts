import { Component, Output, EventEmitter, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NarrativeService } from '../../services/narrative.service';
import { I18nService } from '../../services/i18n.service';
import { TPipe } from '../../pipes/t.pipe';

interface BulkItem {
  narrative: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'duplicate';
  score?: number;
  verdict?: string;
}

@Component({
  selector: 'app-dashboard-bulk',
  standalone: true,
  imports: [FormsModule, TPipe],
  template: `
    <section class="bulk reveal" style="--i: 5">
      <div class="bulk__inner">
        <h2 class="bulk__title">{{ 'bulk.title' | t }}</h2>

        <textarea
          [(ngModel)]="text"
          class="bulk__field"
          [placeholder]="'bulk.placeholder' | t"
          rows="5"></textarea>

        <div class="bulk__actions">
          <button
            (click)="start()"
            [disabled]="!lines().length || running()"
            class="bulk__btn">
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
      </div>
    </section>
  `,
  styles: [`
    :host { display: block; }
    .bulk {
      padding: 0 var(--space-lg) var(--space-3xl);
      max-width: 52rem;
      margin: 0 auto;
    }
    .bulk__title {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: var(--space-md);
    }
    .bulk__field {
      width: 100%;
      background: var(--color-paper-2);
      border: none;
      border-top: 1px solid var(--color-rule);
      color: var(--color-ink);
      font-family: var(--font-body);
      font-size: var(--text-base);
      font-weight: 350;
      padding: var(--space-lg);
      resize: vertical;
      line-height: 1.55;
    }
    .bulk__field::placeholder { color: var(--color-dim); }
    .bulk__field:focus {
      outline: none;
      border-top-color: var(--color-accent);
    }
    .bulk__actions {
      display: flex;
      align-items: center;
      gap: var(--space-lg);
      margin-top: var(--space-lg);
    }
    .bulk__btn {
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
    .bulk__btn:hover { opacity: 0.9; }
    .bulk__btn:disabled { opacity: 0.3; cursor: not-allowed; }
    .bulk__progress {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-muted);
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .bulk__bar {
      margin-top: var(--space-lg);
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
      .bulk { padding-left: var(--space-md); padding-right: var(--space-md); }
    }
  `],
})
export class DashboardBulkComponent {
  @Output() complete = new EventEmitter<void>();

  text = '';
  running = signal(false);
  items = signal<BulkItem[]>([]);
  doneCount = signal(0);

  private narrativeService = inject(NarrativeService);
  private i18n = inject(I18nService);

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
      error: (err) => {
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