import { Injectable, signal } from '@angular/core';
import id from '../i18n/id';
import en from '../i18n/en';

const LANGUAGES: Record<string, Record<string, string>> = { id, en };

@Injectable({ providedIn: 'root' })
export class I18nService {
  private readonly STORAGE_KEY = 'naragate_lang';
  language = signal<string>(this.loadInitial());

  private loadInitial(): string {
    try {
      const saved = localStorage.getItem(this.STORAGE_KEY);
      if (saved && LANGUAGES[saved]) return saved;
    } catch {}
    return 'id';
  }

  t(key: string, params?: Record<string, string | number>): string {
    const lang = this.language();
    const dict = LANGUAGES[lang] || LANGUAGES['id'];
    let val = dict[key] ?? key;

    if (params) {
      for (const [k, v] of Object.entries(params)) {
        val = val.replace(new RegExp(`\\{\\{${k}\\}\\}`, 'g'), String(v));
      }
    }

    return val;
  }

  tEventTitle(eventType: string): string {
    return this.t(`claim.event_title.${eventType}`);
  }

  setLanguage(lang: string) {
    if (LANGUAGES[lang]) {
      this.language.set(lang);
      try { localStorage.setItem(this.STORAGE_KEY, lang); } catch {}
    }
  }

  getLanguages(): { code: string; label: string }[] {
    return [
      { code: 'id', label: 'Bahasa Indonesia' },
      { code: 'en', label: 'English' },
    ];
  }
}
