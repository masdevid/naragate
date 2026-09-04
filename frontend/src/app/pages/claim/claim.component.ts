import { Component, OnInit, OnDestroy, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { NarrativeService } from '../../services/narrative.service';
import { I18nService } from '../../services/i18n.service';
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

  narrative = signal('');
  currentStep = signal('');
  completedSteps = signal<string[]>([]);
  currentEvent = signal<PipelineEvent | null>(null);
  error = signal('');
  claimId = signal('');
  private sub?: Subscription;

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
      error: (err) => { this.error.set(err.message || this.i18n.t('claim.failed')); },
    });
  }

  getEventTitle(): string {
    return this.i18n.tEventTitle(this.currentEvent()?.event_type || '');
  }

  formatEvent(event: PipelineEvent | null): string {
    return event ? JSON.stringify(event.data, null, 2) : '';
  }

  goBack() { this.router.navigate(['/dashboard']); }
}
