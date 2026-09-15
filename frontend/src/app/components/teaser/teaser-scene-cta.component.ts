import { Component } from '@angular/core';

@Component({
  selector: 'app-teaser-scene-cta',
  standalone: true,
  template: `
    <div class="scene">
      <div class="progress"><i></i><i></i><i></i><i></i><i></i><i class="on"></i></div>

      <!-- same window chrome as the Scene 5 repository pane -->
      <div class="win">
        <div class="bar">
          <span class="dot"></span><span class="dot"></span><span class="dot"></span>
          <span class="url">naragate.ilkomers.com</span>
        </div>

        <div class="cover">
          <img class="cover__img" src="assets/result-screenshot.png" alt="" aria-hidden="true">
          <span class="wordmark"><span class="nara">NARA</span><span class="gate">GATE</span></span>
          <div class="tagline">Verifikasi. Deteksi. Skor Realitas.</div>
          <div class="url-line">naragate.ilkomers.com</div>
          <div class="badge">Sectors Hackathon 2026 &middot; Track 1</div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host { position: absolute; inset: 0; overflow: hidden; }
    .progress { position: absolute; top: 28px; right: 36px; display: flex; gap: 8px; z-index: 6; }
    .progress i { width: 7px; height: 7px; border-radius: 50%; background: var(--line); }
    .progress i.on { background: var(--brand-to); }

    /* window chrome — identical voice to the Scene 5 repository window */
    .win {
      position: absolute;
      top: 84px; left: 80px; right: 80px; bottom: 72px;
      background: var(--bg-panel);
      border: 1px solid var(--line);
      border-radius: 12px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      opacity: 0;
      animation: ctWinIn .5s ease-out forwards;
      animation-delay: .15s;
    }
    .win .bar {
      display: flex; align-items: center; gap: 8px;
      padding: 10px 14px;
      background: var(--bg-deep);
      border-bottom: 1px solid var(--line);
    }
    .win .bar .dot { width: 9px; height: 9px; border-radius: 50%; background: var(--line); }
    .win .bar .url { margin-left: 10px; font-size: 12px; color: var(--text-muted); }
    @keyframes ctWinIn { to { opacity: 1; } }

    /* screenshot covers the background, darkened for legibility */
    .cover {
      position: relative;
      flex: 1;
      min-height: 0;
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      overflow: hidden;
      animation: ctCoverIn .8s ease-out forwards;
    }
    .cover__img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; z-index: 0; }
    .cover::after {
      content: ""; position: absolute; inset: 0; z-index: 1;
      background: linear-gradient(180deg, rgba(11,14,23,.72), rgba(11,14,23,.9));
    }
    .cover > * { position: relative; z-index: 2; }
    @keyframes ctCoverIn { from { opacity: .4; } to { opacity: 1; } }

    .wordmark {
      font-family: var(--font-display); font-weight: 700; font-size: 80px; display: inline-flex; user-select: none;
      opacity: 0; transform: scale(.85); animation: ctHeroIn .6s cubic-bezier(.2,.8,.2,1) forwards; animation-delay: 1.2s;
    }
    .wordmark .nara { background: linear-gradient(90deg, var(--brand-from), var(--brand-to)); -webkit-background-clip: text; background-clip: text; color: transparent; }
    .wordmark .gate { color: #fff; }
    @keyframes ctHeroIn { to { opacity: 1; transform: scale(1); } }

    .tagline {
      margin-top: 18px; font-family: var(--font-display); font-weight: 500; font-size: 24px; color: var(--text-primary);
      opacity: 0; animation: ctFadeUp .5s ease-out forwards; animation-delay: 3.1s;
    }
    .url-line {
      margin-top: 26px; font-size: 20px; color: var(--brand-to); letter-spacing: .01em;
      opacity: 0; animation: ctFadeUp .5s ease-out forwards; animation-delay: 4.6s;
    }
    .badge {
      margin-top: 22px; font-size: 13px; color: var(--text-muted);
      border: 1px solid var(--line); border-radius: 999px; padding: 8px 18px;
      background: rgba(20,26,38,.6);
      opacity: 0; animation: ctFadeUp .5s ease-out forwards; animation-delay: 6.1s;
    }
    @keyframes ctFadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

    @media (prefers-reduced-motion: reduce) {
      .win, .cover, .wordmark, .tagline, .url-line, .badge { animation-duration: .2s; }
    }
  `],
})
export class TeaserSceneCtaComponent {}
