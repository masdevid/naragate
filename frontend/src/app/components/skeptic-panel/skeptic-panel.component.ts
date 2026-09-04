import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-skeptic-panel',
  standalone: true,
  template: `
    <div class="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 class="text-lg font-semibold text-slate-200 mb-4">Skeptic Analysis</h3>
      <div class="space-y-3">
        @for (arg of counterArguments; track arg.point) {
          <div class="bg-slate-700/50 rounded p-3">
            <p class="text-slate-300 text-sm">{{ arg.point }}</p>
            <div class="mt-2 flex items-center gap-2">
              <span class="text-xs text-slate-500">Strength:</span>
              <div class="flex-1 bg-slate-600 rounded-full h-2">
                <div class="h-2 rounded-full" [style.width.%]="arg.strength"
                  [style.backgroundColor]="arg.strength > 70 ? '#ef4444' : arg.strength > 40 ? '#eab308' : '#22c55e'"></div>
              </div>
              <span class="text-xs text-slate-400">{{ arg.strength }}%</span>
            </div>
          </div>
        }
        @if (ambiguityPoints.length) {
          <div class="mt-4">
            <h4 class="text-sm font-medium text-slate-400 mb-2">Ambiguity Points</h4>
            @for (point of ambiguityPoints; track point) {
              <p class="text-sm text-slate-500 ml-2">• {{ point }}</p>
            }
          </div>
        }
        @if (missingEvidence.length) {
          <div class="mt-4">
            <h4 class="text-sm font-medium text-slate-400 mb-2">Missing Evidence</h4>
            @for (item of missingEvidence; track item) {
              <p class="text-sm text-slate-500 ml-2">• {{ item }}</p>
            }
          </div>
        }
      </div>
    </div>
  `,
})
export class SkepticPanelComponent {
  @Input() counterArguments: { point: string; evidence_ref: string; strength: number }[] = [];
  @Input() ambiguityPoints: string[] = [];
  @Input() missingEvidence: string[] = [];
}
