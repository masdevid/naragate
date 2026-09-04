import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-score-gauge',
  standalone: true,
  template: `
    <div class="relative w-32 h-32">
      <svg class="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="45" fill="none" stroke="#334155" stroke-width="8"/>
        <circle cx="50" cy="50" r="45" fill="none" [attr.stroke]="getColor()" stroke-width="8"
          [attr.stroke-dasharray]="getDashArray()" stroke-linecap="round"/>
      </svg>
      <div class="absolute inset-0 flex flex-col items-center justify-center">
        <span class="text-2xl font-bold" [style.color]="getColor()">{{ score }}</span>
        <span class="text-xs text-slate-400">/ 100</span>
      </div>
    </div>
  `,
})
export class ScoreGaugeComponent {
  @Input() score: number = 0;

  getColor(): string {
    if (this.score <= 30) return '#ef4444';
    if (this.score <= 60) return '#eab308';
    if (this.score <= 80) return '#22c55e';
    return '#166534';
  }

  getDashArray(): string {
    const circumference = 2 * Math.PI * 45;
    const filled = (this.score / 100) * circumference;
    return `${filled} ${circumference}`;
  }
}
