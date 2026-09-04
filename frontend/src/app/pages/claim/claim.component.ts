import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { NarrativeService } from '../../services/narrative.service';
import { PipelineEvent } from '../../models/pipeline.model';
import { PipelineProgressComponent } from '../../components/pipeline-progress/pipeline-progress.component';

@Component({
  selector: 'app-claim',
  standalone: true,
  imports: [PipelineProgressComponent],
  template: `
    <div class="min-h-screen bg-slate-900 p-8">
      <div class="max-w-4xl mx-auto">
        <button (click)="goBack()" class="text-slate-400 hover:text-white mb-4">← Back</button>
        <h1 class="text-3xl font-bold text-white mb-6">Analyzing Narrative</h1>

        <div class="bg-slate-800 rounded-lg p-6 border border-slate-700 mb-6">
          <p class="text-slate-300 italic">"{{ narrative }}"</p>
        </div>

        <div class="mb-6">
          <app-pipeline-progress [currentStep]="currentStep" [completedSteps]="completedSteps"/>
        </div>

        @if (currentEvent) {
          <div class="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <h2 class="text-lg font-semibold text-white mb-2">{{ getEventTitle() }}</h2>
            <pre class="text-slate-400 text-sm overflow-auto">{{ formatEvent(currentEvent) }}</pre>
          </div>
        }

        @if (error) {
          <div class="bg-red-900/50 rounded-lg p-4 border border-red-700">
            <p class="text-red-300">{{ error }}</p>
          </div>
        }
      </div>
    </div>
  `,
})
export class ClaimComponent implements OnInit, OnDestroy {
  narrative = '';
  currentStep = '';
  completedSteps: string[] = [];
  currentEvent: PipelineEvent | null = null;
  error = '';
  claimId = '';

  private sub?: Subscription;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private narrativeService: NarrativeService,
  ) {}

  ngOnInit() {
    this.sub = this.route.queryParams.subscribe(params => {
      this.narrative = params['narrative'] || '';
      if (this.narrative) {
        this.startPipeline();
      }
    });
  }

  ngOnDestroy() {
    this.sub?.unsubscribe();
  }

  startPipeline() {
    this.narrativeService.analyze(this.narrative).subscribe({
      next: (event) => {
        this.currentEvent = event;
        this.claimId = event.claim_id;

        if (!this.completedSteps.includes(event.event_type) && event.event_type !== 'pipeline_started') {
          this.completedSteps.push(event.event_type);
        }
        this.currentStep = event.event_type;

        if (event.event_type === 'pipeline_complete') {
          setTimeout(() => {
            this.router.navigate(['/results', this.claimId]);
          }, 1000);
        }
      },
      error: (err) => {
        this.error = err.message || 'Pipeline failed';
      },
    });
  }

  getEventTitle(): string {
    const titles: Record<string, string> = {
      pipeline_started: 'Pipeline Started',
      claim_parsing: 'Parsing Claim...',
      claim_parsed: 'Claim Extracted',
      evidence_fetching: 'Fetching Evidence...',
      evidence_ready: 'Evidence Retrieved',
      skeptic_analysis: 'Running Skeptic...',
      skeptic_ready: 'Skeptic Analysis Complete',
      judge_assessment: 'Judging Evidence...',
      assessment_ready: 'Assessment Complete',
      score_computing: 'Computing Score...',
      score_computed: 'Score Computed',
      pipeline_complete: 'Pipeline Complete',
    };
    return titles[this.currentEvent?.event_type || ''] || 'Processing...';
  }

  formatEvent(event: PipelineEvent): string {
    return JSON.stringify(event.data, null, 2);
  }

  goBack() {
    this.router.navigate(['/dashboard']);
  }
}
