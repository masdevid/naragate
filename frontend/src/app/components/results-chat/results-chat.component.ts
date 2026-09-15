import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { I18nService } from '../../services/i18n.service';
import { SectionHelpComponent } from '../section-help/section-help.component';
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
  imports: [FormsModule, SectionHelpComponent, TPipe],
  template: `
    <div class="chat">
      <div class="chat__head">
        <span class="chat__badge">{{ 'chat.title' | t }}</span>
        <span class="chat__rule"></span>
      </div>
      <app-section-help helpKey="section_help.chat"/>
      <div class="chat__log">
        @for (msg of messages(); track $index) {
          <div class="chat__msg" [class.chat__msg--user]="msg.role === 'user'">
            <p class="chat__text">{{ msg.text }}</p>
          </div>
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
      <div class="chat__suggestions">
        @for (s of visibleSuggestions(); track s.id) {
          <button (click)="ask(s)" class="chat__suggestion">{{ suggestionLabel(s) }}</button>
        }
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; }
    .chat {
      margin-top: var(--space-2xl);
      padding: var(--space-lg);
      background: var(--color-paper-2);
      border: 1px solid var(--color-paper-3);
      border-left: 3px solid var(--color-accent);
      display: flex; flex-direction: column; gap: var(--space-md);
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
    .chat__rule { flex: 1; height: 1px; background: var(--color-paper-3); }
    .chat__log { display: flex; flex-direction: column; gap: var(--space-sm); max-height: 20rem; overflow-y: auto; }
    .chat__msg { max-width: 85%; padding: var(--space-sm) var(--space-md); border: 1px solid var(--color-rule); }
    .chat__msg--user { align-self: flex-end; border-color: var(--color-accent); }
    .chat__text { font-size: var(--text-sm); color: var(--color-ink); line-height: 1.5; }
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
    }
    .chat__suggestion:hover { color: var(--color-accent); border-color: var(--color-accent); }
  `],
})
export class ResultsChatComponent {
  @Input() messages: () => { role: string; text: string }[] = () => [];
  @Input() suggestions: () => FollowUpSuggestion[] = () => [];
  @Input() loading = false;
  @Output() sendQuestion = new EventEmitter<string>();
  @Output() suggestionClicked = new EventEmitter<FollowUpSuggestion>();

  question = '';

  private i18n = inject(I18nService);

  visibleSuggestions(): FollowUpSuggestion[] {
    const list = this.suggestions();
    if (list && list.length) return list;
    return this.i18n.language() === 'en' ? FALLBACK_EN : FALLBACK_ID;
  }

  suggestionLabel(s: FollowUpSuggestion): string {
    return this.i18n.language() === 'en' && s.text_en ? s.text_en : s.text;
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