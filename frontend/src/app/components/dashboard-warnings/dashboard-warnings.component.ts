import { Component, Input, Output, EventEmitter } from '@angular/core';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-dashboard-warnings',
  standalone: true,
  imports: [TPipe],
  template: `
    @if (!setupComplete) {
      <div class="warn warn--yellow reveal" style="--i: 0">
        <div class="warn__inner">
          <span class="warn__icon">!</span>
          <span class="warn__text">{{ 'dashboard.warn_setup' | t }}</span>
          <button class="warn__btn" (click)="goSetup.emit()">{{ 'dashboard.start_setup' | t }}</button>
        </div>
      </div>
    }
    @if (!llmConfigured && showDetailWarnings) {
      <div class="warn reveal" style="--i: 0">
        <div class="warn__inner">
          <span class="warn__icon">!</span>
          <span class="warn__text">{{ 'dashboard.warn_llm' | t }}</span>
          <button class="warn__btn" (click)="goSettings.emit()">{{ 'dashboard.fix' | t }}</button>
          <button class="warn__dismiss" (click)="dismissLlm.emit()">&times;</button>
        </div>
      </div>
    }
    @if (!sectorsConfigured && showDetailWarnings) {
      <div class="warn warn--yellow reveal" style="--i: 0">
        <div class="warn__inner">
          <span class="warn__icon">!</span>
          <span class="warn__text">{{ 'dashboard.warn_sectors' | t }}</span>
          <button class="warn__btn" (click)="goSettings.emit()">{{ 'dashboard.fix' | t }}</button>
          <button class="warn__dismiss" (click)="dismissSectors.emit()">&times;</button>
        </div>
      </div>
    }
  `,
  styles: [`
    :host { display: block; }
    .warn {
      padding: var(--space-sm) var(--space-lg);
      background: oklch(22% 0.02 25);
      border-bottom: 1px solid oklch(40% 0.1 25);
    }
    .warn--yellow {
      background: oklch(22% 0.02 85);
      border-bottom-color: oklch(40% 0.1 85);
    }
    .warn__inner {
      max-width: 52rem;
      margin: 0 auto;
      display: flex;
      align-items: center;
      gap: var(--space-sm);
    }
    .warn__icon {
      font-family: var(--font-display);
      font-size: var(--text-md);
      color: var(--color-danger);
      flex-shrink: 0;
    }
    .warn--yellow .warn__icon { color: var(--color-warning); }
    .warn__text {
      font-size: var(--text-sm);
      color: var(--color-ink);
      flex: 1;
    }
    .warn__btn {
      background: none;
      border: 1px solid var(--color-ink);
      color: var(--color-ink);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: var(--space-2xs) var(--space-sm);
      cursor: pointer;
      transition: opacity var(--dur-short) var(--ease-out);
      flex-shrink: 0;
    }
    .warn__btn:hover { opacity: 0.7; }
    .warn__dismiss {
      background: none;
      border: none;
      color: var(--color-muted);
      font-size: var(--text-md);
      cursor: pointer;
      padding: 0 var(--space-xs);
      line-height: 1;
    }
    @media (max-width: 640px) {
      .warn__inner { flex-wrap: wrap; }
    }
  `],
})
export class DashboardWarningsComponent {
  @Input() setupComplete = true;
  /** When false, the LLM/Sectors warnings are suppressed: the single Setup banner already covers them. */
  @Input() showDetailWarnings = true;
  @Input() llmConfigured = true;
  @Input() sectorsConfigured = true;
  @Output() goSetup = new EventEmitter<void>();
  @Output() goSettings = new EventEmitter<void>();
  @Output() dismissLlm = new EventEmitter<void>();
  @Output() dismissSectors = new EventEmitter<void>();
}