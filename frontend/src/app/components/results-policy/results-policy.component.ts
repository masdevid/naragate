import { Component, OnInit, inject, signal } from '@angular/core';
import { NarrativeService } from '../../services/narrative.service';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-results-policy',
  standalone: true,
  imports: [TPipe],
  template: `
    @if (precheck(); as p) {
      <section class="policy">
        <p class="policy__label">{{ 'results.policy.title' | t }}</p>

        <div class="policy__verdict-row">
          <span class="policy__verdict" [attr.data-verdict]="p.verdict">{{ p.verdict }}</span>
          <p class="policy__rationale">{{ p.rationale }}</p>
        </div>

        <div class="policy__beacons">
          <span class="policy__key">{{ 'results.policy.beacons' | t }}</span>
          <span class="policy__beacon-list">{{ beaconText() }}</span>
        </div>

        <table class="policy__table">
          <thead>
            <tr>
              <th>{{ 'results.policy.ticker' | t }}</th>
              <th>{{ 'results.policy.subsector' | t }}</th>
              <th>{{ 'results.policy.vol' | t }}</th>
              <th>{{ 'results.policy.ratio' | t }}</th>
              <th>{{ 'results.policy.regime' | t }}</th>
              <th>{{ 'results.policy.signal' | t }}</th>
              <th>{{ 'results.policy.classification' | t }}</th>
            </tr>
          </thead>
          <tbody>
            @for (r of p.results; track r.ticker) {
              <tr>
                <td class="policy__ticker">{{ r.ticker }}</td>
                <td>{{ r.subsector }}</td>
                <td>{{ r.daily_vol }}%</td>
                <td>{{ ratioText(r) }}</td>
                <td>{{ r.price_regime }}</td>
                <td>{{ r.policy_signal }}</td>
                <td>{{ r.classification }}</td>
              </tr>
            }
          </tbody>
        </table>

        <div class="policy__events">
          <span class="policy__key">{{ 'results.policy.events' | t }}</span>
          <ul class="policy__event-list">
            @for (e of p.policy_events; track e.date) {
              <li class="policy__event">
                <span class="policy__event-date">{{ e.date }}</span>
                <span class="policy__event-title">{{ e.title }}</span>
              </li>
            }
          </ul>
        </div>
      </section>
    }
  `,
  styles: [`
    .policy { border-top: 1px solid var(--color-rule); padding: var(--space-lg) 0; }
    .policy__label {
      font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-dim);
      text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: var(--space-sm);
    }
    .policy__verdict-row { display: flex; align-items: flex-start; gap: var(--space-md); margin-bottom: var(--space-md); }
    .policy__verdict {
      font-family: var(--font-mono); font-size: var(--text-xs); font-weight: 600;
      text-transform: uppercase; letter-spacing: 0.08em;
      padding: var(--space-2xs) var(--space-sm);
      border: 1px solid var(--color-dim); color: var(--color-muted); white-space: nowrap;
    }
    .policy__verdict[data-verdict='PASS'] { border-color: var(--color-success); color: var(--color-success); }
    .policy__verdict[data-verdict='CONDITIONAL'] { border-color: var(--color-warning); color: var(--color-warning); }
    .policy__verdict[data-verdict='FAIL'] { border-color: var(--color-danger); color: var(--color-danger); }
    .policy__rationale { font-size: var(--text-sm); color: var(--color-muted); line-height: 1.55; margin: 0; }
    .policy__beacons { display: flex; gap: var(--space-md); margin-bottom: var(--space-md); }
    .policy__key {
      font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-dim);
      text-transform: uppercase; letter-spacing: 0.06em;
    }
    .policy__beacon-list { font-family: var(--font-mono); font-size: var(--text-sm); color: var(--color-ink); }
    .policy__table {
      width: 100%; border-collapse: collapse; margin-bottom: var(--space-md);
      font-family: var(--font-mono); font-size: var(--text-xs);
    }
    .policy__table th {
      text-align: left; color: var(--color-dim); text-transform: uppercase; letter-spacing: 0.04em;
      font-weight: 400; padding: var(--space-2xs) var(--space-xs); border-bottom: 1px solid var(--color-rule);
    }
    .policy__table td { padding: var(--space-2xs) var(--space-xs); border-bottom: 1px solid var(--color-paper-3); color: var(--color-muted); }
    .policy__table .policy__ticker { color: var(--color-ink); font-weight: 600; }
    .policy__events { display: flex; flex-direction: column; gap: var(--space-sm); }
    .policy__event-list { list-style: none; padding: 0; margin: 0; }
    .policy__event { display: flex; gap: var(--space-sm); padding: var(--space-2xs) 0; font-size: var(--text-sm); }
    .policy__event-date { font-family: var(--font-mono); color: var(--color-accent); min-width: 5.5rem; flex-shrink: 0; }
    .policy__event-title { color: var(--color-muted); line-height: 1.45; }
    @media (max-width: 640px) {
      .policy__table { display: block; overflow-x: auto; }
    }
  `],
})
export class ResultsPolicyComponent implements OnInit {
  private narrativeService = inject(NarrativeService);

  precheck = signal<any | null>(null);

  ngOnInit() {
    this.narrativeService.getPrecheck().subscribe({
      next: (data) => this.precheck.set(data),
      error: () => this.precheck.set(null), // hidden when the pre-check is unavailable
    });
  }

  beaconText(): string {
    const beacons = this.precheck()?.beacon_list ?? [];
    return beacons.length ? beacons.join(', ') : '—';
  }

  ratioText(r: any): string {
    return r.data_days ? `${r.policy_ratio}x` : '—';
  }
}
