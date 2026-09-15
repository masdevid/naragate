import { Component, Input } from '@angular/core';

/* Hallmark · component: process-loader · genre: editorial · theme: token-native (dark paper · accent 35°)
 * states: idle · active · completed · error · reduced-motion · contrast: pass
 * pre-emit critique: P4 H5 E4 S4 R4 V4
 */

interface CircuitAgent {
  id: string;
  short: string;
  icon: string;
  color: string;
}

/**
 * Agentic circuit-board loader. Each agent is a block on a bus; a signal pulses
 * along the trace as the pipeline hands off between agents. Every block owns a
 * distinct hue and shows a check badge once its stage has completed.
 */
@Component({
  selector: 'app-agent-circuit',
  standalone: true,
  template: `
    <div class="circuit" role="status" [attr.aria-label]="statusLabel()">
      <div class="circuit__board">
        <div class="circuit__track">
          @for (agent of agents; track agent.id; let i = $index; let last = $last) {
            <div
              class="circuit__block"
              [style.--agent]="agent.color"
              [class.is-active]="statusOf(agent.id) === 'active'"
              [class.is-done]="statusOf(agent.id) === 'completed'"
              [class.is-error]="statusOf(agent.id) === 'error'">
              <span class="circuit__node" aria-hidden="true">{{ agent.icon }}</span>
              <span class="circuit__label">{{ agent.short }}</span>
              @if (statusOf(agent.id) === 'completed') {
                <span class="circuit__check" aria-hidden="true">&#10003;</span>
              }
              @if (statusOf(agent.id) === 'active') {
                <span class="circuit__ping" aria-hidden="true"></span>
              }
            </div>
            @if (!last) {
              <div
                class="circuit__trace"
                [style.--agent]="agents[i + 1].color"
                [class.is-active]="traceActive(i)"
                [class.is-done]="traceDone(i)">
                <span class="circuit__via" aria-hidden="true"></span>
                @if (traceActive(i)) {
                  <span class="circuit__pulse" aria-hidden="true"></span>
                }
              </div>
            }
          }
        </div>
      </div>
      @if (statusMessage(); as message) {
        <p class="circuit__status">{{ message }}</p>
      }
    </div>
  `,
  styles: [`
    :host {
      /* Component tokens for the two hues the base palette lacks. */
      --circuit-cyan: oklch(70% 0.13 220);
      --circuit-violet: oklch(68% 0.17 300);
      display: block;
    }
    .circuit { width: 100%; }
    .circuit__board {
      padding: var(--space-lg) var(--space-md);
      background: var(--color-paper-2);
      border: 1px solid var(--color-rule);
    }
    .circuit__track {
      display: flex;
      align-items: stretch;
    }
    .circuit__block {
      position: relative;
      flex: 1 1 0;
      min-width: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: var(--space-2xs);
      padding: var(--space-sm) var(--space-xs);
      background: var(--color-paper);
      border: 1px solid var(--color-rule);
      transition: border-color var(--dur-short) var(--ease-out), box-shadow var(--dur-short) var(--ease-out);
    }
    .circuit__node {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 1.75rem;
      height: 1.75rem;
      font-size: var(--text-sm);
      line-height: 1;
      color: var(--color-dim);
      background: var(--color-paper-2);
      border: 1px solid var(--color-rule);
      transition: color var(--dur-short) var(--ease-out), background var(--dur-short) var(--ease-out), border-color var(--dur-short) var(--ease-out);
    }
    .circuit__label {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--color-dim);
    }
    .circuit__check {
      position: absolute;
      top: -0.5rem;
      right: -0.5rem;
      width: 1rem;
      height: 1rem;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: var(--text-xs);
      line-height: 1;
      color: var(--color-paper);
      background: var(--agent);
      border-radius: 999px;
    }
    .circuit__ping {
      position: absolute;
      inset: 0;
      border: 1px solid var(--agent);
      animation: circuitPing 1.6s var(--ease-out) infinite;
    }
    .circuit__block.is-active {
      border-color: var(--agent);
      box-shadow: 0 0 0 1px var(--agent), 0 0 12px -3px var(--agent);
    }
    .circuit__block.is-active .circuit__node { color: var(--agent); border-color: var(--agent); }
    .circuit__block.is-active .circuit__label { color: var(--color-ink); }
    .circuit__block.is-done { border-color: var(--agent); }
    .circuit__block.is-done .circuit__node {
      color: var(--color-paper);
      background: var(--agent);
      border-color: var(--agent);
    }
    .circuit__block.is-done .circuit__label { color: var(--color-muted); }
    .circuit__block.is-error { border-color: var(--color-danger); }
    .circuit__block.is-error .circuit__node { color: var(--color-danger); border-color: var(--color-danger); }
    .circuit__trace {
      position: relative;
      flex: 0 1 2.5rem;
      min-width: 1.25rem;
      align-self: center;
      height: 2px;
      background: var(--color-rule);
    }
    .circuit__trace.is-active { background: linear-gradient(90deg, var(--color-rule), var(--agent)); }
    .circuit__trace.is-done { background: var(--agent); }
    .circuit__via {
      position: absolute;
      top: 50%;
      left: 50%;
      width: 6px;
      height: 6px;
      margin: -3px 0 0 -3px;
      border-radius: 50%;
      background: var(--color-paper-2);
      border: 1px solid var(--color-rule);
    }
    .circuit__trace.is-done .circuit__via { background: var(--agent); border-color: var(--agent); }
    .circuit__pulse {
      position: absolute;
      top: 50%;
      left: 0;
      width: 8px;
      height: 8px;
      margin-top: -4px;
      border-radius: 50%;
      background: var(--agent);
      box-shadow: 0 0 8px var(--agent);
      animation: circuitFlow 1.1s linear infinite;
    }
    .circuit__status {
      margin: var(--space-sm) 0 0;
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--color-muted);
    }
    @keyframes circuitFlow {
      0% { left: 0; opacity: 0; }
      15% { opacity: 1; }
      100% { left: 100%; opacity: 0; }
    }
    @keyframes circuitFlowY {
      0% { top: 0; opacity: 0; }
      15% { opacity: 1; }
      100% { top: 100%; opacity: 0; }
    }
    @keyframes circuitPing {
      0% { transform: scale(1); opacity: 0.5; }
      100% { transform: scale(1.35); opacity: 0; }
    }
    @media (max-width: 640px) {
      .circuit__track { flex-direction: column; }
      .circuit__block {
        flex-direction: row;
        justify-content: flex-start;
        gap: var(--space-sm);
        padding: var(--space-sm);
      }
      .circuit__trace {
        flex: 0 0 auto;
        width: 2px;
        min-width: 0;
        height: 1.5rem;
        margin: 0 auto;
      }
      .circuit__pulse {
        left: 50%;
        top: 0;
        margin-top: 0;
        margin-left: -4px;
        animation-name: circuitFlowY;
      }
    }
    @media (prefers-reduced-motion: reduce) {
      .circuit__pulse, .circuit__ping { animation: none; }
      .circuit__pulse { opacity: 0.9; }
    }
  `],
})
export class AgentCircuitComponent {
  @Input() currentStep = '';
  @Input() completedSteps: string[] = [];
  @Input() errorStep = '';

