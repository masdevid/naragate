import pytest
from app.services.judge import EvidenceJudge, ScoreGenerator
from app.models.schemas import (
    Claim, ClaimCategory, ClaimDirection, EvidenceAssessment, RealityGapScore,
    ValuationEvidence, FundamentalEvidence, MarketEvidence, SkepticOutput, VerdictBand,
    FilingsEvidence
)


class TestEvidenceJudge:
    """Tests for evidence assessment."""

    @pytest.fixture
    def judge(self):
        return EvidenceJudge()

    @pytest.fixture
    def claim(self):
        return Claim(
            ticker="BBCA",
            category=ClaimCategory.VALUATION,
            assertion="PE is expensive",
            direction=ClaimDirection.ABOVE,
            confidence=0.8,
        )

    def test_assesses_with_all_evidence(self, judge, claim):
        valuation = ValuationEvidence(
            claim_ticker="BBCA",
            category="valuation",
            metrics={"pe": 25.5},
            subsector_median={"pe": 20.0},
            premium_pct={"pe": 27.5},
            evidence_freshness="2024-01-01",
            cache_hit=False,
        )
        evidence = {"valuation": valuation}

        assessment = judge.assess(claim, evidence)

        assert assessment.claim_ticker == "BBCA"
        assert assessment.evidence_confidence == round(1 / 3, 2)
        assert "valuation_gap" in assessment.applicable_dimensions

    def test_assesses_without_evidence(self, judge, claim):
        assessment = judge.assess(claim, {})

        assert assessment.evidence_confidence == 0.0
        assert assessment.evidence_summary == {}

    def test_applies_skeptic_penalty(self, judge, claim):
        valuation = ValuationEvidence(
            claim_ticker="BBCA",
            category="valuation",
            metrics={"pe": 25.5},
            subsector_median={"pe": 20.0},
            premium_pct={"pe": 27.5},
            evidence_freshness="2024-01-01",
            cache_hit=False,
        )
        skeptic = SkepticOutput(
            claim_ticker="BBCA",
            counter_arguments=[],
            ambiguity_points=[],
            missing_evidence=[],
            skepticism_score=80.0,
        )
        evidence = {"valuation": valuation}

        assessment = judge.assess(claim, evidence, skeptic)

        assert assessment.evidence_confidence == round(1 / 3 * 0.8, 2)  # 0.33 * 0.8

    def test_detects_contradiction(self, judge):
        claim = Claim(
            ticker="BBCA",
            category=ClaimCategory.VALUATION,
            assertion="PE is expensive",
            direction=ClaimDirection.ABOVE,
            confidence=0.8,
        )
        valuation = ValuationEvidence(
            claim_ticker="BBCA",
            category="valuation",
            metrics={"pe": 35.0},
            subsector_median={},
            premium_pct={},
            evidence_freshness="2024-01-01",
            cache_hit=False,
        )
        fundamental = FundamentalEvidence(
            claim_ticker="BBCA",
            category="fundamental",
            metrics={},
            trend={"earnings_trend": "improving"},
            evidence_freshness="2024-01-01",
            cache_hit=False,
        )
        evidence = {"valuation": valuation, "fundamental": fundamental}

        assessment = judge.assess(claim, evidence)

        assert len(assessment.contradictions) > 0
        assert "growth premium" in assessment.contradictions[0].lower()

    def test_detects_insider_net_selling_contradiction(self, judge):
        claim = Claim(
            ticker="BBCA",
            category=ClaimCategory.INSIDER_TRADING,
            assertion="insiders are selling",
            direction=ClaimDirection.BELOW,
            confidence=0.8,
        )
        filings = FilingsEvidence(
            claim_ticker="BBCA",
            category="insider_trading",
            filings=[],
            summary="test",
            recent_bias="net_selling",
            evidence_freshness="2024-01-01",
            cache_hit=False,
        )
        evidence = {"filings": filings}

        assessment = judge.assess(claim, evidence)

        assert len(assessment.contradictions) > 0
        assert "net selling" in assessment.contradictions[0].lower()
        assert "insider_bias_gap" in assessment.applicable_dimensions

    def test_detects_insider_net_buying_contradiction(self, judge):
        claim = Claim(
            ticker="BBCA",
            category=ClaimCategory.INSIDER_TRADING,
            assertion="insiders are selling",
            direction=ClaimDirection.BELOW,
            confidence=0.8,
        )
        filings = FilingsEvidence(
            claim_ticker="BBCA",
            category="insider_trading",
            filings=[],
            summary="test",
            recent_bias="net_buying",
            evidence_freshness="2024-01-01",
            cache_hit=False,
        )
        evidence = {"filings": filings}

        assessment = judge.assess(claim, evidence)

        assert len(assessment.contradictions) > 0
        assert "net buying" in assessment.contradictions[0].lower()

    def test_insider_filings_included_in_evidence_summary(self, judge):
        claim = Claim(
            ticker="BBCA",
            category=ClaimCategory.INSIDER_TRADING,
            assertion="insiders are selling",
            direction=ClaimDirection.BELOW,
            confidence=0.8,
        )
        filings = FilingsEvidence(
            claim_ticker="BBCA",
            category="insider_trading",
            filings=[{"date": "2025-08-15", "insider_name": "Budi", "transaction_type": "sell"}],
            summary="test",
            recent_bias="net_selling",
            evidence_freshness="2024-01-01",
            cache_hit=False,
        )
        evidence = {"filings": filings}

        assessment = judge.assess(claim, evidence)

        assert "filings" in assessment.evidence_summary
        assert assessment.evidence_summary["filings"]["recent_bias"] == "net_selling"


