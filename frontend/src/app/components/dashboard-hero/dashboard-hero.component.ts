import { Component, Input } from '@angular/core';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-dashboard-hero',
  standalone: true,
  imports: [TPipe],
  template: `
    <section class="hero">
      <div class="hero__inner">
        <p class="hero__eyebrow reveal" style="--i: 1">{{ 'dashboard.eyebrow' | t }}</p>
        <h1 class="hero__display reveal" style="--i: 2">
          @if (headlineParts().length > 1) {
            {{ headlineParts()[0] }}<em class="hero__accent"> {{ headlineParts()[1] }} </em>{{ headlineParts()[2] }}
          } @else {
            {{ 'dashboard.headline' | t }}
          }
        </h1>
        <p class="hero__sub reveal" style="--i: 3">
          {{ 'dashboard.sub' | t }}
        </p>
      </div>
    </section>
  `,
  styles: [`
    :host { display: block; }
    .hero {
      padding: var(--space-4xl) var(--space-lg) var(--space-xl);
      max-width: 52rem;
      margin: 0 auto;
    }
    .hero__eyebrow {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-accent);
      letter-spacing: 0.12em;
      text-transform: uppercase;
      margin-bottom: var(--space-lg);
    }
    .hero__display {
      font-size: var(--text-display);
      line-height: 1.02;
      color: var(--color-ink);
      max-width: 24ch;
    }
    .hero__accent {
      font-style: normal;
      color: var(--color-accent);
    }
    .hero__sub {
      font-size: var(--text-md);
      color: var(--color-muted);
      max-width: 42ch;
      margin-top: var(--space-lg);
      line-height: 1.55;
    }
    @media (max-width: 640px) {
      .hero { padding: var(--space-3xl) var(--space-md) var(--space-xl); }
      .hero__display { font-size: clamp(2rem, 8vw, 3.5rem); }
    }
  `],
})
export class DashboardHeroComponent {
  @Input() headlineParts: () => string[] = () => [];
}