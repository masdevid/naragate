import pytest
from app.services.judge import EvidenceJudge, ScoreGenerator
from app.models.schemas import (
    Claim, ClaimCategory, ClaimDirection, EvidenceAssessment, RealityGapScore,
    ValuationEvidence, FundamentalEvidence, MarketEvidence, SkepticOutput, VerdictBand,
    FilingsEvidence, NewsEvidence
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
        # Valuation confidence counts valuation+fundamental only: 1/2
        assert assessment.evidence_confidence == round(1 / 2, 2)
        assert assessment.direction == "above"
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

        # Valuation confidence counts valuation+fundamental only: (1/2) * 0.8
        assert assessment.evidence_confidence == round(1 / 2 * 0.8, 2)  # 0.4

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

    def test_detects_flow_against_claim_as_contradiction(self, judge):
        claim = Claim(
            ticker="BBCA",
            category=ClaimCategory.MARKET,
            assertion="foreign investors are buying",
            direction=ClaimDirection.ABOVE,
            confidence=0.8,
        )
        evidence = {"market": {
            "performance": {"1d": {"price_change_pct": 0.0}},
            "flow_summary": {"foreign_bias": "net_outflow", "broker_bias": "net_sell"},
        }}

        assessment = judge.assess(claim, evidence)

        assert any("flow" in c.lower() for c in assessment.contradictions)

    def test_aligned_flow_is_not_a_contradiction(self, judge):
        claim = Claim(
            ticker="BBCA",
            category=ClaimCategory.MARKET,
            assertion="foreign investors are buying",
            direction=ClaimDirection.ABOVE,
            confidence=0.8,
        )
        evidence = {"market": {
            "performance": {"1d": {"price_change_pct": 0.0}},
            "flow_summary": {"foreign_bias": "net_inflow", "broker_bias": "net_buy"},
        }}

        assessment = judge.assess(claim, evidence)

        assert not any("flow" in c.lower() for c in assessment.contradictions)

    def test_flow_does_not_contradict_a_valuation_claim(self, judge, claim):
        # claim fixture is a valuation claim; flow must not dilute it.
        evidence = {"market": {
            "performance": {"1d": {"price_change_pct": 0.0}},
            "flow_summary": {"foreign_bias": "net_outflow", "broker_bias": "net_sell"},
        }}

        assessment = judge.assess(claim, evidence)

        assert not any("flow" in c.lower() for c in assessment.contradictions)

    def test_contradictions_carry_both_languages(self, judge):
        claim = Claim(
            ticker="BBCA",
            category=ClaimCategory.MARKET,
            assertion="foreign investors are buying",
            direction=ClaimDirection.ABOVE,
            confidence=0.8,
        )
        evidence = {"market": {
            "performance": {"1d": {"price_change_pct": 0.0}},
            "flow_summary": {"foreign_bias": "net_outflow", "broker_bias": "net_sell"},
        }}

        assessment = judge.assess(claim, evidence)

        assert assessment.contradictions_i18n
        item = assessment.contradictions_i18n[0]
        assert "flow moved against" in item["en"]
        assert "Arus asing/broker" in item["id"]
        # canonical EN list still populated for compatibility
        assert assessment.contradictions[0] == item["en"]

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
            direction="below",  # discounted vs peers → "cheap" claim
            evidence_summary={
                "valuation": {"premium_pct": {"pe": -50.0, "pb": -40.0, "ps": -30.0}}  # Big discount
            },
            contradictions=[],
            skeptic_challenges=[],
            evidence_confidence=1.0,
            applicable_dimensions=["valuation_gap", "evidence_confidence"],
        )

        result = generator.compute(assessment, skeptic_score=0.0)

        assert result.verdict in [VerdictBand.SUPPORTED, VerdictBand.STRONGLY_SUPPORTED]
        assert result.reality_gap_score >= 61.0

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


