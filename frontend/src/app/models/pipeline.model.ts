export interface Claim {
  claim_id?: string;
  ticker: string;
  category: 'valuation' | 'fundamental' | 'market' | 'peer_comparison';
  assertion: string;
  direction: 'above' | 'below' | 'between' | 'neutral';
  time_window?: string;
  magnitude?: number;
  confidence: number;
  ticker_valid: boolean;
  narrative_source?: string;
}

export interface ValuationEvidence {
  claim_ticker: string;
  category: string;
  metrics: { pe?: number; pb?: number; ps?: number; pcf?: number };
  subsector_median: { pe?: number; pb?: number; ps?: number };
  premium_pct: { pe?: number; pb?: number; ps?: number };
  evidence_freshness: string;
  cache_hit: boolean;
}

export interface FundamentalEvidence {
  claim_ticker: string;
  category: string;
  metrics: {
    revenue?: number; earnings?: number; eps?: number;
    gross_margin?: number; roe?: number; roa?: number; debt_to_equity?: number;
  };
  trend: { revenue_trend: string; earnings_trend: string; quarters_analyzed: number };
  evidence_freshness: string;
  cache_hit: boolean;
}

export interface MarketEvidence {
  claim_ticker: string;
  category: string;
  performance: {
    '1d'?: { price_change_pct: number; volume: number };
    '7d'?: { price_change_pct: number; volume: number };
    '30d'?: { price_change_pct: number; volume: number };
  };
  volatility: number;
  evidence_freshness: string;
  cache_hit: boolean;
}

export interface SkepticOutput {
  claim_ticker: string;
  counter_arguments: { point: string; evidence_ref: string; strength: number }[];
  ambiguity_points: string[];
  missing_evidence: string[];
  skepticism_score: number;
}

export interface EvidenceAssessment {
  claim_ticker: string;
  claim_category: string;
  evidence_summary: { valuation?: ValuationEvidence; fundamental?: FundamentalEvidence; market?: MarketEvidence };
  contradictions: string[];
  skeptic_challenges: string[];
  evidence_confidence: number;
  applicable_dimensions: string[];
}

export interface RealityGapScore {
  claim_ticker: string;
  claim_category: string;
  reality_gap_score: number;
  verdict: 'contradicted' | 'mixed' | 'supported' | 'strongly_supported';
  dimensions: Record<string, number>;
  explanation: string;
  confidence: number;
}

export interface PipelineEvent {
  event_type: string;
  claim_id: string;
  data: any;
  timestamp: string;
}
