import { Component, OnInit, OnDestroy, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { NarrativeService } from '../../services/narrative.service';
import { I18nService } from '../../services/i18n.service';
import { FormatService } from '../../services/format.service';
import { PipelineEvent } from '../../models/pipeline.model';
import { PipelineProgressComponent } from '../../components/pipeline-progress/pipeline-progress.component';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-claim',
  standalone: true,
  imports: [PipelineProgressComponent, TPipe],
  template: `
    <div class="claim">
      <div class="claim__inner">
        <button (click)="goBack()" class="claim__back">&larr; {{ 'claim.back' | t }}</button>

        <div class="claim__narrative">
          <p class="claim__quote">&ldquo;{{ narrative() }}&rdquo;</p>
        </div>

        <div class="claim__progress">
          <app-pipeline-progress [currentStep]="currentStep()" [completedSteps]="completedSteps()"/>
        </div>

        @if (connecting()) {
          <div class="claim__connecting">
            <span class="claim__connecting-spinner"></span>
            <span>{{ 'claim.starting' | t }}</span>
          </div>
        }

        @if (usage()) {
          <div class="claim__usage">
            <span class="claim__usage-label">{{ 'claim.usage' | t }}</span>
            <span class="claim__usage-item">{{ 'usage.sectors_calls' | t }}: {{ fmtNumber(usage().sectors_calls, 0) }}</span>
            <span class="claim__usage-item">{{ 'usage.llm_calls' | t }}: {{ fmtNumber(usage().llm_calls, 0) }}</span>
            <span class="claim__usage-item">{{ 'usage.input_tokens' | t }}: {{ fmtNumber(usage().llm_input_tokens, 0) }}</span>
            <span class="claim__usage-item">{{ 'usage.output_tokens' | t }}: {{ fmtNumber(usage().llm_output_tokens, 0) }}</span>
          </div>
        }

        @if (thinking()) {
          <div class="claim__thinking">
            <h2 class="claim__thinking-title">{{ 'claim.thinking' | t }} &mdash; {{ thinking()?.agent }}</h2>
            <pre class="claim__thinking-text">{{ thinking()?.text }}</pre>
          </div>
        }

        @if (currentEvent()) {
          <div class="claim__event">
            <h2 class="claim__event-title">{{ getEventTitle() }}</h2>
            <pre class="claim__event-data">{{ formatEvent(currentEvent()) }}</pre>
          </div>
        }

        @if (error()) {
          <div class="claim__error">
            <p>{{ error() }}</p>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .claim {
      min-height: 100vh;
      padding: var(--space-2xl) var(--space-lg);
    }
    .claim__inner {
      max-width: 48rem;
      margin: 0 auto;
    }
    .claim__back {
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
    .claim__back:hover { color: var(--color-ink); }
    .claim__narrative {
      border-top: 1px solid var(--color-rule);
      padding: var(--space-lg) 0;
      margin-bottom: var(--space-xl);
    }
    .claim__quote {
      font-size: var(--text-md);
      color: var(--color-muted);
      line-height: 1.55;
      font-style: italic;
    }
    .claim__progress { margin-bottom: var(--space-xl); }
    .claim__connecting {
      display: flex; align-items: center; gap: var(--space-sm);
      border-top: 1px solid var(--color-rule); padding: var(--space-lg) 0;
      margin-bottom: var(--space-lg); font-family: var(--font-mono);
      font-size: var(--text-xs); color: var(--color-muted);
      text-transform: uppercase; letter-spacing: 0.06em;
    }
    .claim__connecting-spinner {
      width: 0.75rem; height: 0.75rem; border: 2px solid var(--color-accent);
      border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .claim__usage {
      display: flex; flex-wrap: wrap; gap: var(--space-md);
      border-top: 1px solid var(--color-rule); padding: var(--space-md) 0;
      margin-bottom: var(--space-lg); font-family: var(--font-mono); font-size: var(--text-xs);
    }
    .claim__usage-label {
      color: var(--color-dim); text-transform: uppercase; letter-spacing: 0.06em;
      margin-right: var(--space-sm);
    }
    .claim__usage-item { color: var(--color-muted); }
    .claim__thinking {
      border-top: 1px solid var(--color-rule); padding-top: var(--space-lg);
      margin-bottom: var(--space-lg);
    }
    .claim__thinking-title {
      font-family: var(--font-display); font-size: var(--text-md);
      text-transform: uppercase; margin-bottom: var(--space-md);
    }
    .claim__thinking-text {
      font-family: var(--font-mono); font-size: var(--text-xs);
      color: var(--color-muted); background: var(--color-paper-2);
      padding: var(--space-lg); overflow-x: auto; line-height: 1.6;
      white-space: pre-wrap; word-break: break-word;
      max-height: 16rem; overflow-y: auto;
    }
    .claim__event {
      border-top: 1px solid var(--color-rule);
      padding-top: var(--space-lg);
    }
    .claim__event-title {
      font-family: var(--font-display);
      font-size: var(--text-lg);
      text-transform: uppercase;
      margin-bottom: var(--space-md);
    }
    .claim__event-data {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-muted);
      background: var(--color-paper-2);
      padding: var(--space-lg);
      overflow-x: auto;
      line-height: 1.6;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .claim__error {
      border-top: 1px solid var(--color-danger);
      padding-top: var(--space-lg);
      margin-top: var(--space-lg);
      color: var(--color-danger);
      font-family: var(--font-mono);
      font-size: var(--text-sm);
    }
    @media (max-width: 640px) { .claim { padding: var(--space-lg) var(--space-md); } }
  `],
})
export class ClaimComponent implements OnInit, OnDestroy {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private narrativeService = inject(NarrativeService);
  private i18n = inject(I18nService);
  private format = inject(FormatService);

