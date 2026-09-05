from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class ClaimCategory(str, Enum):
    VALUATION = "valuation"
    FUNDAMENTAL = "fundamental"
    MARKET = "market"
    PEER_COMPARISON = "peer_comparison"

class ClaimDirection(str, Enum):
    ABOVE = "above"
    BELOW = "below"
    BETWEEN = "between"
    NEUTRAL = "neutral"

class ClaimStatus(str, Enum):
    PENDING = "pending"
    PARSED = "parsed"
    EVIDENCE_RETRIEVED = "evidence_retrieved"
    SKEPTIC_REVIEWED = "skeptic_reviewed"
    SCORED = "scored"
    COMPLETED = "completed"
    FAILED = "failed"

class VerdictBand(str, Enum):
    CONTRADICTED = "contradicted"
    MIXED = "mixed"
    SUPPORTED = "supported"
    STRONGLY_SUPPORTED = "strongly_supported"

class Claim(BaseModel):
    claim_id: Optional[str] = None
    ticker: str
    category: ClaimCategory
    assertion: str
    assertion_en: Optional[str] = None
    direction: ClaimDirection
    time_window: Optional[str] = None
    magnitude: Optional[float] = None
    confidence: float = Field(default=0.5, ge=0, le=1)
    ticker_valid: bool = True
    narrative_source: Optional[str] = None

class ClaimCreate(BaseModel):
    narrative: str
    ticker: Optional[str] = None
    narrative_source: Optional[str] = None

class ClaimBulkDelete(BaseModel):
    claim_ids: list[str]

class EvidenceGraph(BaseModel):
    ticker: str
    company_report: Optional[dict] = None
    quarterly_financials: Optional[dict] = None
    subsector_report: Optional[dict] = None
    daily_transaction: Optional[dict] = None
    news_corpus: Optional[dict] = None
    fetched_at: Optional[str] = None
    cache_hit: bool = False

class ValuationEvidence(BaseModel):
    claim_ticker: str
    category: str
    metrics: dict
    subsector_median: dict
    premium_pct: dict
    evidence_freshness: str
    cache_hit: bool

class FundamentalEvidence(BaseModel):
    claim_ticker: str
    category: str
    metrics: dict
    trend: dict
    evidence_freshness: str
    cache_hit: bool

class MarketEvidence(BaseModel):
    claim_ticker: str
    category: str
    performance: dict
    volatility: float
    evidence_freshness: str
    cache_hit: bool

class SkepticOutput(BaseModel):
    claim_ticker: str
    counter_arguments: list[dict]
    ambiguity_points: list[str]
    ambiguity_points_en: Optional[list[str]] = None
    missing_evidence: list[str]
    missing_evidence_en: Optional[list[str]] = None
    skepticism_score: float

class EvidenceAssessment(BaseModel):
    claim_ticker: str
    claim_category: str
    evidence_summary: dict
    contradictions: list[str]
    skeptic_challenges: list[str]
    evidence_confidence: float
    applicable_dimensions: list[str]

class RealityGapScore(BaseModel):
    claim_ticker: str
    claim_category: str
    reality_gap_score: float
    verdict: VerdictBand
    dimensions: dict
    explanation: str
    explanation_en: Optional[str] = None
    confidence: float

class PipelineEvent(BaseModel):
    event_type: str
    claim_id: str
    data: dict
    timestamp: str