  readonly agents: CircuitAgent[] = [
    { id: 'claim_parsing', short: 'Parser', icon: '\u270E', color: 'var(--color-accent)' },
    { id: 'evidence_fetching', short: 'Evidence', icon: '\u2315', color: 'var(--circuit-cyan)' },
    { id: 'skeptic_analysis', short: 'Skeptic', icon: '\u25C9', color: 'var(--color-warning)' },
    { id: 'judge_assessment', short: 'Judge', icon: '\u2696', color: 'var(--circuit-violet)' },
    { id: 'score_computing', short: 'Score', icon: '\u25A4', color: 'var(--color-success)' },
  ];

  private readonly messages: Record<string, string> = {
    claim_parsing: 'Extracting structured claims from the narrative\u2026',
    evidence_fetching: 'Querying Sectors v2 for financial evidence\u2026',
    skeptic_analysis: 'Challenging the claim with counter-evidence\u2026',
    judge_assessment: 'Weighing evidence against the narrative\u2026',
    score_computing: 'Computing the Reality Gap Score\u2026',
  };

  statusOf(id: string): 'idle' | 'active' | 'completed' | 'error' {
    if (this.errorStep === id) return 'error';
    if (this.completedSteps.includes(id)) return 'completed';
    if (this.currentStep === id) return 'active';
    return 'idle';
  }

  traceDone(index: number): boolean {
    return this.statusOf(this.agents[index].id) === 'completed'
      && this.statusOf(this.agents[index + 1].id) === 'completed';
  }

  traceActive(index: number): boolean {
    const from = this.statusOf(this.agents[index].id);
    const to = this.statusOf(this.agents[index + 1].id);
    return from === 'active' || to === 'active';
  }

  statusMessage(): string | null {
    return this.messages[this.currentStep] ?? null;
  }

  statusLabel(): string {
    const active = this.agents.find(a => this.statusOf(a.id) === 'active');
    return active ? `Pipeline: ${active.short} running` : 'Pipeline status';
  }
}
