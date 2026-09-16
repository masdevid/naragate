import { Injectable, computed, signal } from '@angular/core';
import { Observable, map } from 'rxjs';

export interface AuthUser {
  authenticated: boolean;
  email?: string | null;
  subscription_tier?: string | null;
  credits?: number | null;
  promo_credits?: number | null;
  key_bound?: boolean;
}

export interface ApiToken {
  id: string;
  name: string;
  prefix?: string;
  created_at: string;
  last_used_at?: string | null;
  token?: string;
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

  listTokens(): Observable<ApiToken[]> {
    return this.tokenRequest<ApiToken[]>('GET', '/tokens').pipe(map(r => r.tokens || []));
  }

  createToken(name: string): Observable<ApiToken> {
    return this.tokenRequest<ApiToken>('POST', '/tokens', { name });
  }

  revokeToken(id: string): Observable<unknown> {
    return this.tokenRequest<unknown>('DELETE', `/tokens/${id}`);
  }

  private tokenRequest<T>(method: string, path: string, body?: unknown): Observable<any> {
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
          observer.next(data as T);
          observer.complete();
        })
        .catch(err => observer.error(err));
    });
  }
}
