import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { I18nService } from '../../services/i18n.service';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-dashboard-input',
  standalone: true,
  imports: [FormsModule, TPipe],
  template: `
    <section class="input-section reveal" style="--i: 4">
      <div class="input-section__inner">
        <textarea
          [(ngModel)]="narrative"
          class="input-section__field"
          [placeholder]="'dashboard.textarea_placeholder' | t"
          rows="4"></textarea>
        <button
          (click)="analyze.emit(narrative)"
          [disabled]="!narrative.trim() || analyzing"
          class="input-section__btn">
          {{ analyzing ? ('dashboard.analyzing' | t) : ('dashboard.analyze_btn' | t) }}
        </button>
        <button (click)="tryExample()" class="input-section__example">{{ 'dashboard.try_example' | t }}</button>
      </div>
      <div class="input-section__examples">
        <p class="input-section__examples-title">{{ 'dashboard.examples_title' | t }}</p>
        <div class="input-section__examples-grid">
          @for (ex of examples(); track $index) {
            <button class="input-section__example-card" (click)="useExample(ex.narrative)">
              <span class="input-section__example-tag">{{ ex.tag }}</span>
              <span class="input-section__example-text">{{ ex.narrative }}</span>
            </button>
          }
        </div>
      </div>
    </section>
  `,
  styles: [`
    :host { display: block; }
    .input-section {
      padding: 0 var(--space-lg) var(--space-3xl);
      max-width: 52rem;
      margin: 0 auto;
    }
    .input-section__field {
      width: 100%;
      background: var(--color-paper-2);
      border: none;
      border-top: 1px solid var(--color-rule);
      color: var(--color-ink);
      font-family: var(--font-body);
      font-size: var(--text-base);
      font-weight: 350;
      padding: var(--space-lg);
      resize: none;
      line-height: 1.55;
    }
    .input-section__field::placeholder {
      color: var(--color-dim);
    }
    .input-section__field:focus {
      outline: none;
      border-top-color: var(--color-accent);
    }
    .input-section__btn {
      display: inline-block;
      margin-top: var(--space-lg);
      padding: var(--space-md) var(--space-xl);
      background: var(--color-accent);
      color: var(--color-paper);
      border: none;
      font-family: var(--font-display);
      font-size: var(--text-md);
      text-transform: uppercase;
      letter-spacing: 0.02em;
      cursor: pointer;
      transition: opacity var(--dur-short) var(--ease-out);
    }
    .input-section__btn:hover { opacity: 0.9; }
    .input-section__btn:disabled { opacity: 0.3; cursor: not-allowed; }
    .input-section__example {
      display: inline-block;
      margin-top: var(--space-lg);
      margin-left: var(--space-md);
      background: none;
      border: 1px solid var(--color-rule);
      color: var(--color-muted);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: var(--space-md) var(--space-lg);
      cursor: pointer;
      transition: all var(--dur-short) var(--ease-out);
    }
    .input-section__example:hover {
      border-color: var(--color-accent);
      color: var(--color-accent);
    }
    .input-section__examples {
      margin-top: var(--space-xl);
      display: flex;
      flex-direction: column;
      gap: var(--space-sm);
    }
    .input-section__examples-title {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .input-section__examples-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr));
      gap: var(--space-sm);
    }
    .input-section__example-card {
      display: flex;
      flex-direction: column;
      gap: var(--space-2xs);
      text-align: left;
      background: none;
      border: 1px solid var(--color-paper-3);
      color: var(--color-ink);
      padding: var(--space-md);
      cursor: pointer;
      transition: border-color var(--dur-short) var(--ease-out);
    }
    .input-section__example-card:hover { border-color: var(--color-accent); }
    .input-section__example-tag {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-accent);
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .input-section__example-text {
      font-size: var(--text-sm);
      color: var(--color-muted);
      line-height: 1.5;
    }
    @media (max-width: 640px) {
      .input-section { padding-left: var(--space-md); padding-right: var(--space-md); }
    }
  `],
})
export class DashboardInputComponent {
  narrative = '';
  @Input() analyzing = false;

  @Output() analyze = new EventEmitter<string>();

  private i18n = inject(I18nService);

  examples(): { tag: string; narrative: string }[] {
    const lang = this.i18n.language();
    const tags = lang === 'en'
      ? ['Valuation', 'Fundamental', 'Market', 'News']
      : ['Valuasi', 'Fundamental', 'Pasar', 'Berita'];
    return [
      { tag: tags[0], narrative: this.i18n.t('dashboard.examples.valuation') },
      { tag: tags[1], narrative: this.i18n.t('dashboard.examples.fundamental') },
      { tag: tags[2], narrative: this.i18n.t('dashboard.examples.market') },
      { tag: tags[3], narrative: this.i18n.t('dashboard.examples.news') },
    ];
  }

  tryExample() {
    this.narrative = this.i18n.t('dashboard.example_narrative');
  }

  useExample(narrative: string) {
    this.narrative = narrative;
  }
}