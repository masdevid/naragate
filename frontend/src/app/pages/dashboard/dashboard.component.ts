import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { NarrativeService } from '../../services/narrative.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  template: `
    <div class="min-h-screen bg-slate-900 p-8">
      <div class="max-w-4xl mx-auto">
        <h1 class="text-4xl font-bold text-white mb-2">Naragate</h1>
        <p class="text-slate-400 mb-8">AI evidence engine for Indonesian market narratives</p>

        <div class="bg-slate-800 rounded-lg p-6 border border-slate-700 mb-8">
          <h2 class="text-xl font-semibold text-white mb-4">Analyze a Narrative</h2>
          <textarea
            [(ngModel)]="narrative"
            class="w-full h-32 bg-slate-700 text-white rounded-lg p-4 border border-slate-600 focus:border-blue-500 focus:outline-none resize-none"
            placeholder="Enter an Indonesian market narrative... (e.g., 'BBCA labanya jeblok tapi PE-nya mahal')">
          </textarea>
          <button
            (click)="startAnalysis()"
            [disabled]="!narrative.trim()"
            class="mt-4 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed">
            Analyze
          </button>
        </div>

        @if (recentClaims.length) {
          <div class="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <h2 class="text-xl font-semibold text-white mb-4">Recent Analyses</h2>
            <div class="space-y-3">
              @for (claim of recentClaims; track claim.claim_id) {
                <button (click)="viewClaim(claim.claim_id)"
                  class="w-full text-left bg-slate-700/50 hover:bg-slate-700 rounded p-4 transition">
                  <p class="text-slate-300 text-sm truncate">{{ claim.narrative }}</p>
                  <p class="text-slate-500 text-xs mt-1">{{ claim.status }} • {{ claim.created_at | date:'short' }}</p>
                </button>
              }
            </div>
          </div>
        }
      </div>
    </div>
  `,
})
export class DashboardComponent implements OnInit {
  narrative = '';
  recentClaims: any[] = [];

  constructor(private router: Router, private narrativeService: NarrativeService) {}

  ngOnInit() {
    this.narrativeService.getClaims().subscribe({
      next: (claims) => this.recentClaims = claims,
      error: () => {},
    });
  }

  startAnalysis() {
    if (this.narrative.trim()) {
      this.router.navigate(['/claim'], { queryParams: { narrative: this.narrative } });
    }
  }

  viewClaim(claimId: string) {
    this.router.navigate(['/results', claimId]);
  }
}
