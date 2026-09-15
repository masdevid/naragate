export const NARRATIVE_MAX_LENGTH = 4000;

// C0/C1 control characters except tab/newline/carriage-return.
const CONTROL_CHARS = /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g;

/**
 * Harden a user-supplied narrative before it is sent or rendered.
 *
 * Angular escapes interpolation by default (no `innerHTML` sinks in the app),
 * so this is defence-in-depth: drops control characters and caps length.
 * The text is never treated as HTML.
 */
export function sanitizeNarrative(input: string, maxLength = NARRATIVE_MAX_LENGTH): string {
  return (input ?? '').replace(CONTROL_CHARS, '').slice(0, maxLength).trim();
}
