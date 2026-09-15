import { Component, Input, OnChanges, OnDestroy, signal } from '@angular/core';

/* Hallmark · component: status-typing · genre: editorial · theme: token-native
 * states: typing · complete · reduced-motion · contrast: pass
 * pre-emit critique: P4 H4 E4 S4 R5 V4
 */

/**
 * Renders a string with a typewriter reveal and a blinking caret. Used for the
 * agent "thinking" line so it reads as live text rather than raw JSON.
 */
@Component({
  selector: 'app-typing-text',
  standalone: true,
  template: `
    <span class="typing">{{ shown() }}</span><span class="typing__caret" aria-hidden="true"></span>
  `,
  styles: [`
    :host {
      display: inline-flex;
      align-items: baseline;
    }
    .typing {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-muted);
      white-space: pre-wrap;
    }
    .typing__caret {
      display: inline-block;
      width: 0.55ch;
      height: 1em;
      margin-left: 1px;
      background: var(--color-accent);
      animation: typingBlink 1s steps(1, end) infinite;
    }
    @media (prefers-reduced-motion: reduce) {
      .typing__caret { animation: none; }
    }
    @keyframes typingBlink {
      0%, 50% { opacity: 1; }
      50.01%, 100% { opacity: 0; }
    }
  `],
})
export class TypingTextComponent implements OnChanges, OnDestroy {
  @Input() text = '';
  shown = signal('');

  private timer?: number;

  ngOnChanges(): void {
    const full = this.text ?? '';
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = undefined;
    }

    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
      this.shown.set(full);
      return;
    }

    this.shown.set('');
    let index = 0;
    this.timer = window.setInterval(() => {
      index += 1;
      this.shown.set(full.slice(0, index));
      if (index >= full.length) {
        clearInterval(this.timer);
        this.timer = undefined;
      }
    }, 24);
  }

  ngOnDestroy(): void {
    if (this.timer) clearInterval(this.timer);
  }
}
