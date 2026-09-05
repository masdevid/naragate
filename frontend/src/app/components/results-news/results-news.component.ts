import { Component, Input, inject } from '@angular/core';
import { EvidenceCardComponent } from '../evidence-card/evidence-card.component';
import { I18nService } from '../../services/i18n.service';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-results-news',
  standalone: true,
  imports: [EvidenceCardComponent, TPipe],
  template: `
    <div class="news">
      @if (news()) {
        <app-evidence-card [title]="'results.news_title' | t" [cacheHit]="news().cache_hit">
          <div class="news__body">
            <span class="news__badge" [class]="'news__badge--' + news().corroboration">
              {{ corroborationLabel(news().corroboration) }}
            </span>
            <p class="news__summary">{{ summary(news()) }}</p>
            @if (news().headlines?.length) {
              <ul class="news__list">
                @for (h of news().headlines.slice(0, 5); track $index) {
                  <li class="news__item">{{ h.title }}</li>
                }
              </ul>
            }
          </div>
        </app-evidence-card>
      }

      @if (corpActions()) {
        <app-evidence-card [title]="'results.corp_actions_title' | t" [cacheHit]="corpActions().cache_hit">
          <div class="news__body">
            <p class="news__summary">{{ summary(corpActions()) }}</p>
            @if (corpActions().relevant_events?.length) {
              <div class="news__tags">
                @for (ev of corpActions().relevant_events; track $index) {
                  <span class="news__tag">{{ ev }}</span>
                }
              </div>
            }
          </div>
        </app-evidence-card>
      }
    </div>
  `,
  styles: [`
    :host { display: block; }
    .news { display: flex; flex-direction: column; }
    .news__body { display: flex; flex-direction: column; gap: var(--space-sm); }
    .news__badge {
      align-self: flex-start;
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      padding: var(--space-3xs) var(--space-xs);
      border: 1px solid var(--color-rule);
    }
    .news__badge--supports { color: var(--color-success); border-color: var(--color-success); }
    .news__badge--contradicts { color: var(--color-danger); border-color: var(--color-danger); }
    .news__badge--neutral { color: var(--color-warning); border-color: var(--color-warning); }
    .news__badge--no_news { color: var(--color-dim); }
    .news__summary { font-size: var(--text-sm); color: var(--color-muted); line-height: 1.55; }
    .news__list {
      list-style: none;
      padding: 0;
      margin: 0;
      display: flex;
      flex-direction: column;
      gap: var(--space-2xs);
    }
    .news__item {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      padding-left: var(--space-sm);
      border-left: 1px solid var(--color-rule);
    }
    .news__tags { display: flex; flex-wrap: wrap; gap: var(--space-2xs); }
    .news__tag {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-accent);
      border: 1px solid var(--color-accent);
      padding: var(--space-3xs) var(--space-xs);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
  `],
})
export class ResultsNewsComponent {
  @Input() news: () => any = () => null;
  @Input() corpActions: () => any = () => null;

  private i18n = inject(I18nService);

  corroborationLabel(corroboration: string): string {
    return this.i18n.t(`news.corroboration.${corroboration}`);
  }

  summary(evidence: any): string {
    if (!evidence) return '';
    return this.i18n.language() === 'en' && evidence.summary_en ? evidence.summary_en : evidence.summary;
  }
}