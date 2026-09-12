import { Component, Input, inject } from '@angular/core';
import { I18nService } from '../../services/i18n.service';
import { SectionHelpComponent } from '../section-help/section-help.component';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-results-radar',
  standalone: true,
  imports: [SectionHelpComponent, TPipe],
  template: `
    <div class="radar">
      <h3 class="radar__title">{{ 'radar.title' | t }}</h3>
      <app-section-help helpKey="section_help.radar"/>
      <svg class="radar__svg" [attr.viewBox]="viewBox" role="img"
        [attr.aria-label]="'radar.title' | t">
        @for (ring of rings; track ring) {
          <polygon
            class="radar__ring"
            [attr.points]="ringPoints(ring)"
            fill="none"/>
        }
        @for (axis of axes(); track axis.label) {
          <line
            class="radar__axis"
            [attr.x1]="center.x"
            [attr.y1]="center.y"
            [attr.x2]="axis.x"
            [attr.y2]="axis.y"/>
        }
        <polygon
          class="radar__shape"
          [attr.points]="shapePoints()"
          fill="var(--color-accent)"
          fill-opacity="0.18"
          stroke="var(--color-accent)"
          stroke-width="2"/>
        @for (point of shapePointsList(); track point.label) {
          <circle
            class="radar__dot"
            [attr.cx]="point.x"
            [attr.cy]="point.y"
            r="3"/>
        }
        @for (axis of axes(); track axis.label) {
          <text
            class="radar__label"
            [attr.x]="axis.labelX"
            [attr.y]="axis.labelY"
            text-anchor="middle">{{ axis.label }}</text>
        }
      </svg>
      <ul class="radar__legend">
        @for (axis of axes(); track axis.label) {
          <li class="radar__legend-item">
            <span class="radar__legend-swatch"></span>
            <span class="radar__legend-label">{{ axis.label }}</span>
            <span class="radar__legend-value">{{ axis.value }}</span>
          </li>
        }
      </ul>
    </div>
  `,
  styles: [`
    :host { display: block; }
    .radar {
      border-top: 1px solid var(--color-rule);
      padding: var(--space-xl) 0;
    }
    .radar__title {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: var(--space-lg);
    }
    .radar__svg {
      width: 100%;
      max-width: 22rem;
      height: auto;
      display: block;
      margin: 0 auto;
    }
    .radar__ring {
      stroke: var(--color-paper-3);
      stroke-width: 1;
    }
    .radar__axis {
      stroke: var(--color-paper-3);
      stroke-width: 1;
    }
    .radar__dot {
      fill: var(--color-accent);
    }
    .radar__label {
      font-family: var(--font-mono);
      font-size: 10px;
      fill: var(--color-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .radar__legend {
      list-style: none;
      margin: var(--space-lg) auto 0;
      padding: 0;
      max-width: 22rem;
      display: flex;
      flex-direction: column;
      gap: var(--space-2xs);
    }
    .radar__legend-item {
      display: flex;
      align-items: center;
      gap: var(--space-sm);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .radar__legend-swatch {
      width: 0.5rem;
      height: 0.5rem;
      background: var(--color-accent);
      flex-shrink: 0;
    }
    .radar__legend-label { flex: 1; }
    .radar__legend-value { color: var(--color-ink); }
  `],
})
export class ResultsRadarComponent {
  @Input() dimensions: () => Record<string, number> = () => ({});

  private i18n = inject(I18nService);

  readonly size = 260;
  readonly center = { x: 130, y: 130 };
  readonly radius = 90;
  readonly rings = [25, 50, 75, 100];

  get viewBox(): string {
    return `0 0 ${this.size} ${this.size}`;
  }

  axes() {
    const dims = this.dimensions();
    const entries = Object.entries(dims).filter(([, v]) => typeof v === 'number');
    if (!entries.length) return [];
    const n = entries.length;
    return entries.map(([key, value], i) => {
      const angle = this.angleFor(i, n);
      const x = this.center.x + this.radius * Math.cos(angle);
      const y = this.center.y + this.radius * Math.sin(angle);
      const labelX = this.center.x + (this.radius + 22) * Math.cos(angle);
      const labelY = this.center.y + (this.radius + 22) * Math.sin(angle);
      return {
        key,
        value: Math.round(value),
        x,
        y,
        labelX,
        labelY,
        label: this.dimensionLabel(key),
      };
    });
  }

  ringPoints(score: number): string {
    const axes = this.axes();
    if (!axes.length) return '';
    return axes
      .map((a, i) => {
        const angle = this.angleFor(i, axes.length);
        const r = this.radius * (score / 100);
        return `${this.center.x + r * Math.cos(angle)},${this.center.y + r * Math.sin(angle)}`;
      })
      .join(' ');
  }

  shapePoints(): string {
    const axes = this.axes();
    if (!axes.length) return '';
    return axes
      .map((a, i) => {
        const angle = this.angleFor(i, axes.length);
        const r = this.radius * (a.value / 100);
        return `${this.center.x + r * Math.cos(angle)},${this.center.y + r * Math.sin(angle)}`;
      })
      .join(' ');
  }

  shapePointsList() {
    const axes = this.axes();
    return axes.map((a, i) => {
      const angle = this.angleFor(i, axes.length);
      const r = this.radius * (a.value / 100);
      return { label: a.label, x: this.center.x + r * Math.cos(angle), y: this.center.y + r * Math.sin(angle) };
    });
  }

  private angleFor(index: number, count: number): number {
    return -Math.PI / 2 + (index * 2 * Math.PI) / count;
  }

  private dimensionLabel(key: string): string {
    const translated = this.i18n.t(`dimension.${key}`);
    if (translated !== `dimension.${key}`) return translated;
    return key.replace(/_/g, ' ');
  }
}