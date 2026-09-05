import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { I18nService } from '../../services/i18n.service';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-results-chat',
  standalone: true,
  imports: [FormsModule, TPipe],
  template: `
    <div class="chat">
      <p class="chat__label">{{ 'chat.title' | t }}</p>
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
        @for (s of suggestions(); track $index) {
          <button (click)="ask(s)" class="chat__suggestion">{{ s }}</button>
        }
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; }
    .chat { border-top: 1px solid var(--color-rule); padding: var(--space-lg) 0; display: flex; flex-direction: column; gap: var(--space-md); }
    .chat__label {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
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
  @Input() loading = false;
  @Output() sendQuestion = new EventEmitter<string>();

  question = '';

  private i18n = inject(I18nService);

  suggestions(): string[] {
    const lang = this.i18n.language();
    return lang === 'en'
      ? ['Why is the score this high?', 'What would change this verdict?', 'Is the stock fairly valued?']
      : ['Kenapa skornya setinggi ini?', 'Apa yang bisa mengubah verdict ini?', 'Apakah sahamnya wajar?'];
  }

  send() {
    const q = this.question.trim();
    if (!q || this.loading) return;
    this.question = '';
    this.sendQuestion.emit(q);
  }

  ask(s: string) {
    this.question = s;
    this.send();
  }
}