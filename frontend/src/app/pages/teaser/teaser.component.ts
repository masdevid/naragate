import { Component, OnDestroy, OnInit, computed, signal } from '@angular/core';
import { TPipe } from '../../pipes/t.pipe';
import { TeaserSceneHookComponent } from '../../components/teaser/teaser-scene-hook.component';
import { TeaserSceneEvidenceComponent } from '../../components/teaser/teaser-scene-evidence.component';
import { TeaserScenePersonasComponent } from '../../components/teaser/teaser-scene-personas.component';
import { TeaserScenePolicyComponent } from '../../components/teaser/teaser-scene-policy.component';
import { TeaserSceneSurfacesComponent } from '../../components/teaser/teaser-scene-surfaces.component';
import { TeaserSceneCtaComponent } from '../../components/teaser/teaser-scene-cta.component';

interface TeaserScene {
  id: string;
  label: string;
  /** Per-scene timer in milliseconds (each scene can differ). */
  duration: number;
  tts: string;
}

const STAGE_W = 1280;
const STAGE_H = 720;

@Component({
  selector: 'app-teaser',
  standalone: true,
  imports: [
    TPipe,
    TeaserSceneHookComponent,
    TeaserSceneEvidenceComponent,
    TeaserScenePersonasComponent,
    TeaserScenePolicyComponent,
    TeaserSceneSurfacesComponent,
    TeaserSceneCtaComponent,
  ],
  template: `
    <div class="teaser">
      <div class="teaser__frame" [style.width.px]="STAGE_W * scale()" [style.height.px]="STAGE_H * scale()">
        <div class="teaser__stage"
          [style.transform]="'scale(' + scale() + ')'"
          [style.width.px]="STAGE_W" [style.height.px]="STAGE_H">

          @switch (scenes[active()].id) {
            @case ('hook') { <app-teaser-scene-hook /> }
            @case ('evidence') { <app-teaser-scene-evidence /> }
            @case ('personas') { <app-teaser-scene-personas /> }
            @case ('policy') { <app-teaser-scene-policy /> }
            @case ('surfaces') { <app-teaser-scene-surfaces /> }
            @case ('cta') { <app-teaser-scene-cta /> }
          }

          @if (!started()) {
            <button class="teaser__start" (click)="start()">
              <span class="teaser__start-icon">▶</span>
              <span>{{ 'teaser.play' | t }}</span>
            </button>
          }
        </div>
      </div>

      <div class="teaser__controls">
        <button class="teaser__ctrl" (click)="prev()" [attr.aria-label]="'teaser.prev' | t">⏮</button>
        <button class="teaser__ctrl teaser__ctrl--main" (click)="toggle()" [attr.aria-label]="'teaser.play_pause' | t">
          {{ playing() ? '❚❚' : '▶' }}
        </button>
        <button class="teaser__ctrl" (click)="next()" [attr.aria-label]="'teaser.next' | t">⏭</button>

        <div class="teaser__dots">
          @for (scene of scenes; track scene.id; let i = $index) {
            <button class="teaser__dot" [class.teaser__dot--on]="i === active()"
              (click)="goTo(i)" [attr.aria-label]="scene.label"></button>
          }
        </div>

        <span class="teaser__time">{{ sceneLabel() }} · {{ active() + 1 }}/{{ scenes.length }}</span>
        <button class="teaser__ctrl" (click)="restart()" [attr.aria-label]="'teaser.restart' | t">↺</button>
      </div>

      <div class="teaser__bar"><div class="teaser__bar-fill" [style.width.%]="progress()"></div></div>
    </div>
  `,
  styles: [`
    :host { display: block; background: #000; min-height: 100vh; }
    .teaser {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: var(--space-md, 1rem);
      padding: var(--space-lg, 1.5rem);
      background: #000;
    }
    .teaser__frame { position: relative; max-width: 96vw; max-height: 82vh; }
    .teaser__stage {
      position: absolute;
      top: 0; left: 0;
      transform-origin: top left;
      overflow: hidden;
      /* Naragate teaser design tokens */
      --bg-deep:#0B0E17; --bg-panel:#141A26; --bg-panel-2:#1B2233;
      --line: rgba(255,255,255,.09);
      --text-primary:#F4F6FB; --text-muted:#8791A8;
      --brand-from:#E31C5F; --brand-to:#F5A623; --verified:#34D399;
      --font-display:'Space Grotesk', ui-sans-serif, system-ui, sans-serif;
      --font-mono:'IBM Plex Mono', ui-monospace, SFMono-Regular, monospace;
      background:
        radial-gradient(ellipse 900px 500px at 18% -8%, rgba(227,28,95,.16), transparent 55%),
        radial-gradient(ellipse 900px 500px at 102% 112%, rgba(245,166,35,.12), transparent 55%),
        var(--bg-deep);
      font-family: var(--font-mono);
      color: var(--text-primary);
    }
    .teaser__start {
      position: absolute; inset: 0; margin: auto;
      width: 220px; height: 220px; border-radius: 50%;
      border: 1px solid var(--line); background: rgba(20,26,38,.72);
      color: var(--text-primary); font-family: var(--font-display);
      font-size: 22px; cursor: pointer; display: flex;
      flex-direction: column; align-items: center; justify-content: center; gap: 10px;
      backdrop-filter: blur(4px); transition: transform .2s ease, border-color .2s ease;
    }
    .teaser__start:hover { transform: scale(1.04); border-color: var(--brand-to); }
    .teaser__start-icon { font-size: 40px; }
    .teaser__controls {
      display: flex; align-items: center; gap: var(--space-md, 1rem);
      font-family: ui-monospace, monospace; color: #8791A8;
    }
    .teaser__ctrl {
      background: none; border: 1px solid rgba(255,255,255,.12); color: #F4F6FB;
      width: 42px; height: 42px; border-radius: 50%; cursor: pointer; font-size: 14px;
    }
    .teaser__ctrl--main { width: 52px; height: 52px; }
    .teaser__ctrl:hover { border-color: #F5A623; }
    .teaser__dots { display: flex; gap: 8px; }
    .teaser__dot {
      width: 9px; height: 9px; border-radius: 50%; padding: 0;
      background: rgba(255,255,255,.18); border: none; cursor: pointer;
    }
    .teaser__dot--on { background: #F5A623; }
    .teaser__time { font-size: 12px; letter-spacing: .04em; }
    .teaser__bar { width: min(96vw, 1280px); height: 3px; background: rgba(255,255,255,.1); }
    .teaser__bar-fill { height: 100%; background: linear-gradient(90deg,#E31C5F,#F5A623); transition: width .1s linear; }
  `],
})
export class TeaserComponent implements OnInit, OnDestroy {
  readonly STAGE_W = STAGE_W;
  readonly STAGE_H = STAGE_H;

