import { Component } from '@angular/core';

@Component({
  selector: 'app-teaser-scene-surfaces',
  standalone: true,
  template: `
    <div class="scene">
      <div class="progress"><i></i><i></i><i></i><i></i><i class="on"></i><i></i></div>
      <div class="badge"><span class="wordmark"><span class="nara">NARA</span><span class="gate">GATE</span></span></div>

      <div class="divider"></div>

      <div class="pane left">
        <div class="win">
          <div class="bar"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="url">naragate.ilkomers.com</span></div>
          <div class="shotwrap">
            <img class="shot" src="assets/result-app.png"
              alt="Halaman hasil Naragate: klaim &quot;Saham UNVR turun 15% dalam seminggu&quot;, Reality Gap Score 58.76, verdict Campuran">
          </div>
        </div>
        <div class="pane-label">Web UI &mdash; hasil verifikasi langsung</div>
      </div>

      <div class="pane right">
        <div class="win">
          <div class="bar"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="url">repository</span></div>
          <div class="body">
            <div class="repo-path">github.com/<b>masdevid/naragate</b></div>
            <div class="bundle-item bi1"><span class="ic">&#128268;</span><span class="tx"><b>mcp/</b><span>MCP server &mdash; 19 tools siap pakai</span></span></div>
            <div class="bundle-item bi2"><span class="ic">&#128218;</span><span class="tx"><b>skills/</b><span>Skills package untuk agent apa pun</span></span></div>
            <div class="bundle-item bi3"><span class="ic">&#129302;</span><span class="tx"><b>agents/</b><span>Agent definitions siap deploy</span></span></div>
            <div class="repo-note">Satu <b>clone</b>, tiga cara pakai.</div>
          </div>
        </div>
        <div class="pane-label">Bundle MCP &middot; Skills &middot; Agents &mdash; satu repository</div>
      </div>

      <div class="shared"><span class="tag">Satu <b>Evidence Graph</b>, satu ledger kredit &mdash; apa pun jalurnya</span></div>

      <div class="caption">Web UI atau bundle MCP &middot; Skills &middot; Agents &mdash; satu repository.</div>
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

    .divider { position: absolute; top: 128px; left: 50%; width: 1px; height: 0; background: linear-gradient(180deg, var(--brand-from), var(--brand-to)); animation: suGrow 1s ease-out forwards; animation-delay: .2s; }
    @keyframes suGrow { to { height: 400px; } }

    .pane { position: absolute; top: 128px; width: 470px; opacity: 0; animation: suFadeUp .5s ease-out forwards; }
    .pane.left { left: 88px; animation-delay: 1.0s; }
    .pane.right { right: 88px; animation-delay: 3.0s; }
    @keyframes suFadeUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }

    /* both panes share the same window frame */
    .win {
      background: var(--bg-panel); border: 1px solid var(--line); border-radius: 12px;
      overflow: hidden; height: 372px; display: flex; flex-direction: column;
    }
    .win .bar { flex: 0 0 auto; display: flex; align-items: center; gap: 8px; padding: 10px 14px; background: var(--bg-deep); border-bottom: 1px solid var(--line); }
    .win .bar .dot { width: 9px; height: 9px; border-radius: 50%; background: var(--line); }
    .win .bar .url { margin-left: 10px; font-size: 12px; color: var(--text-muted); }

    /* web UI body is the screenshot, filling the frame.
       The wrapper oversizes by 200x40 and is top-left anchored, so the
       screenshot content sits 100px right and 20px lower than centre. */
    .shotwrap { flex: 1; min-height: 0; position: relative; overflow: hidden; }
    .shot { position: absolute; top: 0; left: 0; width: calc(100% + 200px); height: calc(100% + 40px); object-fit: cover; object-position: center; display: block; }

    /* repository window body: plain panel with the bundle list */
    .body { flex: 1; min-height: 0; overflow: hidden; padding: 20px; }
    .repo-path { font-size: 13px; color: var(--text-muted); margin-bottom: 14px; }
    .repo-path b { color: var(--text-primary); font-weight: 600; }
    .bundle-item { display: flex; align-items: center; gap: 12px; padding: 12px 14px; border-radius: 10px; background: var(--bg-deep); border: 1px solid var(--line); margin-bottom: 10px; opacity: 0; transform: translateX(10px); animation: suItemIn .4s ease-out forwards; }
    .bundle-item .ic { font-size: 18px; }
    .bundle-item .tx b { display: block; font-size: 14px; color: var(--text-primary); }
    .bundle-item .tx span { font-size: 12px; color: var(--text-muted); }
    .bi1 { animation-delay: 3.5s; } .bi2 { animation-delay: 3.95s; } .bi3 { animation-delay: 4.4s; }
    @keyframes suItemIn { to { opacity: 1; transform: translateX(0); } }
    .repo-note { margin-top: 6px; font-size: 12px; color: var(--text-muted); opacity: 0; animation: suItemIn .4s ease-out forwards; animation-delay: 4.9s; }
    .repo-note b { color: var(--brand-to); }

    .pane-label { margin-top: 12px; font-size: 13px; color: var(--text-muted); text-align: center; }

    .shared { position: absolute; left: 0; right: 0; top: 552px; text-align: center; opacity: 0; animation: suFadeUp .5s ease-out forwards; animation-delay: 5.4s; }
    .shared .tag { display: inline-block; font-size: 14px; padding: 8px 18px; border-radius: 999px; background: var(--bg-panel); border: 1px solid var(--line); color: var(--text-primary); }
    .shared .tag b { color: var(--brand-to); }

    .caption {
      position: absolute; left: 0; right: 0; bottom: 40px; text-align: center;
      font-family: var(--font-display); font-weight: 500; font-size: 27px; color: var(--text-primary);
      opacity: 0; animation: suFadeUp .6s ease-out forwards; animation-delay: 7.0s;
    }
  `],
})
export class TeaserSceneSurfacesComponent {}
