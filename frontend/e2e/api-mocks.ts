// Shared SSE + claim payload builders for the analysis edge-case e2e suite.

export function sseChunk(eventType: string, data: any): string {
  return `event: ${eventType}\ndata: ${JSON.stringify(data)}\n\n`;
}

export function pipelineEvent(eventType: string, claimId: string, data: any): any {
  return {
    event_type: eventType,
    claim_id: claimId,
    data,
    timestamp: new Date().toISOString(),
  };
}

export function claimParsedEvent(claimId: string, claim: any): string {
  return sseChunk('claim_parsed', pipelineEvent('claim_parsed', claimId, claim));
}

// A full success stream the frontend recognizes as a completed analysis.
export function successStream(claimId: string, narrative: string): string {
  const body = [
    sseChunk('pipeline_started', pipelineEvent('pipeline_started', claimId, { narrative })),
    sseChunk('claim_parsing', pipelineEvent('claim_parsing', claimId, { stage: 'claim_parser' })),
    claimParsedEvent(claimId, {
      ticker: 'BBCA',
      category: 'valuation',
      assertion: 'Harga saham di atas nilai wajar',
      direction: 'above',
      confidence: 0.9,
      ticker_valid: true,
    }),
    sseChunk('evidence_fetching', pipelineEvent('evidence_fetching', claimId, { ticker: 'BBCA', category: 'valuation' })),
    sseChunk('evidence_ready', pipelineEvent('evidence_ready', claimId, {
      valuation: {
        claim_ticker: 'BBCA',
        category: 'valuation',
        metrics: { pe: 18.2, pb: 4.1 },
        subsector_median: { pe: 20.1, pb: 3.2 },
        premium_pct: { pe: -9.5, pb: 28.1 },
        evidence_freshness: '2026-09-07',
        cache_hit: true,
      },
    })),
    sseChunk('skeptic_analysis', pipelineEvent('skeptic_analysis', claimId, { stage: 'skeptic' })),
    sseChunk('skeptic_ready', pipelineEvent('skeptic_ready', claimId, {
      claim_ticker: 'BBCA',
      counter_arguments: [],
      ambiguity_points: [],
      missing_evidence: [],
      skepticism_score: 55,
    })),
    sseChunk('judge_assessment', pipelineEvent('judge_assessment', claimId, { stage: 'judge' })),
    sseChunk('assessment_ready', pipelineEvent('assessment_ready', claimId, { assessment: 'aligned', confidence: 0.7 })),
    sseChunk('score_computing', pipelineEvent('score_computing', claimId, { stage: 'scorer' })),
    sseChunk('score_computed', pipelineEvent('score_computed', claimId, {
      reality_gap_score: 72,
      verdict: 'supported',
      dimensions: { valuation_gap: 30, evidence_confidence: 80 },
      explanation: 'Bukti valuasi mendukung klaim.',
    })),
    sseChunk('pipeline_complete', pipelineEvent('pipeline_complete', claimId, {
      duration_ms: 1500,
      verdict: 'supported',
      score: 72,
    })),
  ];
  return body.join('');
}

// Stream that models the ticker guardrail: no valid ticker -> clarification.
export function clarificationStream(claimId: string, narrative: string): string {
  const body = [
    sseChunk('pipeline_started', pipelineEvent('pipeline_started', claimId, { narrative })),
    sseChunk('claim_parsing', pipelineEvent('claim_parsing', claimId, { stage: 'claim_parser' })),
    claimParsedEvent(claimId, {
      ticker: 'UNKNOWN',
      category: 'valuation',
      assertion: 'Saham perbankan mahal',
      direction: 'above',
      confidence: 0.5,
      ticker_valid: false,
      needs_clarification: true,
      missing: ['ticker'],
      reason: 'No valid 4-letter ticker identified in the narrative',
    }),
    sseChunk('clarification_required', pipelineEvent('clarification_required', claimId, {
      claim_id: claimId,
      missing: ['ticker'],
      reason: 'No valid 4-letter ticker identified in the narrative',
      message: 'Tidak dapat mengidentifikasi kode saham dari narasi. Mohon berikan ticker saham untuk dianalisis.',
    })),
  ];
  return body.join('');
}

export function claimState(overrides: Record<string, any> = {}): any {
  return {
    claim_id: 'stuck-claim',
    narrative: 'Saham UNVR turun 15% dalam seminggu, investor panik.',
    status: 'parsed',
    created_at: '2026-09-08T07:23:02.866054',
    updated_at: '2026-09-08T07:23:10.795340',
    claim: {
      ticker: 'UNVR',
      category: 'market',
      assertion: 'Harga saham turun 15% dalam sepekan',
      direction: 'below',
      confidence: 0.9,
      ticker_valid: true,
    },
    ...overrides,
  };
}