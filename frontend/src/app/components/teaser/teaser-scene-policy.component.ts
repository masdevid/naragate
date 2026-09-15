import { Component } from '@angular/core';

@Component({
  selector: 'app-teaser-scene-policy',
  standalone: true,
  template: `
    <div class="scene">
      <div class="progress"><i></i><i></i><i></i><i class="on"></i><i></i><i></i></div>
      <div class="badge"><span class="wordmark"><span class="nara">NARA</span><span class="gate">GATE</span></span></div>

      <div class="heading"><b>Policy Amplifier</b> &mdash; narasi kebijakan tanpa ticker pun tetap dipetakan.</div>

      <!-- 1 · the policy narrative (no ticker) -->
      <div class="event">
        <div class="event__label">Narasi masuk</div>
        <div class="event__text">&ldquo;HBA batu bara naik untuk Q3.&rdquo;</div>
        <div class="event__tags">
          <span class="tag tag--warn">&#9888; tanpa ticker</span>
          <span class="tag">komoditas</span>
        </div>
        <div class="event__chart">
          <svg viewBox="0 0 220 60" preserveAspectRatio="none" aria-hidden="true" style="display:block;width:100%;height:54px">
            <polyline class="spark" points="0,48 22,46 44,49 66,38 88,41 110,30 132,33 154,22 176,25 198,13 220,10" />
          </svg>
          <div class="event__meta"><span>HBA</span><span style="color: var(--verified)">&#9650; tren naik</span></div>
        </div>
      </div>

      <!-- 2 · the resolver pipeline -->
      <div class="resolver">
        <div class="step s1"><span style="font-size:18px">&#129517;</span><span style="font-size:14px;color:var(--text-primary)">Ekstrak sinyal kebijakan</span></div>
        <div class="link l1"></div>
        <div class="step s2"><span style="font-size:18px">&#127919;</span><span style="font-size:14px;color:var(--text-primary)">Petakan ke sektor</span></div>
        <div class="link l2"></div>
        <div class="step s3"><span style="font-size:18px">&#128200;</span><span style="font-size:14px;color:var(--text-primary)">Ukur dampak real-time</span></div>
      </div>

      <!-- 3 · the resolved sector -->
      <div class="sector">
        <div class="sector__label">Resolved ke</div>
        <div class="sector__name">Sektor Batu Bara</div>
        <div class="sector__members">
          <span class="member">ADRO<i class="mbar mb1"></i></span>
          <span class="member">ITMG<i class="mbar mb2"></i></span>
          <span class="member">PTBA<i class="mbar mb3"></i></span>
        </div>
        <div class="dim">
          <div class="dim__head"><span>+ Policy-Gap dimension</span><span style="color: var(--brand-to); font-weight: 600">72</span></div>
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
    .wordmark { font-family: var(--font-display); font-weight: 700; display: inline-flex; }
    .wordmark .nara { background: linear-gradient(90deg, var(--brand-from), var(--brand-to)); -webkit-background-clip: text; background-clip: text; color: transparent; }
    .wordmark .gate { color: #fff; }
    .badge { position: absolute; top: 32px; left: 40px; }
    .badge .wordmark { font-size: 22px; }
    .heading { position: absolute; top: 104px; left: 96px; max-width: 820px; font-family: var(--font-display); font-weight: 500; font-size: 24px; color: var(--text-primary); opacity: 0; animation: poFadeUp .5s ease-out forwards; animation-delay: .3s; }
    .heading b { color: var(--brand-to); font-weight: 700; }

    /* shared card shell */
    .event, .resolver, .sector { position: absolute; top: 210px; opacity: 0; animation: poFadeUp .5s ease-out forwards; }
    .event, .sector { background: var(--bg-panel); border: 1px solid var(--line); border-radius: 14px; }
    .event { left: 72px; width: 300px; padding: 20px; animation-delay: 1.0s; }
    .sector { right: 72px; width: 320px; padding: 22px; animation-delay: 5.2s; }

    /* 1 · policy narrative */
    .event__label, .event__meta, .tag, .sector__label, .dim__head { font-size: 12px; color: var(--text-muted); }
    .event__label { margin-bottom: 8px; }
    .event__text { font-size: 19px; line-height: 1.35; }
    .event__tags { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
    .tag { padding: 3px 10px; border-radius: 999px; border: 1px solid var(--line); }
    .tag--warn { color: var(--brand-from); border-color: rgba(227,28,95,.4); }
    .event__chart { margin-top: 18px; }
    .spark { fill: none; stroke: var(--brand-to); stroke-width: 2.5; stroke-linecap: round; stroke-dasharray: 260; stroke-dashoffset: 260; animation: poSpark 1.4s ease-out forwards; animation-delay: 2s; }
    @keyframes poSpark { to { stroke-dashoffset: 0; } }
    .event__meta { display: flex; justify-content: space-between; margin-top: 8px; }
    .event__meta .up { color: var(--verified); }

    /* 2 · resolver pipeline */
    .resolver { left: 452px; width: 392px; display: flex; flex-direction: column; align-items: center; gap: 10px; animation-delay: 2.4s; }
    .step { width: 240px; display: flex; align-items: center; gap: 12px; padding: 12px 16px; background: var(--bg-panel); border: 1px solid var(--line); border-radius: 10px; opacity: 0; transform: translateY(8px); animation: poStepIn .45s ease-out forwards; }
    .s1 { animation-delay: 2.6s; } .s2 { animation-delay: 3.6s; } .s3 { animation-delay: 4.6s; }
    @keyframes poStepIn { to { opacity: 1; transform: translateY(0); } }
    .link { width: 2px; height: 16px; background: linear-gradient(180deg, var(--brand-from), var(--brand-to)); transform: scaleY(0); transform-origin: top; animation: poLink .3s ease-out forwards; }
    .link.l1 { animation-delay: 3.35s; } .link.l2 { animation-delay: 4.35s; }
    @keyframes poLink { to { transform: scaleY(1); } }

    /* 3 · resolved sector */
    .sector__label { margin-bottom: 6px; }
    .sector__name { font-family: var(--font-display); font-weight: 700; font-size: 22px; }
    .sector__members { margin-top: 14px; display: flex; flex-direction: column; gap: 8px; }
    .member { display: grid; grid-template-columns: 3.25rem 1fr; align-items: center; gap: 10px; font-size: 13px; color: var(--text-muted); }
    .mbar { height: 6px; border-radius: 999px; background: linear-gradient(90deg, var(--brand-from), var(--brand-to)); width: 0; animation: poBar 1s ease-out forwards; animation-delay: 5.6s; }
    .mb1 { --w: 86%; } .mb2 { --w: 64%; } .mb3 { --w: 74%; }
    @keyframes poBar { to { width: var(--w); } }
    .dim { margin-top: 18px; }
    .dim__head { display: flex; justify-content: space-between; margin-bottom: 6px; }
    .dim__val { color: var(--brand-to); font-weight: 600; }
    .track { height: 8px; border-radius: 999px; background: var(--bg-deep); overflow: hidden; }
    .fill { height: 100%; width: 0; border-radius: 999px; background: linear-gradient(90deg, var(--brand-from), var(--brand-to)); animation: poFill 1.4s ease-out forwards; animation-delay: 6s; }
    @keyframes poFill { to { width: 72%; } }

    .caption { position: absolute; left: 0; right: 0; bottom: 48px; text-align: center; font-family: var(--font-display); font-weight: 500; font-size: 27px; color: var(--text-primary); opacity: 0; animation: poFadeUp .6s ease-out forwards; animation-delay: 7.4s; }
    @keyframes poFadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
  `],
})
export class TeaserScenePolicyComponent {}
