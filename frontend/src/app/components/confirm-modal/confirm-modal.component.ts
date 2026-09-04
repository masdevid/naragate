import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-confirm-modal',
  standalone: true,
  template: `
    <div class="modal" role="dialog" aria-modal="true">
      <div class="modal__overlay" (click)="cancel()"></div>
      <div class="modal__dialog">
        <h3 class="modal__title">{{ title }}</h3>
        <p class="modal__message">{{ message }}</p>
        <div class="modal__actions">
          <button class="modal__btn modal__btn--ghost" (click)="cancel()">{{ cancelLabel }}</button>
          <button class="modal__btn modal__btn--danger" (click)="confirm()">{{ confirmLabel }}</button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .modal {
      position: fixed;
      inset: 0;
      z-index: var(--z-modal);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: var(--space-md);
    }
    .modal__overlay {
      position: absolute;
      inset: 0;
      background: oklch(0% 0 0 / 0.6);
      animation: fade var(--dur-short) var(--ease-out);
    }
    .modal__dialog {
      position: relative;
      background: var(--color-paper-2);
      border: 1px solid var(--color-rule);
      max-width: 26rem;
      width: 100%;
      padding: var(--space-xl);
      animation: rise var(--dur-short) var(--ease-out);
    }
    .modal__title {
      font-family: var(--font-display);
      font-size: var(--text-md);
      text-transform: uppercase;
      letter-spacing: 0.02em;
      color: var(--color-ink);
      margin-bottom: var(--space-md);
    }
    .modal__message {
      font-size: var(--text-sm);
      color: var(--color-muted);
      line-height: 1.55;
      margin-bottom: var(--space-xl);
    }
    .modal__actions {
      display: flex;
      justify-content: flex-end;
      gap: var(--space-sm);
    }
    .modal__btn {
      padding: var(--space-sm) var(--space-lg);
      border: none;
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      cursor: pointer;
      transition: opacity var(--dur-short) var(--ease-out);
    }
    .modal__btn:hover { opacity: 0.85; }
    .modal__btn--ghost {
      background: none;
      border: 1px solid var(--color-rule);
      color: var(--color-muted);
    }
    .modal__btn--danger {
      background: var(--color-danger);
      color: var(--color-paper);
    }
    @keyframes fade { from { opacity: 0; } }
    @keyframes rise { from { opacity: 0; transform: translateY(8px); } }
  `],
})
export class ConfirmModalComponent {
  @Input() title = '';
  @Input() message = '';
  @Input() confirmLabel = 'Delete';
  @Input() cancelLabel = 'Cancel';
  @Output() confirmed = new EventEmitter<void>();
  @Output() cancelled = new EventEmitter<void>();

  confirm() { this.confirmed.emit(); }
  cancel() { this.cancelled.emit(); }
}