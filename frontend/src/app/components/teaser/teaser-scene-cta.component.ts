import { Component } from '@angular/core';

@Component({
  selector: 'app-teaser-scene-cta',
  standalone: true,
  template: `
    <div class="scene">
      <div class="progress"><i></i><i></i><i></i><i></i><i></i><i class="on"></i></div>
      <div class="ring r2"></div>
      <div class="ring"></div>

      <span class="wordmark"><span class="nara">NARA</span><span class="gate">GATE</span></span>
      <div class="tagline">Verifikasi. Deteksi. Skor Realitas.</div>
      <div class="url">naragate.ilkomers.com</div>
      <div class="badge">Sectors Hackathon 2026 &middot; Track 1</div>
    </div>
  `,
  styles: [`
    :host { position: absolute; inset: 0; overflow: hidden; }
    .scene { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
    .progress { position: absolute; top: 28px; right: 36px; display: flex; gap: 8px; z-index: 6; }
    .progress i { width: 7px; height: 7px; border-radius: 50%; background: var(--line); }
    .progress i.on { background: var(--brand-to); }

    .ring {
      position: absolute; width: 420px; height: 420px; border-radius: 50%;
      border: 1px solid rgba(245,166,35,.28);
      opacity: 0; animation: ctRingIn 1s ease-out forwards, ctPulse 3.2s ease-in-out infinite;
      animation-delay: .1s, 1.1s;
    }
    .ring.r2 { width: 520px; height: 520px; border-color: rgba(227,28,95,.18); animation-delay: .3s, 1.3s; }
    @keyframes ctRingIn { to { opacity: 1; } }
    @keyframes ctPulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.035); } }

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
    .url {
      margin-top: 26px; font-size: 20px; color: var(--brand-to); letter-spacing: .01em;
      opacity: 0; animation: ctFadeUp .5s ease-out forwards; animation-delay: 4.6s;
    }
    .badge {
      margin-top: 22px; font-size: 13px; color: var(--text-muted);
      border: 1px solid var(--line); border-radius: 999px; padding: 8px 18px;
      opacity: 0; animation: ctFadeUp .5s ease-out forwards; animation-delay: 6.1s;
    }
    @keyframes ctFadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
  `],
})
export class TeaserSceneCtaComponent {}
