import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { TPipe } from '../../pipes/t.pipe';

/* Hallmark · page: not-found · genre: editorial · theme: studied (Naragate tokens)
 * macrostructure: single-focus recovery · nav: none (app shell) · footer: none (app shell)
 * enrichment: none (typography only)
 * pre-emit critique: P5 H5 E5 S4 R5 V4
 */

@Component({
  selector: 'app-not-found',
  standalone: true,
  imports: [RouterLink, TPipe],
  template: `
    <section class="nf">
      <p class="nf__eyebrow">{{ 'notfound.eyebrow' | t }}</p>

      <h1 class="nf__title">{{ 'notfound.title' | t }}</h1>

      <p class="nf__sub">{{ 'notfound.sub' | t }}</p>

      <p class="nf__path">
        <span class="nf__path-label">{{ 'notfound.path' | t }}</span>
        <code>{{ path() }}</code>
      </p>

      <div class="nf__actions">
        <a routerLink="/dashboard" class="nf__btn nf__btn--primary">{{ 'notfound.home' | t }}</a>
        <button type="button" class="nf__btn nf__btn--ghost" (click)="goBack()">{{ 'notfound.back' | t }}</button>
      </div>

      <p class="nf__countdown" aria-live="polite">
        {{ 'notfound.redirecting' | t }} <span class="nf__count">{{ seconds() }}</span>s
        &middot;
        <button type="button" class="nf__link" (click)="goHome()">{{ 'notfound.now' | t }}</button>
      </p>
    </section>
  `,
  styles: [`
    :host { display: block; }
    .nf {
      max-width: 46rem;
      margin: 0 auto;
      padding: clamp(var(--space-2xl), 10vh, var(--space-4xl)) var(--space-lg) var(--space-3xl);
      display: flex;
      flex-direction: column;
      align-items: flex-start;
    }
    .nf__eyebrow {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--color-accent);
      margin-bottom: var(--space-md);
    }
    .nf__title {
      font-family: var(--font-display);
      font-style: normal;
      font-weight: 400;
      font-size: var(--text-display);
      line-height: 0.98;
      letter-spacing: 0.01em;
      text-transform: uppercase;
      color: var(--color-ink);
      overflow-wrap: anywhere;
      min-width: 0;
      margin-bottom: var(--space-lg);
    }
    .nf__sub {
      font-family: var(--font-body);
      font-size: var(--text-md);
      line-height: 1.55;
      color: var(--color-muted);
      max-width: 34rem;
      margin-bottom: var(--space-lg);
    }
    .nf__path {
      display: flex;
      flex-wrap: wrap;
      align-items: baseline;
      gap: var(--space-xs);
      font-size: var(--text-sm);
      margin-bottom: var(--space-xl);
    }
    .nf__path-label {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--color-dim);
    }
    .nf__path code {
      font-family: var(--font-mono);
      color: var(--color-ink);
      background: var(--color-paper-2);
      border: 1px solid var(--color-rule);
      padding: var(--space-3xs) var(--space-xs);
      overflow-wrap: anywhere;
      min-width: 0;
    }
    .nf__actions {
      display: flex;
      flex-wrap: wrap;
      gap: var(--space-sm);
      margin-bottom: var(--space-xl);
    }
    .nf__btn {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      padding: var(--space-sm) var(--space-lg);
      white-space: nowrap;
      cursor: pointer;
      transition: opacity var(--dur-short) var(--ease-out), border-color var(--dur-short) var(--ease-out);
    }
    .nf__btn--primary {
      background: var(--color-accent);
      color: var(--color-paper);
      border: 1px solid var(--color-accent);
      text-decoration: none;
    }
    .nf__btn--primary:hover { opacity: 0.9; }
    .nf__btn--ghost {
      background: none;
      color: var(--color-ink);
      border: 1px solid var(--color-rule);
    }
    .nf__btn--ghost:hover { border-color: var(--color-ink); }
    .nf__btn:focus-visible,
    .nf__link:focus-visible {
      outline: 2px solid var(--color-focus);
      outline-offset: 2px;
    }
    .nf__countdown {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-dim);
    }
    .nf__count { color: var(--color-accent); }
    .nf__link {
      background: none;
      border: none;
      padding: 0;
      color: var(--color-accent);
      font: inherit;
      text-decoration: underline;
      cursor: pointer;
    }
  `],
})
export class NotFoundComponent implements OnInit, OnDestroy {
  private router = inject(Router);

  readonly path = signal('/');
  readonly seconds = signal(8);

  private timer: ReturnType<typeof setInterval> | null = null;

  ngOnInit() {
    this.path.set(this.router.url);
    this.timer = setInterval(() => {
      const next = this.seconds() - 1;
      if (next <= 0) {
        this.goHome();
        return;
      }
      this.seconds.set(next);
    }, 1000);
  }

  ngOnDestroy() {
    if (this.timer) clearInterval(this.timer);
  }

  goHome() {
    if (this.timer) { clearInterval(this.timer); this.timer = null; }
    this.router.navigate(['/dashboard']);
  }

  goBack() {
    if (this.timer) { clearInterval(this.timer); this.timer = null; }
    if (window.history.length > 1) {
      window.history.back();
    } else {
      this.router.navigate(['/dashboard']);
    }
  }
}
