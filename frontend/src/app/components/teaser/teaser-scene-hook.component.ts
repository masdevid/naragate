import { Component } from '@angular/core';

@Component({
  selector: 'app-teaser-scene-hook',
  standalone: true,
  template: `
    <div class="scene">
      <div class="progress"><i class="on"></i><i></i><i></i><i></i><i></i><i></i></div>

      <div class="bubble b1">&ldquo;BBCA labanya jeblok&rdquo;<span class="src">&mdash; grup WhatsApp</span></div>
      <div class="bubble b2">&ldquo;PE-nya masih murah kok&rdquo;<span class="src">&mdash; komentar media sosial</span></div>
      <div class="bubble b3">&ldquo;TLKM bakal meroket minggu depan&rdquo;<span class="src">&mdash; forum saham</span></div>
      <div class="bubble b4">&ldquo;HBA batu bara turun signifikan&rdquo;<span class="src">&mdash; judul berita</span></div>
      <div class="bubble b5">&ldquo;Subsidi BBM naik, untung ADRO&rdquo;<span class="src">&mdash; broadcast Telegram</span></div>
      <div class="bubble b6">&ldquo;PB-nya di bawah rata-rata sektor&rdquo;<span class="src">&mdash; caption video singkat</span></div>

      <div class="mark">?</div>
      <div class="caption">Narasi pasar menyebar cepat. Tapi&nbsp;&mdash;&nbsp;benarkah?</div>
    </div>
  `,
  styles: [`
    :host { position: absolute; inset: 0; overflow: hidden; }
    .scene::before {
      content: ""; position: absolute; inset: 0; opacity: .05; pointer-events: none;
      background: repeating-linear-gradient(115deg, #fff 0 1px, transparent 1px 46px);
    }
    .progress { position: absolute; top: 28px; right: 36px; display: flex; gap: 8px; z-index: 5; }
    .progress i { width: 7px; height: 7px; border-radius: 50%; background: var(--line); }
    .progress i.on { background: var(--brand-to); }

    .bubble {
      position: absolute; max-width: 300px; padding: 14px 18px; border-radius: 14px;
      background: var(--bg-panel); border: 1px solid var(--line);
      font-size: 19px; line-height: 1.35; color: var(--text-primary);
      opacity: 0; transform: translateY(14px) scale(.92);
      animation: hookPop .6s cubic-bezier(.2,.8,.2,1) forwards, hookDim .5s ease-in forwards;
      animation-delay: var(--in), 6.2s;
    }
    .bubble .src { display: block; margin-top: 6px; font-size: 12px; color: var(--text-muted); }
    @keyframes hookPop { to { opacity: 1; transform: translateY(0) scale(1); } }
    @keyframes hookDim { to { opacity: .22; filter: blur(1.5px); } }

    .b1 { top: 66px; left: 130px; transform: rotate(-4deg); --in: .2s; }
    .b2 { top: 66px; right: 150px; transform: rotate(3deg); --in: .9s; }
    .b3 { top: 330px; left: 56px; transform: rotate(2deg); --in: 1.6s; }
    .b4 { top: 330px; right: 56px; transform: rotate(-3deg); --in: 2.3s; }
    .b5 { bottom: 88px; left: 230px; transform: rotate(3deg); --in: 3.0s; }
    .b6 { bottom: 88px; right: 230px; transform: rotate(-2deg); --in: 3.7s; }

    .mark {
      position: absolute; top: 50%; left: 50%; transform: translate(-50%,-58%) scale(.5);
      font-family: var(--font-display); font-weight: 700; font-size: 180px; line-height: 1;
      background: linear-gradient(180deg, var(--brand-from), var(--brand-to));
      -webkit-background-clip: text; background-clip: text; color: transparent;
      opacity: 0; animation: hookReveal 1.1s cubic-bezier(.2,.8,.2,1) forwards;
      animation-delay: 5.6s;
      filter: drop-shadow(0 0 40px rgba(245,166,35,.25));
    }
    @keyframes hookReveal { to { opacity: 1; transform: translate(-50%,-58%) scale(1); } }

    .caption {
      position: absolute; left: 0; right: 0; bottom: 56px; text-align: center;
      font-family: var(--font-display); font-weight: 500; font-size: 30px; color: var(--text-primary);
      opacity: 0; animation: hookCapIn .7s ease-out forwards; animation-delay: 6.6s;
    }
    @keyframes hookCapIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
  `],
})
export class TeaserSceneHookComponent {}
