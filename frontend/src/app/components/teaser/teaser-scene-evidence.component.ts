import { Component, OnDestroy, OnInit, signal } from '@angular/core';

@Component({
  selector: 'app-teaser-scene-evidence',
  standalone: true,
  template: `
    <div class="scene">
      <div class="progress"><i></i><i class="on"></i><i></i><i></i><i></i><i></i></div>

      <div class="hero">
        <span class="wordmark"><span class="nara">NARA</span><span class="gate">GATE</span></span>
        <span class="tagline">Agent dan Asisten Pemeriksa Fakta Keuangan</span>
        <span class="tagline tagline--2">Jembatan Navigasi Finansial di Era Narasi Palsu</span>
      </div>

      <div class="badge"><span class="wordmark"><span class="nara">NARA</span><span class="gate">GATE</span></span></div>

      <div class="claim-wrap">
        <div class="claim-label">Narasi masuk</div>
        <div class="claim-box">&ldquo;PE BBCA mahal di 25x, jauh di atas rata-rata sektor 18x.&rdquo;</div>
      </div>

      <div class="evidence">
        <div class="row r1"><span class="k">PE BBCA</span><span class="v">25.0x</span></div>
        <div class="row r2"><span class="k">Rata-rata sektor</span><span class="v">18.0x</span></div>
        <div class="row r3"><span class="k">Premium</span><span class="v">+39%</span></div>
        <div class="row r4"><span class="k">Sumber</span><span class="v">Sectors v2 &mdash; Valuation Report</span></div>
      </div>

      <div class="gauge-wrap">
        <svg viewBox="0 0 120 120">
          <defs>
            <linearGradient id="teaserGaugeGrad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stop-color="#E31C5F"/>
              <stop offset="100%" stop-color="#F5A623"/>
            </linearGradient>
          </defs>
          <circle class="track" cx="60" cy="60" r="54"/>
          <circle class="fill" cx="60" cy="60" r="54"/>
        </svg>
        <div class="gauge-num">{{ gaugeNum() }}</div>
        <div class="gauge-label">Reality Gap Score</div>
        <div class="gauge-verdict">&#9989; Supported &mdash; evidence confidence tinggi</div>
      </div>

      <div class="caption">Bukan opini. Data asli dari Sectors API.</div>
    </div>
  `,
  styles: [`
    :host { position: absolute; inset: 0; overflow: hidden; }
    .progress { position: absolute; top: 28px; right: 36px; display: flex; gap: 8px; z-index: 6; }
    .progress i { width: 7px; height: 7px; border-radius: 50%; background: var(--line); }
    .progress i.on { background: var(--brand-to); }

    .wordmark { font-family: var(--font-display); font-weight: 700; display: inline-flex; user-select: none; }
    .wordmark .nara { background: linear-gradient(90deg, var(--brand-from), var(--brand-to)); -webkit-background-clip: text; background-clip: text; color: transparent; }
    .wordmark .gate { color: #fff; }

    .hero {
      position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px;
      opacity: 0; animation: evHeroIn .5s ease-out forwards, evHeroOut .5s ease-in forwards;
      animation-delay: .15s, 2.15s;
    }
    .hero .wordmark { font-size: 64px; }
    .hero .tagline { font-family: var(--font-display); font-weight: 500; font-size: 22px; color: var(--text-primary); }
    .hero .tagline--2 { font-size: 18px; color: var(--text-muted); }
    @keyframes evHeroIn { to { opacity: 1; } }
    @keyframes evHeroOut { to { opacity: 0; visibility: hidden; } }

    .badge { position: absolute; top: 32px; left: 40px; opacity: 0; animation: evBadgeIn .45s ease-out forwards; animation-delay: 2.5s; }
    .badge .wordmark { font-size: 22px; }
    @keyframes evBadgeIn { to { opacity: 1; } }

    .claim-wrap { position: absolute; top: 150px; left: 64px; width: 620px; opacity: 0; animation: evFadeUp .5s ease-out forwards; animation-delay: 2.9s; }
    .claim-label { font-size: 13px; color: var(--text-muted); margin-bottom: 8px; }
    .claim-box {
      background: var(--bg-panel); border: 1px solid var(--line); border-radius: 12px;
      padding: 18px 20px; font-size: 19px; line-height: 1.4; color: var(--text-primary);
      position: relative; overflow: hidden; white-space: nowrap; width: 0;
      animation: evType 1.3s steps(46,end) forwards; animation-delay: 3.1s;
    }
    @keyframes evType { to { width: 560px; } }
    @keyframes evFadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

    .evidence { position: absolute; top: 312px; left: 64px; width: 560px; display: flex; flex-direction: column; gap: 10px; }
    .row {
      display: flex; justify-content: space-between; align-items: baseline;
      padding: 11px 16px; background: var(--bg-panel-2); border: 1px solid var(--line); border-radius: 10px;
      opacity: 0; transform: translateX(-8px); animation: evRowIn .45s ease-out forwards; font-size: 16px;
    }
    .row .k { color: var(--text-muted); }
    .row .v { font-weight: 600; color: var(--text-primary); }
    .row.r1 { animation-delay: 4.6s; }
    .row.r2 { animation-delay: 5.05s; }
    .row.r3 { animation-delay: 5.5s; }
    .row.r4 { animation-delay: 5.95s; }
    .row.r3 .v { color: var(--brand-to); }
    @keyframes evRowIn { to { opacity: 1; transform: translateX(0); } }

    .gauge-wrap {
      position: absolute; top: 190px; right: 96px; width: 340px; height: 340px;
      display: flex; align-items: center; justify-content: center; flex-direction: column;
      opacity: 0; animation: evFadeUp .5s ease-out forwards; animation-delay: 4.0s;
    }
    .gauge-wrap svg { position: absolute; inset: 0; transform: rotate(-90deg); }
    .gauge-wrap .track { fill: none; stroke: var(--line); stroke-width: 14; }
    .gauge-wrap .fill {
      fill: none; stroke-width: 14; stroke-linecap: round; stroke: url(#teaserGaugeGrad);
      stroke-dasharray: 339.3; stroke-dashoffset: 339.3;
      animation: evDraw 2s cubic-bezier(.2,.8,.2,1) forwards; animation-delay: 4.4s;
    }
    @keyframes evDraw { to { stroke-dashoffset: 125.5; } } /* 63 / 100 */
    .gauge-num { font-family: var(--font-display); font-weight: 700; font-size: 64px; }
    .gauge-label { font-size: 13px; color: var(--text-muted); margin-top: 4px; }
    .gauge-verdict {
      margin-top: 10px; font-family: var(--font-display); font-weight: 600; font-size: 17px; color: var(--verified);
      opacity: 0; animation: evFadeUp .4s ease-out forwards; animation-delay: 6.7s;
    }

    .caption {
      position: absolute; left: 0; right: 0; bottom: 56px; text-align: center;
      font-family: var(--font-display); font-weight: 500; font-size: 28px; color: var(--text-primary);
      opacity: 0; animation: evFadeUp .6s ease-out forwards; animation-delay: 7.6s;
    }
  `],
})
export class TeaserSceneEvidenceComponent implements OnInit, OnDestroy {
  readonly gaugeNum = signal(0);
  private timers: ReturnType<typeof setTimeout>[] = [];
  private raf = 0;

  ngOnInit() {
    this.timers.push(setTimeout(() => this.countTo(63, 2000), 4400));
  }

  ngOnDestroy() {
    this.timers.forEach(clearTimeout);
    cancelAnimationFrame(this.raf);
  }

  private countTo(target: number, duration: number) {
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, Math.max(0, (now - start) / duration));
      this.gaugeNum.set(Math.round(t * target));
      if (t < 1) this.raf = requestAnimationFrame(tick);
    };
    this.raf = requestAnimationFrame(tick);
  }
}