  narrative = signal('');
  currentStep = signal('claim_parsing');
  completedSteps = signal<string[]>([]);
  currentEvent = signal<PipelineEvent | null>(null);
  thinking = signal<{ agent: string; text: string } | null>(null);
  usage = signal<any>(null);
  connecting = signal(true);
  error = signal('');
  claimId = signal('');
  private sub?: Subscription;
  private thinkingMap = new Map<string, string>();
  private terminalEvent = false;

  ngOnInit() {
    this.sub = this.route.queryParams.subscribe(params => {
      this.narrative.set(params['narrative'] || '');
      if (this.narrative()) this.startPipeline();
    });
  }

  ngOnDestroy() { this.sub?.unsubscribe(); }

  startPipeline() {
    this.narrativeService.analyze(this.narrative()).subscribe({
      next: (event) => {
        this.connecting.set(false);
        if (event.event_type === 'agent_thinking') {
          this.appendThinking(event.data);
          return;
        }
        if (event.event_type === 'usage_update') {
          this.usage.set(event.data);
          return;
        }
        if (event.event_type === 'claim_parsing' || event.event_type === 'skeptic_analysis') {
          this.thinkingMap.clear();
          this.thinking.set(null);
        }
        if (event.event_type === 'pipeline_error') {
          this.terminalEvent = true;
          this.error.set(event.data?.error || this.i18n.t('claim.failed'));
          return;
        }
        if (event.event_type === 'pipeline_complete') {
          this.terminalEvent = true;
        }
        this.currentEvent.set(event);
        this.claimId.set(event.claim_id);
        if (!this.completedSteps().includes(event.event_type) && event.event_type !== 'pipeline_started') {
          this.completedSteps.update(steps => [...steps, event.event_type]);
        }
        this.currentStep.set(event.event_type);
        if (event.event_type === 'pipeline_complete') {
          setTimeout(() => this.router.navigate(['/results', this.claimId()]), 1000);
        }
      },
      error: (err) => {
        this.connecting.set(false);
        this.error.set(err.message || this.i18n.t('claim.failed'));
      },
      complete: () => {
        this.connecting.set(false);
        if (!this.terminalEvent) {
          this.error.set(this.i18n.t('claim.stream_ended'));
        }
      },
    });
  }

  appendThinking(data: any) {
    const agent = data?.agent || 'llm';
    const delta = data?.delta || '';
    const current = this.thinkingMap.get(agent) || '';
    const next = current + delta;
    this.thinkingMap.set(agent, next);
    this.thinking.set({ agent, text: next });
  }

  getEventTitle(): string {
    return this.i18n.tEventTitle(this.currentEvent()?.event_type || '');
  }

  formatEvent(event: PipelineEvent | null): string {
    return event ? JSON.stringify(event.data, null, 2) : '';
  }

  fmtNumber(value: number | null | undefined, decimals = 0): string {
    return this.format.number(value, decimals);
  }

  goBack() { this.router.navigate(['/dashboard']); }
}
