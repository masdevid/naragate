import { Component } from '@angular/core';

@Component({
  selector: 'app-teaser-scene-personas',
  standalone: true,
  template: `
    <div class="scene">
      <div class="progress"><i></i><i></i><i class="on"></i><i></i><i></i><i></i></div>
      <div class="badge"><span class="wordmark"><span class="nara">NARA</span><span class="gate">GATE</span></span></div>

      <div class="caption">Satu engine, semua kebutuhan.</div>

      <div class="row">
        <div class="card c1"><div class="icon">&#128241;</div><h3>Investor ritel</h3><p>Tempel pesan WhatsApp, langsung dapat fact-check.</p></div>
        <div class="card c2"><div class="icon">&#129518;</div><h3>Analis keuangan</h3><p>Verifikasi klaim sebelum masuk laporan.</p></div>
        <div class="card c3"><div class="icon">&#128737;</div><h3>Tim kepatuhan</h3><p>Saring klaim menyesatkan di media sosial.</p></div>
        <div class="card c4"><div class="icon">&#127974;</div><h3>Fund manager</h3><p>Pantau sinyal risiko kebijakan di sektor energi &amp; komoditas.</p></div>
      </div>
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
    .badge { position: absolute; top: 32px; left: 40px; }
    .badge .wordmark { font-size: 22px; }

    .row { position: absolute; left: 0; right: 0; bottom: 150px; display: flex; justify-content: center; gap: 40px; padding: 0 64px; }
    .card {
      width: 250px; background: var(--bg-panel); border: 1px solid var(--line); border-radius: 16px;
      padding: 26px 22px; opacity: 0; transform: translateY(28px);
      animation: peUp .55s cubic-bezier(.2,.8,.2,1) forwards;
    }
    .card .icon { font-size: 34px; }
    .card h3 { font-family: var(--font-display); font-weight: 600; font-size: 18px; margin: 14px 0 8px; color: var(--text-primary); }
    .card p { font-size: 14px; line-height: 1.5; color: var(--text-muted); margin: 0; }
    .c1 { margin-bottom: 0;    animation-delay: .3s; }
    .c2 { margin-bottom: 46px; animation-delay: 1.5s; }
    .c3 { margin-bottom: 0;    animation-delay: 2.7s; }
    .c4 { margin-bottom: 46px; animation-delay: 3.9s; }
    @keyframes peUp { to { opacity: 1; transform: translateY(0); } }

    .caption {
      position: absolute; left: 0; right: 0; top: 90px; text-align: center;
      font-family: var(--font-display); font-weight: 500; font-size: 30px; color: var(--text-primary);
      opacity: 0; animation: peCapIn .6s ease-out forwards; animation-delay: 6.4s;
    }
    @keyframes peCapIn { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
  `],
})
export class TeaserScenePersonasComponent {}