class TestDirectionAwareScoring:
    """Valuation scoring must align with the claim's direction (above/below)."""

    @pytest.fixture
    def generator(self):
        return ScoreGenerator()

    @pytest.fixture
    def judge(self):
        return EvidenceJudge()

    def test_expensive_claim_all_ratios_positive_is_supported(self, generator):
        # Issue repro: "BBCA stock price is expensive" — all ratios above the
        # subsector median. Support must NOT be ~33/MIXED.
        assessment = EvidenceAssessment(
            claim_ticker="BBCA",
            claim_category="valuation",
            direction="above",
            evidence_summary={
                "valuation": {
                    "metrics": {"pe": 25.5, "pb": 5.1, "ps": 6.4, "forward_pe": 24.0, "pcf": 18.2},
                    "subsector_median": {"pe": 17.5, "pb": 2.9, "ps": 4.1},
                    "premium_pct": {"pe": 45.7, "pb": 75.9, "ps": 56.1},
                }
            },
            contradictions=[],
            skeptic_challenges=[],
            evidence_confidence=1.0,
            applicable_dimensions=["valuation_gap", "peer_relative_gap", "evidence_confidence"],
        )

        result = generator.compute(assessment, skeptic_score=0.0)

        assert result.verdict == VerdictBand.STRONGLY_SUPPORTED, (
            f"Expected STRONGLY_SUPPORTED, got {result.verdict.value} ({result.reality_gap_score})"
        )
        assert result.reality_gap_score > 80.0

    def test_expensive_claim_low_confidence_guardrail_still_not_mixed(self, generator):
        # Even with weak confidence, unanimous ratios cannot produce MIXED.
        assessment = EvidenceAssessment(
            claim_ticker="BBCA",
            claim_category="valuation",
            direction="above",
            evidence_summary={
                "valuation": {
                    "premium_pct": {"pe": 30.0, "pb": 25.0, "ps": 20.0},
                }
            },
            contradictions=[],
            skeptic_challenges=[],
            evidence_confidence=0.3,
            applicable_dimensions=["valuation_gap", "peer_relative_gap", "evidence_confidence"],
        )

        result = generator.compute(assessment, skeptic_score=92.0)

        assert result.verdict == VerdictBand.SUPPORTED
        assert result.reality_gap_score >= 61.0

    def test_cheap_claim_positive_premium_is_contradicted(self, generator):
        # Claim says "cheap" but all ratios trade ABOVE the median → contradicted.
        assessment = EvidenceAssessment(
            claim_ticker="BBCA",
            claim_category="valuation",
            direction="below",
            evidence_summary={
                "valuation": {
                    "premium_pct": {"pe": 45.7, "pb": 75.9, "ps": 56.1},
                }
            },
            contradictions=[],
            skeptic_challenges=[],
            evidence_confidence=0.8,
            applicable_dimensions=["valuation_gap", "peer_relative_gap", "evidence_confidence"],
        )

        result = generator.compute(assessment, skeptic_score=0.0)

        assert result.verdict == VerdictBand.CONTRADICTED

    def test_conflicting_ratios_allow_mixed(self, generator):
        # PE rich but PB cheap → ratios conflict → MIXED is valid.
        assessment = EvidenceAssessment(
            claim_ticker="BBCA",
            claim_category="valuation",
            direction="above",
            evidence_summary={
                "valuation": {
                    "premium_pct": {"pe": 30.0, "pb": -40.0, "ps": 5.0},
                }
            },
            contradictions=[],
            skeptic_challenges=[],
            evidence_confidence=0.8,
            applicable_dimensions=["valuation_gap", "peer_relative_gap", "evidence_confidence"],
        )

        result = generator.compute(assessment, skeptic_score=50.0)

        assert result.verdict in [VerdictBand.MIXED, VerdictBand.SUPPORTED]

    def test_market_momentum_flips_with_direction(self, generator):
        # A +5% day supports an "above/rising" market claim, contradicts a "below" one.
        up = EvidenceAssessment(
            claim_ticker="BBCA",
            claim_category="market",
            direction="above",
            evidence_summary={"market": {"performance": {"1d": {"price_change_pct": 5.0}}}},
            contradictions=[],
            skeptic_challenges=[],
            evidence_confidence=0.8,
            applicable_dimensions=["market_momentum_gap", "evidence_confidence"],
        )
        down = EvidenceAssessment(
            claim_ticker="BBCA",
            claim_category="market",
            direction="below",
            evidence_summary={"market": {"performance": {"1d": {"price_change_pct": 5.0}}}},
            contradictions=[],
            skeptic_challenges=[],
            evidence_confidence=0.8,
            applicable_dimensions=["market_momentum_gap", "evidence_confidence"],
        )

        up_result = generator.compute(up)
        down_result = generator.compute(down)

        assert up_result.dimensions["market_momentum_gap"] == 75.0
        assert down_result.dimensions["market_momentum_gap"] == 25.0

    @staticmethod
    def _market_assessment(direction, price_change_pct, flow_summary=None, market_movers=None, relative_strength=None):
        market = {"performance": {"1d": {"price_change_pct": price_change_pct}}}
        if flow_summary is not None:
            market["flow_summary"] = flow_summary
        if market_movers is not None:
            market["market_movers"] = market_movers
        if relative_strength is not None:
            market["relative_strength"] = relative_strength
        return EvidenceAssessment(
            claim_ticker="BBCA",
            claim_category="market",
            direction=direction,
            evidence_summary={"market": market},
            contradictions=[],
            skeptic_challenges=[],
            evidence_confidence=0.8,
            applicable_dimensions=["market_momentum_gap", "evidence_confidence"],
        )

    def test_market_momentum_corroborated_by_unanimous_flow(self, generator):
        # Flat price but foreign inflow + broker net buy corroborate an "above" claim.
        result = generator.compute(self._market_assessment(
            "above", 0.0, {"foreign_bias": "net_inflow", "broker_bias": "net_buy"}
        ))
        assert result.dimensions["market_momentum_gap"] == 60.0  # 50 + 10

    def test_market_momentum_flow_opposes_claim(self, generator):
        # Outflow + net sell undercut a bullish claim.
        result = generator.compute(self._market_assessment(
            "above", 0.0, {"foreign_bias": "net_outflow", "broker_bias": "net_sell"}
        ))
        assert result.dimensions["market_momentum_gap"] == 40.0  # 50 - 10

    def test_market_momentum_flow_mirrors_for_below_claim(self, generator):
        # Outflow corroborates a bearish claim.
        result = generator.compute(self._market_assessment(
            "below", 0.0, {"foreign_bias": "net_outflow", "broker_bias": "net_sell"}
        ))
        assert result.dimensions["market_momentum_gap"] == 60.0

    def test_market_momentum_flow_dilutes_on_disagreement(self, generator):
        # Foreign inflow vs broker net sell cancel out — no fabricated edge.
        result = generator.compute(self._market_assessment(
            "above", 0.0, {"foreign_bias": "net_inflow", "broker_bias": "net_sell"}
        ))
        assert result.dimensions["market_momentum_gap"] == 50.0

    def test_market_momentum_balanced_or_absent_flow_is_neutral(self, generator):
        balanced = generator.compute(self._market_assessment(
            "above", 0.0, {"foreign_bias": "balanced", "broker_bias": "balanced"}
        ))
        absent = generator.compute(self._market_assessment("above", 0.0))
        assert balanced.dimensions["market_momentum_gap"] == 50.0
        assert absent.dimensions["market_momentum_gap"] == 50.0

    def test_market_momentum_flow_is_bounded(self, generator):
        # +5% price alone is 75; inflow adds 10 -> 85, still within [0, 100].
        high = generator.compute(self._market_assessment(
            "above", 5.0, {"foreign_bias": "net_inflow"}
        ))
        low = generator.compute(self._market_assessment(
            "above", -20.0, {"foreign_bias": "net_outflow"}
        ))
        assert high.dimensions["market_momentum_gap"] == 85.0
        assert low.dimensions["market_momentum_gap"] == 0.0  # clamped

    def test_relative_strength_overrides_raw_price_change(self, generator):
        # Raw +3% looks bullish, but +3% vs an IHSG +5% day is underperformance.
        result = generator.compute(self._market_assessment(
            "above", 3.0, None, relative_strength={"1d": -2.0}
        ))
        assert result.dimensions["market_momentum_gap"] == 40.0  # 50 + (-2)*5

    def test_market_mover_membership_nudges_score(self, generator):
        gainer = generator.compute(self._market_assessment(
            "above", 0.0, None, market_movers={"classification": "top_gainers", "rank": 1}
        ))
        loser = generator.compute(self._market_assessment(
            "above", 0.0, None, market_movers={"classification": "top_losers", "rank": 1}
        ))
        assert gainer.dimensions["market_momentum_gap"] == 55.0
        assert loser.dimensions["market_momentum_gap"] == 45.0

    def test_flow_and_mover_adjustments_combine(self, generator):
        result = generator.compute(self._market_assessment(
            "above", 0.0,
            {"foreign_bias": "net_inflow", "broker_bias": "net_buy"},
            market_movers={"classification": "top_gainers", "rank": 1},
        ))
        assert result.dimensions["market_momentum_gap"] == 65.0  # 50 + 10 + 5

    def test_combined_scenario_pins_sum_and_explains_index_tension(self, generator):
        # Raw +3% but underperformed IHSG (-2% relative), propped up by inflow + top-gainer.
        assessment = self._market_assessment(
            "above", 3.0,
            {"foreign_bias": "net_inflow", "broker_bias": "net_buy"},
            market_movers={"classification": "top_gainers", "rank": 1},
            relative_strength={"1d": -2.0},
        )
        result = generator.compute(assessment, skeptic_score=50.0)

        # relative overrides raw (-2), then flow +10 and mover +5 => 55
        assert result.dimensions["market_momentum_gap"] == 55.0
        assert "indeks" in result.explanation.lower()
        assert "index" in result.explanation_en.lower()

    def test_no_tension_note_when_relative_aligns(self, generator):
        result = generator.compute(self._market_assessment(
            "above", 3.0, {"foreign_bias": "net_inflow"}, relative_strength={"1d": 2.0}
        ))
        assert "indeks" not in result.explanation.lower()
        assert "index" not in result.explanation_en.lower()

    def test_no_tension_note_when_nothing_props_it_up(self, generator):
        # Relative opposes the claim, but flow also opposes — no "propped up" story.
        result = generator.compute(self._market_assessment(
            "above", 3.0, {"foreign_bias": "net_outflow"}, relative_strength={"1d": -2.0}
        ))
        assert "indeks" not in result.explanation.lower()

    def test_indonesian_explanation_uses_localised_contradictions(self, generator):
        assessment = EvidenceAssessment(
            claim_ticker="BBCA",
            claim_category="market",
            direction="above",
            evidence_summary={"market": {"performance": {"1d": {"price_change_pct": 0.0}}}},
            contradictions=["Foreign/broker flow moved against the claim's direction"],
            contradictions_i18n=[{
                "en": "Foreign/broker flow moved against the claim's direction",
                "id": "Arus asing/broker bergerak berlawanan dengan arah klaim",
            }],
            skeptic_challenges=[],
            evidence_confidence=0.8,
            applicable_dimensions=["market_momentum_gap", "evidence_confidence"],
        )

        result = generator.compute(assessment, skeptic_score=50.0)

        assert "Arus asing/broker" in result.explanation
        assert "Foreign/broker" not in result.explanation
        assert "Foreign/broker" in result.explanation_en

    def test_valuation_not_diluted_by_news_or_market(self, judge, generator):
        # A valuation claim must ignore news/market sentiment in confidence.
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
            metrics={"pe": 25.5, "pb": 5.1, "ps": 6.4},
            subsector_median={"pe": 17.5, "pb": 2.9, "ps": 4.1},
            premium_pct={"pe": 45.7, "pb": 75.9, "ps": 56.1},
            evidence_freshness="2024-01-01",
            cache_hit=False,
        )
        evidence = {
            "valuation": valuation,
            "market": MarketEvidence(
                claim_ticker="BBCA",
                category="market",
                performance={"1d": {"price_change_pct": -8.0}},
                volatility=3.0,
                evidence_freshness="2024-01-01",
                cache_hit=False,
            ),
            "news": NewsEvidence(
                claim_ticker="BBCA",
                category="news",
                headlines=[{"title": "analysts put buy target"}],
                corroboration="contradicts",
                summary="News contradicts",
                evidence_freshness="2024-01-01",
                cache_hit=False,
            ),
        }

        assessment = judge.assess(claim, evidence, None)

        # Confidence counts valuation+fundamental only: 1/2, untouched by news
        assert assessment.evidence_confidence == 0.5
        # News cannot inject a contradiction into a valuation claim
        assert all("news" not in c.lower() for c in assessment.contradictions)

        result = generator.compute(assessment, skeptic_score=50.0)

        assert result.verdict in [VerdictBand.SUPPORTED, VerdictBand.STRONGLY_SUPPORTED]
        assert result.verdict != VerdictBand.MIXED
        assert result.reality_gap_score >= 61.0

    def test_quality_premium_note_added_when_roe_strong(self, generator):
        assessment = EvidenceAssessment(
            claim_ticker="BBCA",
            claim_category="valuation",
            direction="above",
            evidence_summary={
                "valuation": {
                    "premium_pct": {"pe": 45.7, "pb": 75.9, "ps": 56.1},
                    "health": {"roe": 21.2, "nim": 6.1, "npl": 1.2},
                }
            },
            contradictions=[],
            skeptic_challenges=[],
            evidence_confidence=0.8,
            applicable_dimensions=["valuation_gap", "peer_relative_gap", "evidence_confidence"],
        )

        result = generator.compute(assessment, skeptic_score=50.0)

        assert "quality premium" in result.explanation_en.lower()
        assert result.verdict in [VerdictBand.SUPPORTED, VerdictBand.STRONGLY_SUPPORTED]
