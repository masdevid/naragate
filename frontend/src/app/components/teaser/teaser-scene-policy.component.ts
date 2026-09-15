import { Component } from '@angular/core';

@Component({
  selector: 'app-teaser-scene-policy',
  standalone: true,
  template: `
    <div class="scene">
      <div class="progress"><i></i><i></i><i></i><i class="on"></i><i></i><i></i></div>
      <div class="badge"><span class="wordmark"><span class="nara">NARA</span><span class="gate">GATE</span></span></div>

      <div class="chip">
        <div class="label">Narasi kebijakan</div>
        <div class="text">&ldquo;HBA batu bara naik untuk Q3.&rdquo;</div>
        <div class="no-ticker">&#9888; tanpa ticker</div>
      </div>

      <div class="resolver">
        <div class="line"></div>
        <div class="tag">Sector Resolver</div>
      </div>

      <div class="sector">
        <div class="label">Resolved ke</div>
        <div class="name">Sektor Batu Bara</div>
        <div class="members"><span>ADRO</span><span>ITMG</span><span>PTBA</span></div>
        <div class="dim">
          <div class="dimlabel">+ Policy-Gap dimension</div>
          <div class="track"><div class="fill"></div></div>
        </div>
      </div>

      <div class="caption">Narasi kebijakan tanpa ticker? Tetap terdeteksi.</div>
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

    .chip {
      position: absolute; top: 300px; left: 96px; width: 300px;
      background: var(--bg-panel); border: 1px solid var(--line); border-radius: 14px;
      padding: 20px; opacity: 0; animation: poFadeUp .5s ease-out forwards; animation-delay: .3s;
    }
    .chip .label { font-size: 12px; color: var(--text-muted); margin-bottom: 8px; }
    .chip .text { font-size: 19px; color: var(--text-primary); }
    .chip .no-ticker {
      display: inline-block; margin-top: 10px; font-size: 12px; color: var(--brand-from);
      border: 1px solid rgba(227,28,95,.4); border-radius: 999px; padding: 3px 10px;
      opacity: 0; animation: poFadeUp .4s ease-out forwards; animation-delay: 1.4s;
    }
    @keyframes poFadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

    .resolver { position: absolute; top: 328px; left: 420px; width: 230px; text-align: center; opacity: 0; animation: poFadeUp .5s ease-out forwards; animation-delay: 2.5s; }
    .resolver .line { height: 2px; background: linear-gradient(90deg, var(--brand-from), var(--brand-to)); width: 0; animation: poGrow 1s ease-out forwards; animation-delay: 2.6s; }
    @keyframes poGrow { to { width: 100%; } }
    .resolver .tag { margin-top: 10px; font-size: 13px; color: var(--text-muted); }

    .sector {
      position: absolute; top: 268px; right: 96px; width: 340px;
      background: var(--bg-panel); border: 1px solid var(--line); border-radius: 14px; padding: 22px;
      opacity: 0; animation: poFadeUp .55s ease-out forwards; animation-delay: 4.0s;
    }
    .sector .label { font-size: 12px; color: var(--text-muted); margin-bottom: 6px; }
    .sector .name { font-family: var(--font-display); font-weight: 700; font-size: 22px; }
    .sector .members { margin-top: 10px; display: flex; gap: 8px; flex-wrap: wrap; }
    .sector .members span { font-size: 13px; padding: 4px 10px; border-radius: 999px; background: var(--bg-deep); border: 1px solid var(--line); color: var(--text-muted); }
    .sector .dim { margin-top: 18px; }
    .sector .dim .dimlabel { font-size: 12px; color: var(--text-muted); margin-bottom: 6px; }
    .sector .track { height: 8px; border-radius: 999px; background: var(--bg-deep); overflow: hidden; }
    .sector .fill { height: 100%; width: 0; border-radius: 999px; background: linear-gradient(90deg, var(--brand-from), var(--brand-to)); animation: poFill 1.4s ease-out forwards; animation-delay: 5.6s; }
    @keyframes poFill { to { width: 72%; } }

    .caption {
      position: absolute; left: 0; right: 0; bottom: 56px; text-align: center;
      font-family: var(--font-display); font-weight: 500; font-size: 28px; color: var(--text-primary);
      opacity: 0; animation: poFadeUp .6s ease-out forwards; animation-delay: 7.4s;
    }
  `],
})
export class TeaserScenePolicyComponent {}
