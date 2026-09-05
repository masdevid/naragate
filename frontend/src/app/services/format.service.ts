import { Injectable, inject } from '@angular/core';
import { I18nService } from './i18n.service';

@Injectable({ providedIn: 'root' })
export class FormatService {
  private i18n = inject(I18nService);

  private get locale(): string {
    return this.i18n.language() === 'en' ? 'en-US' : 'id-ID';
  }

  number(value: number | null | undefined, decimals = 2): string {
    if (value === null || value === undefined || Number.isNaN(value)) return '\u2014';
    return new Intl.NumberFormat(this.locale, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value);
  }

  percent(value: number | null | undefined, decimals = 1): string {
    if (value === null || value === undefined || Number.isNaN(value)) return '\u2014';
    return this.number(value, decimals) + '%';
  }

  idr(value: number | null | undefined): string {
    if (value === null || value === undefined || Number.isNaN(value)) return '\u2014';
    const isEn = this.i18n.language() === 'en';
    const abs = Math.abs(value);
    let scaled = value;
    let unit = '';
    let decimals = 0;
    if (abs >= 1e12) { scaled = value / 1e12; unit = isEn ? 'T' : ' T'; decimals = 1; }
    else if (abs >= 1e9) { scaled = value / 1e9; unit = isEn ? 'B' : ' M'; decimals = 1; }
    else if (abs >= 1e6) { scaled = value / 1e6; unit = isEn ? 'M' : ' Jt'; }
    else if (abs >= 1e3) { scaled = value / 1e3; unit = isEn ? 'K' : ' Rb'; }
    return (isEn ? 'IDR ' : 'Rp ') + this.number(scaled, decimals) + unit;
  }

  directionIcon(direction: string): string {
    switch (direction) {
      case 'above': return '\u25B2';
      case 'below': return '\u25BC';
      case 'between': return '\u21C4';
      case 'neutral': return '\u25C6';
      default: return '';
    }
  }

  trendClass(trend: string): string {
    switch (trend) {
      case 'improving': return 'trend--up';
      case 'declining': return 'trend--down';
      default: return 'trend--flat';
    }
  }

  changeClass(value: number | null | undefined): string {
    if (value === null || value === undefined || Number.isNaN(value) || value === 0) return '';
    return value > 0 ? 'trend--up' : 'trend--down';
  }
}