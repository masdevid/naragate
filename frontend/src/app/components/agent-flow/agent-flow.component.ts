import { Component, Input, OnChanges, SimpleChanges, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';

interface AgentNode {
  id: string;
  label: string;
  shortLabel: string;
  status: 'idle' | 'active' | 'completed' | 'error';
  x: number;
  y: number;
}

interface DataPacket {
  id: number;
  from: string;
  to: string;
  progress: number;
  label: string;
  active: boolean;
  currentX: number;
  currentY: number;
}

@Component({
  selector: 'app-agent-flow',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="flow">
      <div class="flow__canvas">
        <svg class="flow__svg" viewBox="0 0 600 280" preserveAspectRatio="xMidYMid meet">
          <!-- Connection lines -->
          @for (conn of connections(); track conn.id) {
            <path
              [attr.d]="conn.path"
              class="flow__path"
              [class.flow__path--active]="conn.active"
              [class.flow__path--done]="conn.done"
              fill="none"
              stroke-width="2"
            />
          }

          <!-- Data packets -->
          @for (packet of packets(); track packet.id) {
            @if (packet.active) {
              <circle
                class="flow__packet"
                [attr.cx]="packet.currentX"
                [attr.cy]="packet.currentY"
                r="4"
              />
              <text
                class="flow__packet-label"
                [attr.x]="packet.currentX"
                [attr.y]="packet.currentY - 10"
                text-anchor="middle"
              >{{ packet.label }}</text>
            }
          }

          <!-- Agent nodes -->
          @for (agent of agents(); track agent.id) {
            <g [attr.transform]="'translate(' + agent.x + ',' + agent.y + ')'">
              <circle
                class="flow__node"
                [class.flow__node--active]="agent.status === 'active'"
                [class.flow__node--done]="agent.status === 'completed'"
                [class.flow__node--error]="agent.status === 'error'"
                r="28"
              />
              @if (agent.status === 'active') {
                <circle class="flow__pulse" r="28" />
              }
              <text class="flow__icon" text-anchor="middle" dy="1">
                {{ getAgentIcon(agent.id) }}
              </text>
              <text class="flow__label" text-anchor="middle" dy="46">
                {{ agent.shortLabel }}
              </text>
            </g>
          }
        </svg>
      </div>

      @if (currentMessage()) {
        <div class="flow__message">
          <span class="flow__message-agent">{{ currentMessage()?.agent }}</span>
          <span class="flow__message-text">{{ currentMessage()?.text }}</span>
        </div>
      }
    </div>
  `,
  styles: [`
    .flow {
      width: 100%;
    }
    .flow__canvas {
      width: 100%;
      max-width: 600px;
      margin: 0 auto;
    }
    .flow__svg {
      width: 100%;
      height: auto;
    }
    .flow__path {
      stroke: var(--color-paper-3);
      stroke-dasharray: 4 4;
    }
    .flow__path--active {
      stroke: var(--color-accent);
      stroke-dasharray: none;
      animation: flowPulse 1.5s ease-in-out infinite;
    }
    .flow__path--done {
      stroke: var(--color-success);
      stroke-dasharray: none;
    }
    .flow__node {
      fill: var(--color-paper-2);
      stroke: var(--color-paper-3);
      stroke-width: 2;
      transition: all var(--dur-short) var(--ease-out);
    }
    .flow__node--active {
      fill: var(--color-accent);
      stroke: var(--color-accent);
    }
    .flow__node--done {
      fill: var(--color-success);
      stroke: var(--color-success);
    }
    .flow__node--error {
      fill: var(--color-danger);
      stroke: var(--color-danger);
    }
    .flow__pulse {
      fill: var(--color-accent);
      opacity: 0.3;
      animation: pulse 2s ease-in-out infinite;
    }
    .flow__icon {
      fill: var(--color-ink);
      font-size: 16px;
      dominant-baseline: central;
    }
    .flow__node--active .flow__icon,
    .flow__node--done .flow__icon {
      fill: var(--color-paper);
    }
    .flow__label {
      fill: var(--color-muted);
      font-family: var(--font-mono);
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .flow__node--active + .flow__pulse ~ .flow__label,
    .flow__label:has(+ .flow__node--active) {
      fill: var(--color-ink);
    }
    .flow__packet {
      fill: var(--color-accent);
      filter: drop-shadow(0 0 4px var(--color-accent));
    }
    .flow__packet-label {
      fill: var(--color-muted);
      font-family: var(--font-mono);
      font-size: 8px;
    }
    .flow__message {
      display: flex;
      align-items: center;
      gap: var(--space-sm);
      padding: var(--space-sm) var(--space-md);
      background: var(--color-paper-2);
      border-left: 2px solid var(--color-accent);
      margin-top: var(--space-md);
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      animation: fadeIn var(--dur-short) var(--ease-out);
    }
    .flow__message-agent {
      color: var(--color-accent);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      white-space: nowrap;
    }
    .flow__message-text {
      color: var(--color-muted);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    @keyframes pulse {
      0%, 100% { transform: scale(1); opacity: 0.3; }
      50% { transform: scale(1.3); opacity: 0; }
    }
    @keyframes flowPulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(-4px); }
      to { opacity: 1; transform: none; }
    }

    @media (prefers-reduced-motion: reduce) {
      .flow__pulse, .flow__path--active { animation: none; }
      .flow__message { animation: none; }
    }
  `],
})
export class AgentFlowComponent implements OnChanges {
  @Input() currentStep = '';
  @Input() completedSteps: string[] = [];

  currentMessage = signal<{ agent: string; text: string } | null>(null);

  private agentDefs: AgentNode[] = [
    { id: 'claim_parsing', label: 'Claim Parser', shortLabel: 'Parser', status: 'idle', x: 75, y: 140 },
    { id: 'evidence_fetching', label: 'Evidence Fetcher', shortLabel: 'Evidence', status: 'idle', x: 200, y: 140 },
    { id: 'skeptic_analysis', label: 'Skeptic', shortLabel: 'Skeptic', status: 'idle', x: 325, y: 140 },
    { id: 'judge_assessment', label: 'Judge', shortLabel: 'Judge', status: 'idle', x: 450, y: 140 },
    { id: 'score_computing', label: 'Score Computer', shortLabel: 'Score', status: 'idle', x: 575, y: 140 },
  ];

  private packetId = 0;
  private activePackets: DataPacket[] = [];

  agents = signal<AgentNode[]>([]);
  packets = signal<DataPacket[]>([]);

  connections = computed(() => {
    const agentList = this.agents();
    const conns = [];
    for (let i = 0; i < agentList.length - 1; i++) {
      const from = agentList[i];
      const to = agentList[i + 1];
      const isActive = from.status === 'active' || (from.status === 'completed' && to.status === 'active');
      const isDone = from.status === 'completed' && to.status === 'completed';
      conns.push({
        id: `${from.id}-${to.id}`,
        path: `M${from.x + 28},${from.y} L${to.x - 28},${to.y}`,
        active: isActive,
        done: isDone,
      });
    }
    return conns;
  });

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['currentStep'] || changes['completedSteps']) {
      this.updateAgents();
    }
  }

  private updateAgents(): void {
    const step = this.currentStep;
    const completed = this.completedSteps;

    const updated = this.agentDefs.map(agent => {
      let status: AgentNode['status'] = 'idle';
      if (completed.includes(agent.id)) {
        status = 'completed';
      } else if (step === agent.id) {
        status = 'active';
      }
      return { ...agent, status };
    });

    this.agents.set(updated);

    const activeAgent = updated.find(a => a.status === 'active');
    if (activeAgent) {
      this.updateMessage(activeAgent.id);
      this.spawnPacket(activeAgent.id);
    }
  }

  private updateMessage(step: string): void {
    const messages: Record<string, { agent: string; text: string }> = {
      claim_parsing: { agent: 'Parser', text: 'Extracting structured claims from narrative...' },
      evidence_fetching: { agent: 'Evidence', text: 'Querying Sectors v2 API for financial data...' },
      skeptic_analysis: { agent: 'Skeptic', text: 'Challenging claim with counter-evidence...' },
      judge_assessment: { agent: 'Judge', text: 'Weighing evidence against narrative...' },
      score_computing: { agent: 'Score', text: 'Computing Reality Gap Score...' },
    };
    this.currentMessage.set(messages[step] || null);
  }

  private spawnPacket(fromStep: string): void {
    const stepOrder = ['claim_parsing', 'evidence_fetching', 'skeptic_analysis', 'judge_assessment', 'score_computing'];
    const idx = stepOrder.indexOf(fromStep);
    if (idx < 0 || idx >= stepOrder.length - 1) return;

    const fromAgent = this.agentDefs[idx];
    const toAgent = this.agentDefs[idx + 1];

    const packetLabels = ['claims', 'evidence', 'challenges', 'assessment'];
    const packet: DataPacket = {
      id: this.packetId++,
      from: fromStep,
      to: stepOrder[idx + 1],
      progress: 0,
      label: packetLabels[idx] || 'data',
      active: true,
      currentX: fromAgent.x + 28,
      currentY: fromAgent.y,
    };

    this.activePackets.push(packet);
    this.animatePacket(packet, fromAgent, toAgent);
  }

  private animatePacket(packet: DataPacket, from: AgentNode, to: AgentNode): void {
    const duration = 800;
    const start = performance.now();

    const animate = (now: number) => {
      const elapsed = now - start;
      const t = Math.min(elapsed / duration, 1);
      const eased = t < 0.5
        ? 4 * t * t * t
        : 1 - Math.pow(-2 * t + 2, 3) / 2;

      const startX = from.x + 28;
      const endX = to.x - 28;
      const currentX = startX + (endX - startX) * eased;
      const currentY = from.y + Math.sin(eased * Math.PI) * -8;

      const idx = this.activePackets.findIndex(p => p.id === packet.id);
      if (idx >= 0) {
        this.activePackets[idx] = {
          ...this.activePackets[idx],
          progress: t,
          currentX,
          currentY,
        };
        this.packets.set([...this.activePackets]);
      }

      if (t < 1) {
        requestAnimationFrame(animate);
      } else {
        const idx = this.activePackets.findIndex(p => p.id === packet.id);
        if (idx >= 0) {
          this.activePackets[idx] = { ...this.activePackets[idx], active: false };
          this.packets.set(this.activePackets.filter(p => p.active));
        }
      }
    };

    requestAnimationFrame(animate);
  }

  getAgentIcon(id: string): string {
    const icons: Record<string, string> = {
      claim_parsing: '\u270E',
      evidence_fetching: '\u{1F50D}',
      skeptic_analysis: '\u{1F440}',
      judge_assessment: '\u2696',
      score_computing: '\u{1F4CA}',
    };
    return icons[id] || '\u2022';
  }
}
