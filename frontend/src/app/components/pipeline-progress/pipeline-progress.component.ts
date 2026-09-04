import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-pipeline-progress',
  standalone: true,
  template: `
    <div class="flex items-center gap-2 text-sm">
      @for (step of steps; track step.key) {
        <div class="flex items-center gap-2">
          <div class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold"
            [class]="getStepClass(step.key)">
            @if (currentStep === step.key) {
              <span class="animate-spin">⟳</span>
            } @else if (isCompleted(step.key)) {
              ✓
            } @else {
              {{ step.index }}
            }
          </div>
          <span class="text-slate-400 hidden sm:inline">{{ step.label }}</span>
          @if (step.index < steps.length) {
            <span class="text-slate-600">→</span>
          }
        </div>
      }
    </div>
  `,
})
export class PipelineProgressComponent {
  @Input() currentStep: string = '';
  @Input() completedSteps: string[] = [];

  steps = [
    { key: 'claim_parsing', label: 'Parsing', index: 1 },
    { key: 'evidence_fetching', label: 'Evidence', index: 2 },
    { key: 'skeptic_analysis', label: 'Skeptic', index: 3 },
    { key: 'judge_assessment', label: 'Judge', index: 4 },
    { key: 'score_computing', label: 'Scoring', index: 5 },
  ];

  isCompleted(stepKey: string): boolean {
    return this.completedSteps.includes(stepKey);
  }

  getStepClass(stepKey: string): string {
    if (this.currentStep === stepKey) return 'bg-blue-600 text-white';
    if (this.isCompleted(stepKey)) return 'bg-green-600 text-white';
    return 'bg-slate-700 text-slate-400';
  }
}
