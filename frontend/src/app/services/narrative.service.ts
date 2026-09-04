import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { PipelineEvent } from '../models/pipeline.model';

@Injectable({ providedIn: 'root' })
export class NarrativeService {
  private apiUrl = 'http://localhost:8000';

  analyze(narrative: string): Observable<PipelineEvent> {
    return new Observable(observer => {
      const url = `${this.apiUrl}/api/v1/stream/evaluate`;
      const body = JSON.stringify({ narrative });

      fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body,
      }).then(response => {
        if (!response.ok) {
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
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split('\n');
              buffer = lines.pop() || '';

              let eventType = '';
              let eventData = '';

              for (const line of lines) {
                if (line.startsWith('event:')) {
                  eventType = line.slice(6).trim();
                } else if (line.startsWith('data:')) {
                  eventData = line.slice(5).trim();
                } else if (line === '' && eventType && eventData) {
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
                }
              }
            }
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

  getClaim(claimId: string): Observable<any> {
    return new Observable(observer => {
      fetch(`${this.apiUrl}/api/v1/claims/${claimId}`)
        .then(r => r.json())
        .then(data => { observer.next(data); observer.complete(); })
        .catch(err => observer.error(err));
    });
  }
}
