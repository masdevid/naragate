import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { I18nService } from '../../services/i18n.service';
import { TPipe } from '../../pipes/t.pipe';

export interface FollowUpSuggestion {
  id: string;
  text: string;
  text_en: string;
}

const FALLBACK_EN: FollowUpSuggestion[] = [
  { id: 'd1', text: 'Why is the score this high?', text_en: 'Why is the score this high?' },
  { id: 'd2', text: 'What would change this verdict?', text_en: 'What would change this verdict?' },
  { id: 'd3', text: 'Is the stock fairly valued?', text_en: 'Is the stock fairly valued?' },
];

const FALLBACK_ID: FollowUpSuggestion[] = [
  { id: 'd1', text: 'Kenapa skornya setinggi ini?', text_en: 'Why is the score this high?' },
  { id: 'd2', text: 'Apa yang bisa mengubah verdict ini?', text_en: 'What would change this verdict?' },
  { id: 'd3', text: 'Apakah sahamnya wajar?', text_en: 'Is the stock fairly valued?' },
];

@Component({
  selector: 'app-results-chat',
  standalone: true,
  imports: [FormsModule, TPipe],
  template: `
    @if (!open) {
      <button (click)="toggle()" class="chat__fab" [attr.aria-expanded]="open">
        <span class="chat__fab-label">{{ 'chat.open' | t }}</span>
      </button>
    }

    @if (open) {
      <div class="chat__scrim" (click)="close()"></div>
      <aside class="chat__panel">
        <div class="chat__head">
          <span class="chat__badge">{{ 'chat.title' | t }}</span>
          <span class="chat__rule"></span>
          <button (click)="close()" class="chat__close" [attr.aria-label]="'chat.close' | t">&times;</button>
        </div>
        <div class="chat__log">
          @for (msg of messages(); track $index) {
            <div class="chat__msg" [class.chat__msg--user]="msg.role === 'user'">
              <p class="chat__text">{{ msg.text }}</p>
            </div>
          }
          @if (loading) {
            <div class="chat__msg chat__msg--thinking">
              <span class="chat__dots" aria-hidden="true"><i></i><i></i><i></i></span>
              <span class="chat__thinking-text">{{ 'chat.thinking' | t }}</span>
            </div>
          }
        </div>
        <div class="chat__suggestions">
          @for (s of visibleSuggestions(); track s.id) {
            <button
              (click)="ask(s)"
              class="chat__suggestion"
              [class.is-leaving]="removingId === s.id">{{ suggestionLabel(s) }}</button>
          }
        </div>
        <div class="chat__input">
          <input
            [(ngModel)]="question"
            (keyup.enter)="send()"
            [placeholder]="'chat.placeholder' | t"
            class="chat__field"
            [disabled]="loading"/>
          <button (click)="send()" [disabled]="!question.trim() || loading" class="chat__btn">
            {{ loading ? ('chat.sending' | t) : ('chat.send' | t) }}
          </button>
        </div>
      </aside>
    }
  `,
  styles: [`
    :host { display: block; }
    .chat__fab {
      position: fixed;
      right: var(--space-lg);
      bottom: var(--space-lg);
      z-index: 50;
      background: var(--color-ink);
      color: var(--color-paper);
      border: 1px solid var(--color-ink);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      padding: var(--space-sm) var(--space-md);
      cursor: pointer;
      transition: opacity var(--dur-short) var(--ease-out), transform var(--dur-short) var(--ease-out);
    }
    .chat__fab:hover { opacity: 0.7; }
    .chat__scrim {
      position: fixed;
      inset: 0;
      z-index: 40;
      background: rgba(0, 0, 0, 0.35);
    }
    .chat__panel {
      position: fixed;
      top: 0;
      right: 0;
      bottom: 0;
      z-index: 45;
      width: min(24rem, 100vw);
      background: var(--color-paper);
      border-left: 1px solid var(--color-rule);
      display: flex;
      flex-direction: column;
      gap: var(--space-md);
      padding: var(--space-lg);
      box-shadow: -12px 0 32px rgba(0, 0, 0, 0.18);
      animation: chat-in var(--dur-short) var(--ease-out);
    }
    @keyframes chat-in {
      from { transform: translateX(100%); }
      to { transform: translateX(0); }
    }
    .chat__head { display: flex; align-items: center; gap: var(--space-sm); }
    .chat__badge {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      font-weight: 600;
      color: var(--color-accent);
      text-transform: uppercase;
      letter-spacing: 0.12em;
      border: 1px solid var(--color-accent);
      padding: var(--space-3xs) var(--space-sm);
    }
    .chat__rule { flex: 1; height: 1px; background: var(--color-rule); }
    .chat__close {
      background: none;
      border: none;
      color: var(--color-muted);
      font-size: var(--text-lg);
      line-height: 1;
      cursor: pointer;
      padding: 0 var(--space-2xs);
      transition: color var(--dur-short) var(--ease-out);
    }
    .chat__close:hover { color: var(--color-ink); }
    .chat__log {
      flex: 1;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: var(--space-sm);
      min-height: 0;
    }
    .chat__msg {
      max-width: 85%;
      padding: var(--space-sm) var(--space-md);
      border: 1px solid var(--color-rule);
      align-self: flex-start;
    }
    .chat__msg--user { align-self: flex-end; border-color: var(--color-accent); }
    .chat__text { font-size: var(--text-sm); color: var(--color-ink); line-height: 1.5; }
    .chat__msg--thinking {
      display: flex;
      align-items: center;
      gap: var(--space-sm);
      border-style: dashed;
      color: var(--color-muted);
    }
    .chat__dots { display: inline-flex; gap: 0.25rem; }
    .chat__dots i {
      width: 0.35rem;
      height: 0.35rem;
      border-radius: 50%;
      background: var(--color-muted);
      animation: chat-blink 1.2s infinite ease-in-out;
    }
    .chat__dots i:nth-child(2) { animation-delay: 0.2s; }
    .chat__dots i:nth-child(3) { animation-delay: 0.4s; }
    @keyframes chat-blink {
      0%, 60%, 100% { opacity: 0.25; }
      30% { opacity: 1; }
    }
    .chat__thinking-text {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .chat__suggestions { display: flex; flex-wrap: wrap; gap: var(--space-2xs); }
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
    .chat__suggestion:hover { color: var(--color-accent); border-color: var(--color-accent); }
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
    .chat__input { display: flex; gap: var(--space-sm); }
    .chat__field {
      flex: 1;
      background: none;
      border: 1px solid var(--color-rule);
      color: var(--color-ink);
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      padding: var(--space-sm) var(--space-md);
    }
    .chat__field:focus { outline: none; border-color: var(--color-accent); }
    .chat__btn {
      background: none;
      border: 1px solid var(--color-ink);
      color: var(--color-ink);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: var(--space-sm) var(--space-md);
      cursor: pointer;
      transition: opacity var(--dur-short) var(--ease-out);
    }
    .chat__btn:disabled { opacity: 0.35; cursor: default; }
    .chat__btn:hover:not(:disabled) { opacity: 0.7; }
  `],
})
export class ResultsChatComponent {
  @Input() messages: () => { role: string; text: string }[] = () => [];
  @Input() suggestions: () => FollowUpSuggestion[] = () => [];
  @Input() loading = false;
  @Input() removingId = '';
  @Input() loaded = false;
  @Output() sendQuestion = new EventEmitter<string>();
  @Output() suggestionClicked = new EventEmitter<FollowUpSuggestion>();
  @Output() opened = new EventEmitter<void>();

  question = '';
  open = false;

  private i18n = inject(I18nService);

  visibleSuggestions(): FollowUpSuggestion[] {
    if (this.loaded) return this.suggestions() || [];
    const list = this.suggestions();
    if (list && list.length) return list;
    return this.i18n.language() === 'en' ? FALLBACK_EN : FALLBACK_ID;
  }

  suggestionLabel(s: FollowUpSuggestion): string {
    return this.i18n.language() === 'en' && s.text_en ? s.text_en : s.text;
  }

  toggle() {
    if (this.open) {
      this.close();
    } else {
      this.open = true;
      this.opened.emit();
    }
  }

  close() {
    this.open = false;
  }

  send() {
    const q = this.question.trim();
    if (!q || this.loading) return;
    this.question = '';
    this.sendQuestion.emit(q);
  }

  ask(s: FollowUpSuggestion) {
    this.suggestionClicked.emit(s);
  }
}