import { Component, HostListener, OnInit, signal } from '@angular/core';
import { TPipe } from '../../pipes/t.pipe';

/* Hallmark · component: scroll-to-top · genre: editorial · theme: token-native
 * states: hidden · shown · hover · focus · active · reduced-motion · contrast: pass
 * pre-emit critique: P4 H4 E5 S4 R5 V4
 */

/**
 * Floating "back to top" control. Appears only when the page is long enough to
 * scroll and the user has moved past the fold, then hides again at the top.
 */
@Component({
  selector: 'app-scroll-top',
  standalone: true,
  imports: [TPipe],
  template: `
    @if (visible()) {
      <button
        type="button"
        class="to-top"
        (click)="toTop()"
        [attr.aria-label]="'common.scroll_top' | t"
        [title]="'common.scroll_top' | t">
        <span aria-hidden="true">&#8593;</span>
      </button>
    }
  `,
  styles: [`
    .to-top {
      position: fixed;
      left: var(--space-lg);
      bottom: var(--space-lg);
      z-index: 50;
      width: 2.5rem;
      height: 2.5rem;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: var(--color-paper-2);
      color: var(--color-ink);
      border: 1px solid var(--color-rule);
      border-radius: 999px;
      font-size: var(--text-md);
      line-height: 1;
      cursor: pointer;
      animation: toTopIn var(--dur-short) var(--ease-out);
      transition: background var(--dur-short) var(--ease-out), border-color var(--dur-short) var(--ease-out), color var(--dur-short) var(--ease-out);
    }
    .to-top:hover {
      background: var(--color-accent);
      border-color: var(--color-accent);
      color: var(--color-paper);
    }
    .to-top:focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px; }
    .to-top:active { transform: translateY(1px); }
    @keyframes toTopIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: none; }
    }
    @media (prefers-reduced-motion: reduce) { .to-top { animation: none; } }
  `],
})
export class ScrollTopComponent implements OnInit {
  visible = signal(false);

  ngOnInit(): void {
    this.update();
  }

  @HostListener('window:scroll')
  onScroll(): void {
    this.update();
  }

  @HostListener('window:resize')
  onResize(): void {
    this.update();
  }

  private update(): void {
    const doc = document.documentElement;
    const pageIsLong = doc.scrollHeight > window.innerHeight * 1.25;
    this.visible.set(pageIsLong && window.scrollY > 320);
  }

  toTop(): void {
    const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    window.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' });
  }
}
