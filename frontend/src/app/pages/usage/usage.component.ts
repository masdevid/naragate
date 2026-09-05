import { Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { DatePipe } from '@angular/common';
import { UsageService, UsageSummary } from '../../services/usage.service';
import { I18nService } from '../../services/i18n.service';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-usage',
  standalone: true,
  imports: [DatePipe, TPipe],
  template: `
    <div class="usage">
      <div class="usage__inner">
        <button (click)="goBack()" class="usage__back">&larr; {{ 'usage.back' | t }}</button>
        <h1 class="usage__title">{{ 'usage.title' | t }}</h1>
        <p class="usage__sub">{{ 'usage.sub' | t }}</p>

        @if (loading()) {
          <p class="usage__status">{{ 'usage.loading' | t }}</p>
        } @else if (error()) {
          <p class="usage__status usage__status--err">{{ error() }}</p>
        } @else if (usage()) {
          <!-- Sectors API -->
          <section class="usage__card">
            <div class="usage__card-head">
              <h2 class="usage__card-title">{{ 'usage.section_sectors' | t }}</h2>
              <span class="usage__card-pct">{{ usage()!.sectors.budget_pct }}%</span>
            </div>
            <div class="usage__bar">
              <div class="usage__bar-fill" [style.width.%]="barWidth()"></div>
            </div>
            <div class="usage__stats">
              <div class="usage__stat">
                <span class="usage__stat-key">{{ 'usage.used' | t }}</span>
                <span class="usage__stat-val">{{ fmt(usage()!.sectors.total_calls) }}</span>
              </div>
              <div class="usage__stat">
                <span class="usage__stat-key">{{ 'usage.cached' | t }}</span>
                <span class="usage__stat-val">{{ fmt(usage()!.sectors.cached_calls) }}</span>
              </div>
              <div class="usage__stat">
                <span class="usage__stat-key">{{ 'usage.budget' | t }}</span>
                <span class="usage__stat-val">{{ fmt(usage()!.sectors.budget) }}</span>
              </div>
              <div class="usage__stat">
                <span class="usage__stat-key">{{ 'usage.remaining' | t }}</span>
                <span class="usage__stat-val">{{ fmt(usage()!.sectors.remaining) }}</span>
              </div>
            </div>
          </section>

          <!-- LLM usage -->
          <section class="usage__card">
            <div class="usage__card-head">
              <h2 class="usage__card-title">{{ 'usage.section_llm' | t }}</h2>
              <span class="usage__card-model">{{ usage()!.llm.model }}</span>
            </div>
            <div class="usage__stats">
              <div class="usage__stat">
                <span class="usage__stat-key">{{ 'usage.calls' | t }}</span>
                <span class="usage__stat-val">{{ fmt(usage()!.llm.total_calls) }}</span>
              </div>
              <div class="usage__stat">
                <span class="usage__stat-key">{{ 'usage.input_tokens' | t }}</span>
                <span class="usage__stat-val">{{ fmt(usage()!.llm.input_tokens) }}</span>
              </div>
              <div class="usage__stat">
                <span class="usage__stat-key">{{ 'usage.output_tokens' | t }}</span>
                <span class="usage__stat-val">{{ fmt(usage()!.llm.output_tokens) }}</span>
              </div>
              <div class="usage__stat">
                <span class="usage__stat-key">{{ 'usage.total_tokens' | t }}</span>
                <span class="usage__stat-val">{{ fmt(usage()!.llm.total_tokens) }}</span>
              </div>
              <div class="usage__stat">
                <span class="usage__stat-key">{{ 'usage.est_cost' | t }}</span>
                <span class="usage__stat-val">{{ fmtCost(usage()!.llm.estimated_cost_usd) }}</span>
              </div>
            </div>
          </section>

          <!-- Pipelines -->
          <section class="usage__card">
            <div class="usage__card-head">
              <h2 class="usage__card-title">{{ 'usage.section_pipelines' | t }}</h2>
            </div>
            <div class="usage__stats">
              <div class="usage__stat">
                <span class="usage__stat-key">{{ 'usage.total' | t }}</span>
                <span class="usage__stat-val">{{ fmt(usage()!.pipelines.total) }}</span>
              </div>
              <div class="usage__stat">
                <span class="usage__stat-key">{{ 'usage.completed' | t }}</span>
                <span class="usage__stat-val usage__stat-val--ok">{{ fmt(usage()!.pipelines.completed) }}</span>
              </div>
              <div class="usage__stat">
                <span class="usage__stat-key">{{ 'usage.failed' | t }}</span>
                <span class="usage__stat-val usage__stat-val--err">{{ fmt(usage()!.pipelines.failed) }}</span>
              </div>
            </div>
          </section>

          <!-- Daily breakdown -->
          <section class="usage__card">
            <div class="usage__card-head">
              <h2 class="usage__card-title">{{ 'usage.section_daily' | t }}</h2>
            </div>
            <table class="usage__table">
              <thead>
                <tr>
                  <th>{{ 'usage.date' | t }}</th>
                  <th>{{ 'usage.sectors_calls' | t }}</th>
                  <th>{{ 'usage.llm_calls' | t }}</th>
                  <th>{{ 'usage.input_tokens' | t }}</th>
                  <th>{{ 'usage.output_tokens' | t }}</th>
                </tr>
              </thead>
              <tbody>
                @for (day of dailyRows(); track day.date) {
                  <tr>
                    <td>{{ day.date | date:'EEE, MMM d' }}</td>
                    <td>{{ fmt(day.sectors_calls) }}</td>
                    <td>{{ fmt(day.llm_calls) }}</td>
                    <td>{{ fmt(day.llm_input_tokens) }}</td>
                    <td>{{ fmt(day.llm_output_tokens) }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </section>
        }
      </div>
    </div>
  `,
  styles: [`
    .usage {
      padding: var(--space-2xl) var(--space-lg);
    }
    .usage__inner {
      max-width: 48rem;
      margin: 0 auto;
    }
    .usage__back {
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
    .usage__back:hover { color: var(--color-ink); }

    .usage__title {
      font-family: var(--font-display);
      font-size: var(--text-2xl);
      text-transform: uppercase;
      margin-bottom: var(--space-xs);
    }
    .usage__sub {
      font-size: var(--text-sm);
      color: var(--color-muted);
      margin-bottom: var(--space-2xl);
    }
    .usage__status {
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      color: var(--color-muted);
      padding: var(--space-4xl) 0;
      text-align: center;
    }
    .usage__status--err { color: var(--color-danger); }

    .usage__card {
      border-top: 1px solid var(--color-rule);
      padding: var(--space-xl) 0;
    }
    .usage__card-head {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: var(--space-md);
      margin-bottom: var(--space-lg);
    }
    .usage__card-title {
      font-family: var(--font-display);
      font-size: var(--text-md);
      text-transform: uppercase;
    }
    .usage__card-pct {
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      color: var(--color-accent);
      font-variant-numeric: tabular-nums;
    }
    .usage__card-model {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
    }

    .usage__bar {
      height: 4px;
      background: var(--color-paper-3);
      margin-bottom: var(--space-lg);
    }
    .usage__bar-fill {
      height: 100%;
      background: var(--color-accent);
      transition: width var(--dur-long) var(--ease-out);
    }

    .usage__stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(8rem, 1fr));
      gap: var(--space-md);
    }
    .usage__stat {
      display: flex;
      flex-direction: column;
      gap: var(--space-3xs);
    }
    .usage__stat-key {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .usage__stat-val {
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      color: var(--color-ink);
      font-variant-numeric: tabular-nums;
    }
    .usage__stat-val--ok { color: var(--color-success); }
    .usage__stat-val--err { color: var(--color-danger); }

    .usage__table {
      width: 100%;
      border-collapse: collapse;
      font-family: var(--font-mono);
      font-size: var(--text-xs);
    }
    .usage__table th {
      text-align: left;
      color: var(--color-dim);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      font-weight: 400;
      padding: var(--space-xs) var(--space-sm);
      border-bottom: 1px solid var(--color-rule);
    }
    .usage__table td {
      padding: var(--space-sm);
      color: var(--color-muted);
      border-bottom: 1px solid var(--color-paper-3);
      font-variant-numeric: tabular-nums;
    }
    .usage__table td:first-child { color: var(--color-ink); }

    @media (max-width: 640px) {
      .usage { padding: var(--space-lg) var(--space-md); }
      .usage__stats { grid-template-columns: repeat(2, 1fr); }
    }
  `],
})
export class UsageComponent implements OnInit {
  private usageService = inject(UsageService);
  private router = inject(Router);
  private i18n = inject(I18nService);

  usage = signal<UsageSummary | null>(null);
  loading = signal(true);
  error = signal('');

  ngOnInit() {
    this.usageService.getUsage().subscribe({
      next: (data) => { this.usage.set(data); this.loading.set(false); },
      error: (err) => { this.error.set(err.message || this.i18n.t('usage.load_error')); this.loading.set(false); },
    });
  }

  goBack() { this.router.navigate(['/dashboard']); }

  dailyRows() {
    return this.usage()?.daily ? [...this.usage()!.daily].reverse() : [];
  }

  barWidth() {
    return Math.min(this.usage()?.sectors.budget_pct ?? 0, 100);
  }

  fmt(n: number): string {
    return (n ?? 0).toLocaleString();
  }

  fmtCost(n: number): string {
    const v = n ?? 0;
    if (v === 0) return '$0.00';
    if (v < 0.01) return '$' + v.toFixed(6);
    return '$' + v.toFixed(2);
  }
}