  readonly scenes: TeaserScene[] = [
    { id: 'hook', label: 'Masalah', duration: 10000, tts: 'Setiap hari, ribuan narasi pasar berseliweran—di WhatsApp, media sosial, berita. Tapi mana yang benar-benar sesuai data?' },
    { id: 'evidence', label: 'Naragate', duration: 10000, tts: 'Kenalkan Naragate. Ekstrak klaim, verifikasi ke data Sectors, dan hasilkan Reality Gap Score—skor celah realitas dari nol sampai seratus.' },
    { id: 'personas', label: 'Untuk siapa', duration: 10000, tts: 'Untuk investor ritel yang mau cek cepat, analis yang perlu verifikasi laporan, tim kepatuhan yang menyaring medsos, dan fund manager yang memantau risiko kebijakan.' },
    { id: 'policy', label: 'Policy Amplifier', duration: 10000, tts: 'Bahkan narasi kebijakan tanpa ticker, seperti HBA turun, otomatis dipetakan ke sektor yang tepat—dan dampaknya diukur secara real-time.' },
    { id: 'surfaces', label: 'Dua jalur akses', duration: 10000, tts: 'Akses dari mana saja—lewat web UI di naragate titik ilkomers titik com, atau langsung dari agent favoritmu lewat MCP server dan skills package.' },
    { id: 'cta', label: 'Coba sekarang', duration: 10000, tts: 'Naragate—verifikasi klaim, deteksi dampak kebijakan, skor celah realitas. Coba sekarang di naragate titik ilkomers titik com.' },
  ];

