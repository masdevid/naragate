import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { NarrativeService } from '../../services/narrative.service';
import { ScoreGaugeComponent } from '../../components/score-gauge/score-gauge.component';
import { VerdictBadgeComponent } from '../../components/verdict-badge/verdict-badge.component';
import { EvidenceCardComponent } from '../../components/evidence-card/evidence-card.component';
import { SkepticPanelComponent } from '../../components/skeptic-panel/skeptic-panel.component';

@Component({
  selector: 'app-results',
  standalone: true,
  imports: [ScoreGaugeComponent, VerdictBadgeComponent, EvidenceCardComponent, SkepticPanelComponent],
  template: `
    <div class="min-h-screen bg-slate-900 p-8">
      <div class="max-w-4xl mx-auto">
        <button (click)="goBack()" class="text-slate-400 hover:text-white mb-4">← Back</button>

        @if (loading) {
          <div class="text-center py-16">
            <p class="text-slate-400 text-lg">Loading results...</p>
          </div>
        } @else if (error) {
          <div class="bg-red-900/50 rounded-lg p-6 border border-red-700">
            <p class="text-red-300">{{ error }}</p>
          </div>
        } @else if (claimData) {
          <div class="mb-6">
            <p class="text-slate-500 text-sm mb-2">Narrative</p>
            <p class="text-slate-300 italic">"{{ claimData.narrative }}"</p>
          </div>

          @if (claimData.claim) {
            <div class="bg-slate-800 rounded-lg p-6 border border-slate-700 mb-6">
              <p class="text-slate-500 text-sm mb-2">Extracted Claim</p>
              <p class="text-white text-lg">{{ claimData.claim.assertion }}</p>
              <div class="flex gap-4 mt-2">
                <span class="text-slate-400 text-sm">Ticker: <span class="text-white">{{ claimData.claim.ticker }}</span></span>
                <span class="text-slate-400 text-sm">Category: <span class="text-white">{{ claimData.claim.category }}</span></span>
                <span class="text-slate-400 text-sm">Direction: <span class="text-white">{{ claimData.claim.direction }}</span></span>
              </div>
            </div>
          }

          @if (claimData.score) {
            <div class="bg-slate-800 rounded-lg p-6 border border-slate-700 mb-6">
              <div class="flex items-center gap-8">
                <app-score-gauge [score]="claimData.score.reality_gap_score"/>
                <div>
                  <app-verdict-badge [verdict]="claimData.score.verdict"/>
                  <p class="text-slate-400 text-sm mt-4 max-w-md">{{ claimData.score.explanation }}</p>
                </div>
              </div>
            </div>
          }

          @if (claimData.evidence) {
            <div class="space-y-4 mb-6">
              @if (claimData.evidence.valuation) {
                <app-evidence-card title="Valuation Evidence" [cacheHit]="claimData.evidence.valuation.cache_hit">
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <p class="text-slate-500 text-xs">PE Ratio</p>
                      <p class="text-white">{{ claimData.evidence.valuation.metrics.pe || 'N/A' }}</p>
                    </div>
                    <div>
                      <p class="text-slate-500 text-xs">PB Ratio</p>
                      <p class="text-white">{{ claimData.evidence.valuation.metrics.pb || 'N/A' }}</p>
                    </div>
                    <div>
                      <p class="text-slate-500 text-xs">PS Ratio</p>
                      <p class="text-white">{{ claimData.evidence.valuation.metrics.ps || 'N/A' }}</p>
                    </div>
                    <div>
                      <p class="text-slate-500 text-xs">PE Premium vs Median</p>
                      <p class="text-white">{{ claimData.evidence.valuation.premium_pct.pe || 'N/A' }}%</p>
                    </div>
                  </div>
                </app-evidence-card>
              }

              @if (claimData.evidence.fundamental) {
                <app-evidence-card title="Fundamental Evidence" [cacheHit]="claimData.evidence.fundamental.cache_hit">
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <p class="text-slate-500 text-xs">Revenue Trend</p>
                      <p class="text-white">{{ claimData.evidence.fundamental.trend.revenue_trend }}</p>
                    </div>
                    <div>
                      <p class="text-slate-500 text-xs">Earnings Trend</p>
                      <p class="text-white">{{ claimData.evidence.fundamental.trend.earnings_trend }}</p>
                    </div>
                    <div>
                      <p class="text-slate-500 text-xs">ROE</p>
                      <p class="text-white">{{ claimData.evidence.fundamental.metrics.roe || 'N/A' }}</p>
                    </div>
                    <div>
                      <p class="text-slate-500 text-xs">Debt to Equity</p>
                      <p class="text-white">{{ claimData.evidence.fundamental.metrics.debt_to_equity || 'N/A' }}</p>
                    </div>
                  </div>
                </app-evidence-card>
              }

              @if (claimData.evidence.market) {
                <app-evidence-card title="Market Evidence" [cacheHit]="claimData.evidence.market.cache_hit">
                  <div class="grid grid-cols-3 gap-4">
                    <div>
                      <p class="text-slate-500 text-xs">1D Change</p>
                      <p class="text-white">{{ claimData.evidence.market.performance['1d']?.price_change_pct || 'N/A' }}%</p>
                    </div>
                    <div>
                      <p class="text-slate-500 text-xs">7D Change</p>
                      <p class="text-white">{{ claimData.evidence.market.performance['7d']?.price_change_pct || 'N/A' }}%</p>
                    </div>
                    <div>
                      <p class="text-slate-500 text-xs">30D Change</p>
                      <p class="text-white">{{ claimData.evidence.market.performance['30d']?.price_change_pct || 'N/A' }}%</p>
                    </div>
                  </div>
                </app-evidence-card>
              }
            </div>
          }

          @if (claimData.skeptic) {
            <app-skeptic-panel
              [counterArguments]="claimData.skeptic.counter_arguments"
              [ambiguityPoints]="claimData.skeptic.ambiguity_points"
              [missingEvidence]="claimData.skeptic.missing_evidence"/>
          }
        }
      </div>
    </div>
  `,
})
export class ResultsComponent implements OnInit {
  claimId = '';
  claimData: any = null;
  loading = true;
  error = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private narrativeService: NarrativeService,
  ) {}

  ngOnInit() {
    this.claimId = this.route.snapshot.paramMap.get('id') || '';
    if (this.claimId) {
      this.loadClaim();
    } else {
      this.loading = false;
      this.error = 'No claim ID provided';
    }
  }

  loadClaim() {
    this.narrativeService.getClaim(this.claimId).subscribe({
      next: (data) => {
        this.claimData = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = err.message || 'Failed to load claim';
        this.loading = false;
      },
    });
  }

  goBack() {
    this.router.navigate(['/dashboard']);
  }
}
