import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { NarrativeService } from '../../services/narrative.service';
import { I18nService } from '../../services/i18n.service';
import { FormatService } from '../../services/format.service';
import { SkepticPanelComponent } from '../../components/skeptic-panel/skeptic-panel.component';
import { ResultsVerdictComponent } from '../../components/results-verdict/results-verdict.component';
import { ResultsEvidenceComponent } from '../../components/results-evidence/results-evidence.component';
import { ResultsNewsComponent } from '../../components/results-news/results-news.component';
import { ResultsFilingsComponent } from '../../components/results-filings/results-filings.component';
import { ResultsChatComponent, FollowUpSuggestion } from '../../components/results-chat/results-chat.component';
import { ResultsPolicyComponent } from '../../components/results-policy/results-policy.component';
import { ResultsRadarComponent } from '../../components/results-radar/results-radar.component';
import { TPipe } from '../../pipes/t.pipe';
import { buildVerdictNarrative } from '../../utils/verdict-narrative';

@Component({
  selector: 'app-results',
  standalone: true,
  imports: [
    SkepticPanelComponent,
    ResultsVerdictComponent,
    ResultsEvidenceComponent,
    ResultsNewsComponent,
    ResultsFilingsComponent,
    ResultsChatComponent,
    ResultsPolicyComponent,
    ResultsRadarComponent,
    TPipe,
  ],
  template: `
    <div class="results">
      <div class="results__inner">
        <button (click)="goBack()" class="results__back">&larr; {{ 'results.back' | t }}</button>

        @if (loading()) {
          <div class="results__loading">
            <p>{{ 'results.loading' | t }}</p>
          </div>
        } @else if (error()) {
          <div class="results__error">
            <p>{{ error() }}</p>
          </div>
        } @else if (claimData()) {
          @if (claimData().status === 'failed') {
            <div class="results__status results__status--failed">
              <p class="results__status-title">{{ 'results.failed_title' | t }}</p>
              <p class="results__status-text">{{ claimData().error || 'results.failed_message' | t }}</p>
              <button (click)="retry()" class="results__status-btn">{{ 'results.retry' | t }}</button>
            </div>
          } @else if (claimData().status !== 'completed') {
            <div class="results__status">
              <p class="results__status-title">{{ 'results.pending_title' | t }}</p>
              <p class="results__status-text">{{ 'results.pending_message' | t }}</p>
              <button (click)="retry()" class="results__status-btn">{{ 'results.retry' | t }}</button>
            </div>
          }

          <div class="results__narrative">
            <p class="results__label">{{ 'results.narrative_label' | t }}</p>
            <p class="results__quote">&ldquo;{{ claimData().narrative }}&rdquo;</p>
          </div>

          @if (claimData().claim) {
            <div class="results__claim">
              <p class="results__label">{{ 'results.claim_label' | t }}</p>
              <p class="results__assertion">{{ assertion() }}</p>
              <div class="results__meta">
                <span class="results__meta-item">
                  <span class="results__meta-key">{{ 'results.ticker' | t }}</span>
                  <a class="results__meta-value" [href]="sectorsUrl(claimData().claim.ticker)" target="_blank" rel="noopener">{{ claimData().claim.ticker }}</a>
                </span>
                <span class="results__meta-item">
                  <span class="results__meta-key">{{ 'results.category' | t }}</span>
                  <span class="results__meta-value">{{ claimData().claim.category }}</span>
                </span>
                <span class="results__meta-item">
                  <span class="results__meta-key">{{ 'results.direction' | t }}</span>
                  <span class="results__meta-value">
                    <span class="results__direction-icon">{{ directionIcon(claimData().claim.direction) }}</span>
                    {{ directionLabel(claimData().claim.direction) }}
                  </span>
                </span>
              </div>
            </div>
          }

          @if (claimData().score) {
            <app-results-verdict
              [score]="scoreValue"
              [verdict]="verdictValue"
              [explanation]="explanation"
              [narrative]="narrative"/>
            <app-results-radar [dimensions]="dimensions"/>
          }

          @if (claimData().status === 'completed' && claimData().claim?.is_policy) {
            <app-results-policy [sector]="policySector"/>
          }

          @if (claimData().evidence) {
            <app-results-evidence
              [valuation]="valuation"
              [fundamental]="fundamental"
              [market]="market"/>
            <app-results-news
              [news]="news"
              [corpActions]="corpActions"/>
            <app-results-filings
              [filings]="filings"/>
          }

          @if (claimData().skeptic) {
            <app-skeptic-panel
              [counterArguments]="claimData().skeptic.counter_arguments"
              [ambiguityPoints]="claimData().skeptic.ambiguity_points"
              [ambiguityPointsEn]="claimData().skeptic.ambiguity_points_en"
              [missingEvidence]="claimData().skeptic.missing_evidence"
              [missingEvidenceEn]="claimData().skeptic.missing_evidence_en"/>
          }

          @if (claimData().status === 'completed') {
            <app-results-chat
              [messages]="chatMessages"
              [suggestions]="followupSuggestions"
              [removingId]="removingId()"
              [loaded]="suggestionsLoaded()"
              [loading]="chatLoading()"
              (opened)="onChatOpened()"
              (sendQuestion)="sendChat($event)"
              (suggestionClicked)="onSuggestionClick($event)"/>
          }
        }
      </div>
    </div>
  `,
  styles: [`
    .results { padding: var(--space-2xl) var(--space-lg); }
    .results__inner { max-width: 48rem; margin: 0 auto; }
    .results__back {
      background: none;
      border: none;
      color: var(--color-muted);
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      cursor: pointer;
      padding: 0;
      margin-bottom: var(--space-xl);
      transition: color var(--dur-short) var(--ease-out);
    }
    .results__back:hover { color: var(--color-ink); }
    .results__loading, .results__error {
      padding: var(--space-4xl) 0;
      text-align: center;
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      color: var(--color-muted);
    }
    .results__error { color: var(--color-danger); }
    .results__status {
      border: 1px solid var(--color-warning);
      padding: var(--space-lg);
      margin-bottom: var(--space-lg);
      display: flex;
      flex-direction: column;
      gap: var(--space-sm);
    }
    .results__status--failed { border-color: var(--color-danger); }
    .results__status-title {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--color-warning);
    }
    .results__status--failed .results__status-title { color: var(--color-danger); }
    .results__status-text { font-size: var(--text-sm); color: var(--color-muted); line-height: 1.55; }
    .results__status-btn {
      align-self: flex-start;
      background: none;
      border: 1px solid var(--color-ink);
      color: var(--color-ink);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: var(--space-2xs) var(--space-sm);
      cursor: pointer;
      transition: opacity var(--dur-short) var(--ease-out);
    }
    .results__status-btn:hover { opacity: 0.7; }
    .results__narrative { border-top: 1px solid var(--color-rule); padding: var(--space-lg) 0; }
    .results__label {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: var(--space-sm);
    }
    .results__quote {
      font-size: var(--text-md);
      color: var(--color-muted);
      line-height: 1.55;
      font-style: italic;
    }
    .results__claim { border-top: 1px solid var(--color-rule); padding: var(--space-lg) 0; }
    .results__assertion { font-size: var(--text-xl); color: var(--color-ink); margin-bottom: var(--space-md); }
    .results__meta { display: flex; flex-wrap: wrap; gap: var(--space-lg); }
    .results__meta-item { display: flex; flex-direction: column; gap: var(--space-3xs); }
    .results__meta-key {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .results__meta-value {
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      color: var(--color-ink);
      text-transform: uppercase;
      text-decoration: none;
      transition: color var(--dur-short) var(--ease-out);
    }
    .results__meta-value:hover {
      color: var(--color-accent);
      text-decoration: underline;
    }
    .results__direction-icon { margin-right: var(--space-2xs); color: var(--color-accent); }
    @media (max-width: 640px) {
      .results { padding: var(--space-lg) var(--space-md); }
    }
  `],
})
export class ResultsComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private narrativeService = inject(NarrativeService);
  private i18n = inject(I18nService);
  private format = inject(FormatService);

  claimId = '';
  claimData = signal<any>(null);
  loading = signal(true);
  error = signal('');

  chatMessages = signal<{ role: string; text: string }[]>([]);
  chatLoading = signal(false);
  followupSuggestions = signal<FollowUpSuggestion[]>([]);
  removingId = signal('');
  suggestionsLoaded = signal(false);
  suggestionsRequested = false;

  ngOnInit() {
    this.claimId = this.route.snapshot.paramMap.get('id') || '';
    if (this.claimId) {
      this.loadClaim();
    } else {
      this.loading.set(false);
      this.error.set(this.i18n.t('results.no_claim'));
    }
  }

  loadClaim() {
    this.narrativeService.getClaim(this.claimId).subscribe({
      next: (data) => {
        this.claimData.set(data);
        this.loading.set(false);
      },
      error: (err) => { this.error.set(err.message || this.i18n.t('results.load_error')); this.loading.set(false); },
    });
  }

  onChatOpened() {
    if (this.suggestionsRequested) return;
    this.suggestionsRequested = true;
    this.loadSuggestions();
  }

  loadSuggestions() {
    this.narrativeService.getFollowUpSuggestions(this.claimId).subscribe({
      next: (res) => {
        this.followupSuggestions.set(res?.suggestions || []);
        this.suggestionsLoaded.set(true);
      },
      error: () => {
        this.followupSuggestions.set([]);
        this.suggestionsLoaded.set(true);
      },
    });
  }

  // Replace a clicked template with a fresh one, animating the chip out first.
  private replaceSuggestion(exclude: string[]) {
    this.narrativeService.getNextSuggestion(this.claimId, exclude).subscribe({
      next: (res) => {
        const next = res?.suggestion;
        if (next) {
          this.followupSuggestions.update(list => [...list, next]);
        }
      },
      error: () => {},
    });
  }

  goBack() { this.router.navigate(['/dashboard']); }

  sectorsUrl(ticker: string): string {
    return `https://sectors.app/idx/${ticker.toLowerCase()}`;
  }

  retry() {
    const narrative = this.claimData()?.narrative;
    if (narrative) {
      this.router.navigate(['/claim'], { queryParams: { narrative } });
    }
  }

  assertion() {
    const claim = this.claimData()?.claim;
    if (!claim) return '';
    return this.i18n.language() === 'en' && claim.assertion_en ? claim.assertion_en : claim.assertion;
  }

  explanation = () => {
    const score = this.claimData()?.score;
    if (!score) return '';
    return this.i18n.language() === 'en' && score.explanation_en ? score.explanation_en : score.explanation;
  };

  narrative = () => {
    const lang = this.i18n.language() === 'en' ? 'en' : 'id';
    return buildVerdictNarrative(this.claimData(), lang);
  };

  scoreValue = () => this.claimData()?.score?.reality_gap_score ?? 0;
  policySector = () => this.claimData()?.claim?.sector ?? null;
  verdictValue = () => this.claimData()?.score?.verdict ?? '';
  dimensions = () => this.claimData()?.score?.dimensions ?? {};
  valuation = () => this.claimData()?.evidence?.valuation ?? null;
  fundamental = () => this.claimData()?.evidence?.fundamental ?? null;
  market = () => this.claimData()?.evidence?.market ?? null;
  news = () => this.claimData()?.evidence?.news ?? null;
  corpActions = () => this.claimData()?.evidence?.corporate_actions ?? null;
  filings = () => this.claimData()?.evidence?.filings ?? null;

  directionIcon(direction: string): string {
    return this.format.directionIcon(direction);
  }

  directionLabel(direction: string): string {
    return this.i18n.t(`direction.${direction}`);
  }

  sendChat(question: string) {
    if (!question || this.chatLoading()) return;
    this.chatMessages.update(m => [...m, { role: 'user', text: question }]);
    this.chatLoading.set(true);
    this.narrativeService.askFollowUp(this.claimId, question).subscribe({
      next: (res) => {
        const text = this.i18n.language() === 'en' && res.answer_en ? res.answer_en : res.answer;
        this.chatMessages.update(m => [...m, { role: 'assistant', text }]);
        this.chatLoading.set(false);
      },
      error: () => {
        this.chatMessages.update(m => [...m, { role: 'assistant', text: this.i18n.t('chat.error') }]);
        this.chatLoading.set(false);
      },
    });
  }

  onSuggestionClick(s: FollowUpSuggestion) {
    const text = this.i18n.language() === 'en' && s.text_en ? s.text_en : s.text;
    const exclude = this.followupSuggestions().map(x => x.text);
    this.narrativeService.recordSuggestionFeedback(this.claimId, s.id, s.text).subscribe({
      error: () => {},
    });
    this.sendChat(text);

    // Dismiss the clicked chip, then generate a fresh template to replace it.
    this.removingId.set(s.id);
    window.setTimeout(() => {
      this.followupSuggestions.update(list => list.filter(x => x.id !== s.id));
      this.removingId.set('');
      this.replaceSuggestion(exclude);
    }, 200);
  }
}