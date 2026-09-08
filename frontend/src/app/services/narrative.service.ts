import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { PipelineEvent } from '../models/pipeline.model';

@Injectable({ providedIn: 'root' })
export class NarrativeService {
  private apiUrl = '';

  analyze(narrative: string): Observable<PipelineEvent> {
    return this.streamEvaluate('/api/v1/stream/evaluate', { narrative });
  }

  analyzeBulk(narratives: string[]): Observable<PipelineEvent> {
    return this.streamEvaluate('/api/v1/stream/evaluate-bulk', { narratives });
  }

  private streamEvaluate(path: string, body: any): Observable<PipelineEvent> {
    return new Observable(observer => {
      const url = `${this.apiUrl}${path}`;

      fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }).then(response => {
        if (!response.ok) {
          if (response.status === 409) {
            response.json().then(body => {
              const err: any = new Error('setup_incomplete');
              err.code = 'setup_incomplete';
              err.missing = body?.detail?.missing || [];
              observer.error(err);
            }).catch(() => observer.error(new Error(`HTTP ${response.status}`)));
            return;
          }
          observer.error(new Error(`HTTP ${response.status}`));
          return;
        }

        const reader = response.body?.getReader();
        if (!reader) {
          observer.error(new Error('No response body'));
          return;
        }

        const decoder = new TextDecoder();
        let buffer = '';

        const processStream = async () => {
          try {
            let eventType = '';
            let eventData = '';

            const emitEvent = () => {
              if (!eventType || !eventData) return;
              try {
                const parsed = JSON.parse(eventData);
                observer.next({
                  event_type: eventType,
                  claim_id: parsed.claim_id || '',
                  data: parsed.data || parsed,
                  timestamp: parsed.timestamp || new Date().toISOString(),
                });
              } catch (e) {
                observer.next({
                  event_type: eventType,
                  claim_id: '',
                  data: eventData,
                  timestamp: new Date().toISOString(),
                });
              }
              eventType = '';
              eventData = '';
            };

            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split('\n');
              buffer = lines.pop() || '';

              for (const line of lines) {
                if (line.startsWith('event:')) {
                  eventType = line.slice(6).trim();
                } else if (line.startsWith('data:')) {
                  eventData = line.slice(5).trim();
                } else if (line === '') {
                  emitEvent();
                }
              }
            }

            // Flush a pending event whose blank-line terminator was consumed
            // by the buffer split (e.g. final event ending in a single \n).
            if (eventType && eventData) emitEvent();

            observer.complete();
          } catch (error) {
            observer.error(error);
          }
        };

        processStream();
      }).catch(error => {
        observer.error(error);
      });

      return () => {};
    });
  }

  getClaims(): Observable<any[]> {
    return new Observable(observer => {
      fetch(`${this.apiUrl}/api/v1/claims/`)
        .then(r => r.json())
        .then(data => { observer.next(data); observer.complete(); })
        .catch(err => observer.error(err));
    });
  }

  getClaimsSummary(): Observable<any> {
    return new Observable(observer => {
      fetch(`${this.apiUrl}/api/v1/claims/summary`)
        .then(r => r.json())
        .then(data => { observer.next(data); observer.complete(); })
        .catch(err => observer.error(err));
    });
  }

  getClaim(claimId: string): Observable<any> {
    return new Observable(observer => {
      fetch(`${this.apiUrl}/api/v1/claims/${claimId}`)
        .then(r => r.json())
        .then(data => { observer.next(data); observer.complete(); })
        .catch(err => observer.error(err));
    });
  }

  deleteClaim(claimId: string): Observable<any> {
    return new Observable(observer => {
      fetch(`${this.apiUrl}/api/v1/claims/${claimId}`, { method: 'DELETE' })
        .then(r => r.json())
        .then(data => { observer.next(data); observer.complete(); })
        .catch(err => observer.error(err));
    });
  }

  deleteClaims(claimIds: string[]): Observable<any> {
    return new Observable(observer => {
      fetch(`${this.apiUrl}/api/v1/claims/`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ claim_ids: claimIds }),
      })
        .then(r => r.json())
        .then(data => { observer.next(data); observer.complete(); })
        .catch(err => observer.error(err));
    });
  }

  deleteAllClaims(): Observable<any> {
    return new Observable(observer => {
      fetch(`${this.apiUrl}/api/v1/claims/all`, { method: 'DELETE' })
        .then(r => r.json())
        .then(data => { observer.next(data); observer.complete(); })
        .catch(err => observer.error(err));
    });
  }

  askFollowUp(claimId: string, question: string): Observable<any> {
    return new Observable(observer => {
      fetch(`${this.apiUrl}/api/v1/claims/${claimId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })
        .then(r => {
          if (!r.ok) {
            throw new Error(`HTTP ${r.status}`);
          }
          return r.json();
        })
        .then(data => { observer.next(data); observer.complete(); })
        .catch(err => observer.error(err));
    });
  }

  getFollowUpSuggestions(claimId: string): Observable<any> {
    return new Observable(observer => {
      fetch(`${this.apiUrl}/api/v1/claims/${claimId}/suggestions`)
        .then(r => {
          if (!r.ok) {
            throw new Error(`HTTP ${r.status}`);
          }
          return r.json();
        })
        .then(data => { observer.next(data); observer.complete(); })
        .catch(err => observer.error(err));
    });
  }

  recordSuggestionFeedback(claimId: string, suggestionId: string, text: string): Observable<any> {
    return new Observable(observer => {
      fetch(`${this.apiUrl}/api/v1/claims/${claimId}/suggestions/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ suggestion_id: suggestionId, text }),
      })
        .then(r => {
          if (!r.ok) {
            throw new Error(`HTTP ${r.status}`);
          }
          return r.json();
        })
        .then(data => { observer.next(data); observer.complete(); })
        .catch(err => observer.error(err));
    });
  }
}
