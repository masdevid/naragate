import { Component, Input, Output, EventEmitter, signal, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-masked-key-input',
  standalone: true,
  imports: [FormsModule],
  template: `
    <input
      [ngModel]="display()"
      (ngModelChange)="onInput($event)"
      (focus)="onFocus()"
      (blur)="onBlur()"
      type="text"
      spellcheck="false"
      autocomplete="off"
      [placeholder]="placeholder"
      [class]="inputClass"
      [attr.aria-label]="placeholder">
  `,
})
export class MaskedKeyInputComponent {
  @Input() placeholder = '';
  @Input() inputClass = '';
  @Output() valueChange = new EventEmitter<string>();

  private _value = '';
  display = signal('');
  private focused = false;

  @Input() set value(v: string | undefined | null) {
    this._value = v || '';
    if (!this.focused) this.display.set(this.mask(this._value));
  }

  get value(): string {
    return this._value;
  }

  onFocus() {
    this.focused = true;
    this.display.set(this._value);
  }

  onBlur() {
    this.focused = false;
    this.display.set(this.mask(this._value));
  }

  onInput(v: string) {
    this._value = v;
    this.valueChange.emit(v);
    this.display.set(this.focused ? v : this.mask(v));
  }

  private mask(value: string): string {
    if (!value) return '';
    if (value.length <= 4) return value;
    return value.slice(0, 2) + '••••••' + value.slice(-2);
  }
}