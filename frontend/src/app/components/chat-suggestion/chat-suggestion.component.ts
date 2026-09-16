import { Component, Input, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'app-chat-suggestion',
  standalone: true,
  template: `
    <button
      type="button"
      (click)="picked.emit()"
      class="chat__suggestion"
      [disabled]="disabled"
      [class.is-leaving]="leaving">{{ label }}</button>
  `,
  styles: [`
    :host { display: contents; }
    .chat__suggestion {
      background: none;
      border: 1px dashed var(--color-rule);
      color: var(--color-muted);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      padding: var(--space-2xs) var(--space-sm);
      cursor: pointer;
      transition: color var(--dur-short) var(--ease-out), border-color var(--dur-short) var(--ease-out);
      animation: chipIn var(--dur-short) var(--ease-out);
    }
    .chat__suggestion:hover:not(:disabled) { color: var(--color-accent); border-color: var(--color-accent); }
    .chat__suggestion:disabled { opacity: 0.4; cursor: default; }
    .chat__suggestion.is-leaving {
      animation: chipOut var(--dur-short) var(--ease-in) forwards;
    }
    @keyframes chipIn {
      from { opacity: 0; transform: translateY(4px); }
      to { opacity: 1; transform: none; }
    }
    @keyframes chipOut {
      to { opacity: 0; transform: translateY(-4px); }
    }
    @media (prefers-reduced-motion: reduce) {
      .chat__suggestion { animation: none; }
      .chat__suggestion.is-leaving { opacity: 0; }
    }
  `],
})
export class ChatSuggestionComponent {
  @Input() label = '';
  @Input() disabled = false;
  @Input() leaving = false;
  @Output() picked = new EventEmitter<void>();
}
