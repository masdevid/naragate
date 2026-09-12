import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

export type NaraWordmarkSize = 'sm' | 'md' | 'lg' | 'xl';

const SIZE_CLASSES: Record<NaraWordmarkSize, string> = {
  sm: 'text-lg',
  md: 'text-xl',
  lg: 'text-3xl',
  xl: 'text-5xl',
};

/**
 * The Naragate wordmark — "NARA" in the brand gradient, "GATE" in solid white.
 *
 * This is the one canonical place the gradient classes live. Drop it in the header,
 * the footer, a loading screen, wherever the brand mark shows up — nobody has to
 * remember or re-type the from/to hex values again.
 *
 * Purely presentational: no router dependency, no state. If you want it to double as
 * a home link, wrap it yourself — `<a routerLink="/"><app-nara-wordmark /></a>` — so
 * this component stays reusable in non-routed contexts too (emails, marketing pages).
 *
 * @example
 * <app-nara-wordmark size="lg" />
 */
@Component({
  selector: 'app-nara-wordmark',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span [class]="'inline-flex [font-family:var(--font-display)] select-none ' + sizeClass()">
      <span class="bg-gradient-to-r from-[#E31C5F] to-[#F5A623] bg-clip-text text-transparent"
        >NARA</span
      ><span class="text-white">GATE</span>
    </span>
  `,
})
export class NaraWordmarkComponent {
  /** Text size — maps to a Tailwind text-size class. Defaults to 'md'. */
  readonly size = input<NaraWordmarkSize>('md');

  protected readonly sizeClass = computed(() => SIZE_CLASSES[this.size()]);
}