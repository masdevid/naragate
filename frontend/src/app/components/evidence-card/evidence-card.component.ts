import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-evidence-card',
  standalone: true,
  template: `
    <div class="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <button (click)="expanded = !expanded" class="w-full flex items-center justify-between text-left">
        <h3 class="text-lg font-semibold text-slate-200">{{ title }}</h3>
        <span class="text-slate-400">{{ expanded ? '▲' : '▼' }}</span>
      </button>
      @if (expanded) {
        <div class="mt-4 space-y-2">
          <ng-content></ng-content>
        </div>
      }
    </div>
  `,
})
export class EvidenceCardComponent {
  @Input() title: string = '';
  @Input() cacheHit: boolean = false;
  expanded: boolean = true;
}
