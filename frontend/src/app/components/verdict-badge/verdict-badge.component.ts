import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-verdict-badge',
  standalone: true,
  template: `
    <span class="px-3 py-1 rounded-full text-sm font-semibold" [style.backgroundColor]="getBgColor()" [style.color]="getTextColor()">
      {{ getLabel() }}
    </span>
  `,
})
export class VerdictBadgeComponent {
  @Input() verdict: string = '';

  getLabel(): string {
    return this.verdict.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }

  getBgColor(): string {
    switch (this.verdict) {
      case 'contradicted': return '#7f1d1d';
      case 'mixed': return '#713f12';
      case 'supported': return '#14532d';
      case 'strongly_supported': return '#052e16';
      default: return '#334155';
    }
  }

  getTextColor(): string {
    switch (this.verdict) {
      case 'contradicted': return '#fca5a5';
      case 'mixed': return '#fde047';
      case 'supported': return '#86efac';
      case 'strongly_supported': return '#bbf7d0';
      default: return '#94a3b8';
    }
  }
}
