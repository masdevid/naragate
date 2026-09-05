import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface UsageSummary {
  sectors: {
    total_calls: number;
    budget: number;
    budget_pct: number;
    remaining: number;
  };
  llm: {
    model: string;
    total_calls: number;
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    estimated_cost_usd: number;
  };
  pipelines: {
    total: number;
    completed: number;
    failed: number;
  };
  daily: {
    date: string;
    sectors_calls: number;
    llm_calls: number;
    llm_input_tokens: number;
    llm_output_tokens: number;
  }[];
}

@Injectable({ providedIn: 'root' })
export class UsageService {
  private apiUrl = '/api/v1/usage';

  getUsage(): Observable<UsageSummary> {
    return new Observable(observer => {
      fetch(this.apiUrl)
        .then(r => r.json())
        .then(data => { observer.next(data); observer.complete(); })
        .catch(err => observer.error(err));
    });
  }
}