class TestScoreGenerator:
    """Tests for Reality Gap Score computation."""

    @pytest.fixture
    def generator(self):
        return ScoreGenerator()

    @pytest.fixture
    def assessment(self):
        return EvidenceAssessment(
            claim_ticker="BBCA",
            claim_category="valuation",
            evidence_summary={
                "valuation": {
                    "premium_pct": {"pe": 25.0}
                }
            },
            contradictions=[],
            skeptic_challenges=[],
            evidence_confidence=0.8,
            applicable_dimensions=["valuation_gap", "peer_relative_gap", "evidence_confidence"],
        )

    def test_computes_score_for_valuation(self, generator, assessment):
        result = generator.compute(assessment, skeptic_score=50.0)

        assert isinstance(result, RealityGapScore)
        assert result.claim_ticker == "BBCA"
        assert 0 <= result.reality_gap_score <= 100
        assert result.verdict in VerdictBand

    def test_verdict_band_contradicted(self, generator):
        assessment = EvidenceAssessment(
            claim_ticker="BBCA",
            claim_category="valuation",
            evidence_summary={},
            contradictions=[],
            skeptic_challenges=[],
            evidence_confidence=0.0,
            applicable_dimensions=[],
        )

        result = generator.compute(assessment, skeptic_score=100.0)

        # With 0 evidence confidence and high skeptic score, score should be low
        assert result.reality_gap_score < 50
        assert result.verdict in [VerdictBand.CONTRADICTED, VerdictBand.MIXED]

    def test_verdict_band_strongly_supported(self, generator):
        assessment = EvidenceAssessment(
            claim_ticker="BBCA",
            claim_category="valuation",
            evidence_summary={
                "valuation": {"premium_pct": {"pe": -50.0}}  # Big discount
            },
            contradictions=[],
            skeptic_challenges=[],
            evidence_confidence=1.0,
            applicable_dimensions=["valuation_gap", "evidence_confidence"],
        )

        result = generator.compute(assessment, skeptic_score=0.0)

        assert result.verdict in [VerdictBand.SUPPORTED, VerdictBand.STRONGLY_SUPPORTED]

    def test_skeptic_adjusts_score(self, generator):
        assessment = EvidenceAssessment(
            claim_ticker="BBCA",
            claim_category="valuation",
            evidence_summary={},
            contradictions=[],
            skeptic_challenges=[],
            evidence_confidence=0.5,
            applicable_dimensions=[],
        )

        result_low_skeptic = generator.compute(assessment, skeptic_score=0.0)
        result_high_skeptic = generator.compute(assessment, skeptic_score=100.0)

        assert result_low_skeptic.reality_gap_score > result_high_skeptic.reality_gap_score

    def test_builds_explanation(self, generator, assessment):
        result = generator.compute(assessment, skeptic_score=50.0)

        assert "Verdik:" in result.explanation
        assert "Keyakinan bukti:" in result.explanation
        assert "Verdict:" in result.explanation_en
        assert "Evidence confidence:" in result.explanation_en

    def test_fundamental_category_uses_earnings_gap(self, generator):
        assessment = EvidenceAssessment(
            claim_ticker="BBCA",
            claim_category="fundamental",
            evidence_summary={
                "fundamental": {
                    "trend": {"earnings_trend": "improving"}
                }
            },
            contradictions=[],
            skeptic_challenges=[],
            evidence_confidence=0.8,
            applicable_dimensions=["earnings_gap", "evidence_confidence"],
        )

        result = generator.compute(assessment)

        assert "earnings_gap" in result.dimensions
        assert result.dimensions["earnings_gap"] == 75.0

    def test_market_category_uses_momentum(self, generator):
        assessment = EvidenceAssessment(
            claim_ticker="BBCA",
            claim_category="market",
            evidence_summary={
                "market": {
                    "performance": {"1d": {"price_change_pct": 5.0}}
                }
            },
            contradictions=[],
            skeptic_challenges=[],
            evidence_confidence=0.8,
            applicable_dimensions=["market_momentum_gap", "evidence_confidence"],
        )

        result = generator.compute(assessment)

        assert "market_momentum_gap" in result.dimensions
        assert result.dimensions["market_momentum_gap"] == 75.0  # 50 + 5*5

    def test_insider_trading_uses_insider_bias_gap(self, generator):
        assessment = EvidenceAssessment(
            claim_ticker="BBCA",
            claim_category="insider_trading",
            evidence_summary={
                "filings": {"recent_bias": "net_buying"}
            },
            contradictions=[],
            skeptic_challenges=[],
            evidence_confidence=0.8,
            applicable_dimensions=["insider_bias_gap", "evidence_confidence", "market_momentum_gap"],
        )

        result = generator.compute(assessment)

        assert "insider_bias_gap" in result.dimensions
        assert result.dimensions["insider_bias_gap"] == 75.0

    def test_insider_trading_net_selling_scores_low(self, generator):
        assessment = EvidenceAssessment(
            claim_ticker="BBCA",
            claim_category="insider_trading",
            evidence_summary={
                "filings": {"recent_bias": "net_selling"}
            },
            contradictions=[],
            skeptic_challenges=[],
            evidence_confidence=0.8,
            applicable_dimensions=["insider_bias_gap", "evidence_confidence", "market_momentum_gap"],
        )

        result = generator.compute(assessment)

        assert result.dimensions["insider_bias_gap"] == 25.0

    def test_insider_trading_balanced_scores_mid(self, generator):
        assessment = EvidenceAssessment(
            claim_ticker="BBCA",
            claim_category="insider_trading",
            evidence_summary={
                "filings": {"recent_bias": "balanced"}
            },
            contradictions=[],
            skeptic_challenges=[],
            evidence_confidence=0.8,
            applicable_dimensions=["insider_bias_gap", "evidence_confidence", "market_momentum_gap"],
        )

        result = generator.compute(assessment)

        assert result.dimensions["insider_bias_gap"] == 50.0

    def test_insider_trading_without_filings_scores_mid(self, generator):
        assessment = EvidenceAssessment(
            claim_ticker="BBCA",
            claim_category="insider_trading",
            evidence_summary={},
            contradictions=[],
            skeptic_challenges=[],
            evidence_confidence=0.8,
            applicable_dimensions=["insider_bias_gap", "evidence_confidence", "market_momentum_gap"],
        )

        result = generator.compute(assessment)

        assert result.dimensions["insider_bias_gap"] == 50.0
