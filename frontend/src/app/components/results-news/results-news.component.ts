import { Component, Input, inject } from '@angular/core';
import { EvidenceCardComponent } from '../evidence-card/evidence-card.component';
import { SectionHelpComponent } from '../section-help/section-help.component';
import { I18nService } from '../../services/i18n.service';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-results-news',
  standalone: true,
  imports: [EvidenceCardComponent, SectionHelpComponent, TPipe],
  template: `
    <div class="news">
      @if (news() || corpActions()) {
        <app-section-help helpKey="section_help.news"/>
      }
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
                  @if (headlineUrl(h)) {
                    <li class="news__item">
                      <a class="news__link" [href]="headlineUrl(h)" target="_blank" rel="noopener">{{ h.title }}</a>
                      <span class="news__source">{{ headlineSource(h) }}</span>
                    </li>
                  } @else {
                    <li class="news__item">{{ h.title }}</li>
                  }
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
      display: flex;
      flex-direction: column;
      gap: var(--space-2xs);
    }
    .news__link {
      color: var(--color-muted);
      line-height: 1.45;
      text-decoration: none;
      transition: color var(--dur-short) var(--ease-out);
    }
    .news__link:hover { color: var(--color-accent); }
    .news__source {
      font-size: var(--text-2xs);
      color: var(--color-accent);
      text-transform: lowercase;
      letter-spacing: 0.02em;
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

  headlineUrl(h: any): string {
    if (!h) return '';
    const u = h.url || h.link || '';
    if (u) return u;
    const s = h.source || '';
    return s.startsWith('http://') || s.startsWith('https://') || s.startsWith('www.') ? s : '';
  }

  headlineSource(h: any): string {
    const u = this.headlineUrl(h) || (h.source ?? '');
    if (!u) return '';
    try {
      const host = new URL(u.startsWith('http') ? u : 'https://' + u).hostname.replace(/^www\./, '');
      return host || u;
    } catch {
      return u;
    }
  }
}