  readonly active = signal(0);
  readonly playing = signal(false);
  readonly started = signal(false);
  readonly progress = signal(0);
  readonly scale = signal(1);
  readonly sceneLabel = computed(() => this.scenes[this.active()].label);

  private advanceTimer: ReturnType<typeof setTimeout> | null = null;
  private rafId = 0;
  private sceneStartedAt = 0;
  private fontLink: HTMLLinkElement | null = null;
  private onResize = () => this.fit();

  ngOnInit() {
    this.injectFonts();
    this.fit();
    window.addEventListener('resize', this.onResize);
  }

  ngOnDestroy() {
    window.removeEventListener('resize', this.onResize);
    this.clearAdvance();
    cancelAnimationFrame(this.rafId);
    if ('speechSynthesis' in window) speechSynthesis.cancel();
    this.fontLink?.remove();
  }

  start() {
    this.started.set(true);
    this.playing.set(true);
    this.enterScene(0);
  }

  toggle() {
    if (!this.started()) { this.start(); return; }
    this.playing.update(p => !p);
    if (this.playing()) {
      if ('speechSynthesis' in window) speechSynthesis.resume();
      this.scheduleAdvance(this.scenes[this.active()].duration);
      this.sceneStartedAt = performance.now();
      this.tick();
    } else {
      this.clearAdvance();
      cancelAnimationFrame(this.rafId);
      if ('speechSynthesis' in window) speechSynthesis.pause();
    }
  }

  next() { this.goTo((this.active() + 1) % this.scenes.length); }
  prev() { this.goTo((this.active() - 1 + this.scenes.length) % this.scenes.length); }

  restart() {
    this.started.set(true);
    this.playing.set(true);
    this.enterScene(0);
  }

  goTo(index: number) {
    if (!this.started()) this.started.set(true);
    this.enterScene(index);
  }

  private enterScene(index: number) {
    this.active.set(index);
    this.progress.set(0);
    this.clearAdvance();
    cancelAnimationFrame(this.rafId);
    if ('speechSynthesis' in window) speechSynthesis.cancel();
    if (this.playing()) {
      this.speak(this.scenes[index].tts);
      this.scheduleAdvance(this.scenes[index].duration);
      this.sceneStartedAt = performance.now();
      this.tick();
    } else {
      this.progress.set(0);
    }
  }

  private scheduleAdvance(duration: number) {
    this.clearAdvance();
    this.advanceTimer = setTimeout(() => this.next(), duration);
  }

  private clearAdvance() {
    if (this.advanceTimer) { clearTimeout(this.advanceTimer); this.advanceTimer = null; }
  }

  private tick = () => {
    const duration = this.scenes[this.active()].duration;
    const elapsed = performance.now() - this.sceneStartedAt;
    this.progress.set(Math.min(100, (elapsed / duration) * 100));
    if (this.playing()) this.rafId = requestAnimationFrame(this.tick);
  };

  private speak(text: string) {
    try {
      const u = new SpeechSynthesisUtterance(text);
      u.lang = 'id-ID';
      u.rate = 0.97;
      speechSynthesis.speak(u);
    } catch { /* speech engine unavailable */ }
  }

  private fit() {
    const s = Math.min(1, (window.innerWidth * 0.96) / STAGE_W, (window.innerHeight * 0.82) / STAGE_H);
    this.scale.set(s);
  }

  private injectFonts() {
    const id = 'teaser-fonts';
    if (document.getElementById(id)) return;
    const link = document.createElement('link');
    link.id = id;
    link.rel = 'stylesheet';
    link.href = 'https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap';
    document.head.appendChild(link);
    this.fontLink = link;
  }
}
