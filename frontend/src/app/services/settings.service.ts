import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface RuntimeSettings {
  llm_endpoint?: string;
  llm_api_key?: string;
  llm_model?: string;
  sectors_api_key?: string;
  sectors_key_bound_to?: string | null;
  sectors_key_owner_ip?: string | null;
  sectors_authorized_ips?: string[];
  sectors_key_is_owner?: boolean;
  sectors_enforce_per_ip?: boolean;
  client_ip?: string;
  claim_parser_model?: string;
  skeptic_model?: string;
  scorer_model?: string;
  news_model?: string;
  chat_model?: string;
  [key: string]: string | number | boolean | string[] | null | undefined;
}

export interface ValidateResult {
  ok: boolean;
  endpoint: string;
  models: string[];
  error?: string;
}

export interface SectorsValidateResult {
  ok: boolean;
  error?: string;
}

export interface SetupStatus {
  complete: boolean;
  missing: string[];
}

@Injectable({ providedIn: 'root' })
export class SettingsService {
  private apiUrl = '/api/v1/settings';

  getSettings(): Observable<RuntimeSettings> {
    return new Observable(observer => {
      fetch(this.apiUrl)
        .then(r => r.json())
        .then(data => { observer.next(data); observer.complete(); })
        .catch(err => observer.error(err));
    });
  }

  updateSettings(settings: Partial<RuntimeSettings>): Observable<any> {
    return new Observable(observer => {
      fetch(this.apiUrl, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      })
        .then(r => r.json())
        .then(data => { observer.next(data); observer.complete(); })
        .catch(err => observer.error(err));
    });
  }

  resetSettings(): Observable<any> {
    return new Observable(observer => {
      fetch(this.apiUrl, { method: 'DELETE' })
        .then(r => r.json())
        .then(data => { observer.next(data); observer.complete(); })
        .catch(err => observer.error(err));
    });
  }

  validateEndpoint(endpoint: string, apiKey?: string): Observable<ValidateResult> {
    return new Observable(observer => {
      fetch(`${this.apiUrl}/validate-llm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ endpoint, api_key: apiKey || null }),
      })
        .then(r => r.json())
        .then(data => { observer.next(data); observer.complete(); })
        .catch(err => observer.error(err));
    });
  }

  validateSectors(apiKey: string): Observable<SectorsValidateResult> {
    return new Observable(observer => {
      fetch(`${this.apiUrl}/validate-sectors`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKey }),
      })
        .then(r => r.json())
        .then(data => { observer.next(data); observer.complete(); })
        .catch(err => observer.error(err));
    });
  }

  updateSectorsIp(ip: string, action: 'add' | 'remove'): Observable<any> {
    return new Observable(observer => {
      fetch(`${this.apiUrl}/sectors-ips`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip, action }),
      })
        .then(r => r.json())
        .then(data => {
          if (data && data.sectors_authorized_ips) {
            observer.next(data);
          } else {
            observer.error(new Error(data?.detail || 'Request failed'));
          }
          observer.complete();
        })
        .catch(err => observer.error(err));
    });
  }

  getSetupStatus(): Observable<SetupStatus> {
    return new Observable(observer => {
      fetch(`${this.apiUrl}/status`)
        .then(r => r.json())
        .then(data => { observer.next(data); observer.complete(); })
        .catch(err => observer.error(err));
    });
  }
}
