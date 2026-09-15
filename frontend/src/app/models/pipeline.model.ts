export interface Claim {
  claim_id?: string;
  ticker: string;
  category: 'valuation' | 'fundamental' | 'market' | 'peer_comparison' | 'insider_trading';
  assertion: string;
  assertion_en?: string;
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
  metrics: { pe?: number; pb?: number; ps?: number; pcf?: number; forward_pe?: number };
  subsector_median: { pe?: number; pb?: number; ps?: number };
  premium_pct: { pe?: number; pb?: number; ps?: number };
  health?: { roe?: number; roa?: number; net_profit_margin?: number; nim?: number; npl?: number; loan_growth?: number };
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
  segments?: {
    financial_year?: number;
    top_sources: { source: string; value: number; share_pct: number }[];
  };
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
  foreign_flow?: unknown[] | Record<string, unknown>;
  broker_flow?: Record<string, unknown>;
  flow_summary?: {
    foreign_net?: number;
    foreign_bias?: 'net_inflow' | 'net_outflow' | 'balanced';
    broker_net?: number;
    broker_bias?: 'net_buy' | 'net_sell' | 'balanced';
  };
  market_movers?: {
    classification: 'top_gainers' | 'top_losers';
    period: string;
    rank: number;
    price_change?: number;
  };
  relative_strength?: { '1d'?: number; '7d'?: number; '30d'?: number };
}

export interface InsiderFiling {
  date: string;
  insider_name: string;
  insider_title: string;
  transaction_type: 'buy' | 'sell';
  shares: number;
  price: number;
  total_value: number;
}

export interface FilingsEvidence {
  claim_ticker: string;
  category: 'insider_trading';
  filings: InsiderFiling[];
  summary: string;
  recent_bias: 'net_buying' | 'net_selling' | 'balanced';
  evidence_freshness: string;
  cache_hit: boolean;
}

export interface SkepticOutput {
  claim_ticker: string;
  counter_arguments: { point: string; point_en?: string; evidence_ref: string; strength: number }[];
  ambiguity_points: string[];
  ambiguity_points_en?: string[];
  missing_evidence: string[];
  missing_evidence_en?: string[];
  skepticism_score: number;
}

export interface EvidenceAssessment {
  claim_ticker: string;
  claim_category: string;
  direction?: 'above' | 'below' | 'between' | 'neutral';
  evidence_summary: { valuation?: ValuationEvidence; fundamental?: FundamentalEvidence; market?: MarketEvidence };
  contradictions: string[];
  contradictions_i18n?: { id: string; en: string }[];
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
  explanation_en?: string;
  confidence: number;
  direction?: 'above' | 'below' | 'between' | 'neutral';
}

export interface PipelineEvent {
  event_type: string;
  claim_id: string;
  data: any;
  timestamp: string;
}
