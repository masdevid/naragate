import { Injectable, computed, signal } from '@angular/core';
import { Observable } from 'rxjs';

export interface AuthUser {
  authenticated: boolean;
  email?: string | null;
  subscription_tier?: string | null;
  credits?: number | null;
  promo_credits?: number | null;
  key_bound?: boolean;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private apiUrl = '/api/v1/auth';
  private _user = signal<AuthUser | null>(null);

  readonly user = this._user.asReadonly();
  readonly isAuthenticated = computed(() => !!this._user()?.authenticated);

  private request(method: string, path: string, body?: unknown): Observable<AuthUser> {
    return new Observable(observer => {
      fetch(`${this.apiUrl}${path}`, {
        method,
        credentials: 'same-origin',
        headers: body ? { 'Content-Type': 'application/json' } : undefined,
        body: body ? JSON.stringify(body) : undefined,
      })
        .then(async r => {
          const data = await r.json().catch(() => ({}));
          if (!r.ok) throw new Error(data?.detail || `Request failed (HTTP ${r.status})`);
          this._user.set(data);
          observer.next(data);
          observer.complete();
        })
        .catch(err => observer.error(err));
    });
  }

  login(email: string, password: string, apiKey?: string): Observable<AuthUser> {
    const body: Record<string, string> = { email, password };
    if (apiKey && apiKey.trim()) body['api_key'] = apiKey.trim();
    return this.request('POST', '/login', body);
  }

  logout(): Observable<AuthUser> {
    return this.request('POST', '/logout');
  }

  me(): Observable<AuthUser> {
    return this.request('GET', '/me');
  }
}
