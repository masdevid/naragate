import { Component, Input, Output, EventEmitter } from '@angular/core';
import { LlmProvider } from '../../services/llm-providers';
import { TPipe } from '../../pipes/t.pipe';

/**
 * Provider selector grid used by the LLM Connector. Emits the chosen provider id.
 */
@Component({
  selector: 'app-llm-provider-picker',
  standalone: true,
  imports: [TPipe],
  template: `
    <div class="conn__providers">
      @for (p of providers; track p.id) {
        <button class="conn__provider"
          [class.conn__provider--active]="selectedId === p.id"
          (click)="select.emit(p.id)">
          <span class="conn__provider-name">{{ p.labelKey | t }}</span>
          @if (p.default) {
            <span class="conn__provider-badge">{{ 'connector.default_badge' | t }}</span>
          }
        </button>
      }
    </div>
  `,
  styles: [`
    .conn__providers {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: var(--space-sm);
      margin-top: var(--space-sm);
    }
    .conn__provider {
      background: var(--color-paper-2);
      border: 1px solid var(--color-paper-3);
      color: var(--color-muted);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      padding: var(--space-md) var(--space-sm);
      cursor: pointer;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      transition: all var(--dur-short) var(--ease-out);
    }
    .conn__provider:hover { border-color: var(--color-dim); color: var(--color-ink); }
    .conn__provider--active {
      background: var(--color-accent);
      border-color: var(--color-accent);
      color: var(--color-paper);
    }
    @media (max-width: 640px) {
      .conn__providers { grid-template-columns: repeat(2, 1fr); }
    }
  `],
})
export class LlmProviderPickerComponent {
  @Input() providers: LlmProvider[] = [];
  @Input() selectedId = '';
  @Output() select = new EventEmitter<string>();
}