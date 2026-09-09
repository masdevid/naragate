import pytest
from unittest.mock import AsyncMock, patch

from app.models.schemas import (
    Claim, ClaimCategory, ClaimDirection, EvidenceAssessment
)
from app.services.judge import (
    EvidenceJudge, ScoreGenerator, policy_narrative_dimension,
    MIN_POLICY_REACTION, MAX_PRIOR_DRIFT,
)
from app.services.policy_reaction import (
    policy_reaction_for_series, gather_policy_reactions,
)


class TestPolicyReactionForSeries:
    def test_computes_post_and_prior_returns(self):
        series = [
            ("2026-01-01", 100.0), ("2026-01-02", 101.0), ("2026-01-03", 102.0),
            ("2026-01-04", 103.0), ("2026-01-05", 104.0), ("2026-01-06", 105.0),
            ("2026-01-07", 106.0),
        ]
        r = policy_reaction_for_series(series, "2026-01-03", window_days=2)
        assert r is not None
        assert r["prior_return"] == pytest.approx(2.0)   # (102-100)/100*100
        assert r["post_return"] == pytest.approx((104 - 102) / 102 * 100, abs=1e-2)  # 2 days after

    def test_missing_data_after_policy_returns_none(self):
        series = [
            ("2026-01-01", 100.0), ("2026-01-02", 101.0), ("2026-01-03", 102.0),
        ]
        assert policy_reaction_for_series(series, "2026-01-03", window_days=2) is None

    def test_policy_date_before_all_data_returns_none(self):
        series = [("2026-01-05", 100.0), ("2026-01-06", 101.0)]
        assert policy_reaction_for_series(series, "2026-01-03", window_days=1) is None

    def test_policy_date_not_a_trading_day_uses_last_prior_day(self):
        # 2026-01-04 falls on a weekend in this synthetic series; anchor is 01-03.
        series = [
            ("2026-01-01", 100.0), ("2026-01-02", 101.0), ("2026-01-03", 102.0),
            ("2026-01-05", 103.0), ("2026-01-06", 104.0),
        ]
        r = policy_reaction_for_series(series, "2026-01-04", window_days=1)
        assert r is not None
        assert r["post_return"] == pytest.approx((103 - 102) / 102 * 100, abs=1e-2)


class TestGatherPolicyReactions:
    @pytest.mark.asyncio
    async def test_uses_latest_policy_date(self):
        tx = [
            {"date": "2026-01-01", "close": 100.0},
            {"date": "2026-01-02", "close": 101.0},
            {"date": "2026-01-03", "close": 102.0},
            {"date": "2026-01-04", "close": 103.0},
            {"date": "2026-01-05", "close": 104.0},
            {"date": "2026-01-06", "close": 105.0},
        ]
        with patch("app.services.policy_reaction.fetch_daily_transaction", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = (tx, True)
            reactions = await gather_policy_reactions(
                ["PGAS"], ["2026-01-01", "2026-01-03"], window_days=1
            )
        assert len(reactions) == 1
        assert reactions[0]["ticker"] == "PGAS"
        assert reactions[0]["policy_date"] == "2026-01-03"

    @pytest.mark.asyncio
    async def test_member_failure_skipped(self):
        with patch("app.services.policy_reaction.fetch_daily_transaction", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = Exception("downstream")
            reactions = await gather_policy_reactions(["PGAS", "MEDC"], ["2026-01-03"])
        assert reactions == []

    @pytest.mark.asyncio
    async def test_empty_inputs(self):
        assert await gather_policy_reactions([], ["2026-01-03"]) == []
        assert await gather_policy_reactions(["PGAS"], []) == []


class TestPolicyNarrativeDimension:
    def test_supporting_reaction_scores_high(self):
        policy = {"policy_events": [], "reactions": [
            {"ticker": "PGAS", "post_return": 4.0, "prior_return": 0.0},
        ]}
        assert policy_narrative_dimension(policy, "above") == 70.0  # 50 + 4*5

    def test_mirror_direction_lowers_score(self):
        policy = {"policy_events": [], "reactions": [
            {"ticker": "PGAS", "post_return": 4.0, "prior_return": 0.0},
        ]}
        assert policy_narrative_dimension(policy, "below") == 30.0  # 50 - 4*5

    def test_timing_violation_scores_neutral(self):
        # The same name moved in the prior period → reaction not attributable.
        policy = {"reactions": [
            {"ticker": "PGAS", "post_return": 8.0, "prior_return": MAX_PRIOR_DRIFT},
        ]}
        assert policy_narrative_dimension(policy, "above") == 50.0

    def test_no_reactions_scores_neutral(self):
        assert policy_narrative_dimension({}, "above") == 50.0
        assert policy_narrative_dimension(None, "above") == 50.0

    def test_inert_post_move_scores_neutral(self):
        policy = {"reactions": [
            {"ticker": "PGAS", "post_return": 0.1, "prior_return": 0.0},
        ]}
        assert policy_narrative_dimension(policy, "above") == 50.0

    def test_partial_timing_violation_keeps_clean_reactions(self):
        policy = {"reactions": [
            {"ticker": "PGAS", "post_return": 4.0, "prior_return": 0.0},
            {"ticker": "MEDC", "post_return": 8.0, "prior_return": MAX_PRIOR_DRIFT},
        ]}
        assert policy_narrative_dimension(policy, "above") == 70.0


def _market_claim(direction="above"):
    return Claim(
        ticker="PGAS",
        category=ClaimCategory.MARKET,
        assertion="harga bbm naik",
        direction=ClaimDirection(direction),
        confidence=0.7,
        is_policy=True,
        sector="oil-gas",
        sector_members=["PGAS"],
    )


class TestJudgePolicyDimensionAccAc:
    @pytest.fixture
    def judge(self):
        return EvidenceJudge()

    @pytest.fixture
    def generator(self):
        return ScoreGenerator()

    def policy(self, post=4.0, prior=0.0):
        return [{"ticker": "PGAS", "post_return": post, "prior_return": prior}]

    def test_market_claim_dimensions_include_policy_narrative_gap(self, judge):
        assessment = judge.assess(_market_claim(), {"policy": {"reactions": self.policy()}})
        assert "policy_narrative_gap" in assessment.applicable_dimensions

    def test_fundamental_claim_dimensions_include_policy_narrative_gap(self, judge):
        claim = Claim(
            ticker="PGAS", category=ClaimCategory.FUNDAMENTAL,
            assertion="subsidi bbm naik", direction=ClaimDirection.ABOVE, confidence=0.7,
            is_policy=True, sector="oil-gas", sector_members=["PGAS"],
        )
        assessment = judge.assess(claim, {"policy": {"reactions": self.policy()}})
        assert "policy_narrative_gap" in assessment.applicable_dimensions

    def test_valuation_claim_dimensions_never_include_it(self, judge):
        claim = Claim(
            ticker="BBCA", category=ClaimCategory.VALUATION,
            assertion="PE mahal", direction=ClaimDirection.ABOVE, confidence=0.8,
        )
        assessment = judge.assess(claim, {"policy": {"reactions": self.policy(post=8.0)}})
        assert "policy_narrative_gap" not in assessment.applicable_dimensions

    def test_timing_violation_scores_neutral_in_generator(self, generator):
        assessment = EvidenceAssessment(
            claim_ticker="PGAS",
            claim_category="market",
            direction="above",
            evidence_summary={"policy": {"reactions": self.policy(post=8.0, prior=MAX_PRIOR_DRIFT)}},
            contradictions=[],
            skeptic_challenges=[],
            evidence_confidence=0.8,
            applicable_dimensions=["policy_narrative_gap", "evidence_confidence"],
        )
        result = generator.compute(assessment)
        assert result.dimensions["policy_narrative_gap"] == 50.0

    def test_judge_contradicts_market_claim_on_opposing_reaction(self, judge):
        # Claim "above" but sector fell after the announcement → contradiction.
        assessment = judge.assess(_market_claim("above"), {"policy": {"reactions": self.policy(post=-4.0)}})
        assert any("policy announcement" in c.lower() for c in assessment.contradictions)

    def test_judge_no_contradiction_when_aligned(self, judge):
        assessment = judge.assess(_market_claim("above"), {"policy": {"reactions": self.policy(post=4.0)}})
        assert not any("policy announcement" in c.lower() for c in assessment.contradictions)

    def test_valuation_never_contradicted_by_policy_reaction(self, judge):
        claim = Claim(
            ticker="BBCA", category=ClaimCategory.VALUATION,
            assertion="PE mahal", direction=ClaimDirection.ABOVE, confidence=0.8,
        )
        assessment = judge.assess(claim, {"policy": {"reactions": self.policy(post=-4.0)}})
        assert not any("policy announcement" in c.lower() for c in assessment.contradictions)

    def test_generator_policy_dimension_supports_direction(self, generator):
        assessment = EvidenceAssessment(
            claim_ticker="PGAS",
            claim_category="market",
            direction="above",
            evidence_summary={"policy": {"reactions": self.policy(post=4.0)}},
            contradictions=[],
            skeptic_challenges=[],
            evidence_confidence=0.8,
            applicable_dimensions=["policy_narrative_gap", "evidence_confidence"],
        )
        result = generator.compute(assessment)
        assert result.dimensions["policy_narrative_gap"] == 70.0

    def test_generator_policy_dimension_without_evidence_scores_neutral(self, generator):
        assessment = EvidenceAssessment(
            claim_ticker="PGAS",
            claim_category="market",
            direction="above",
            evidence_summary={},
            contradictions=[],
            skeptic_challenges=[],
            evidence_confidence=0.8,
            applicable_dimensions=["policy_narrative_gap", "evidence_confidence"],
        )
        result = generator.compute(assessment)
        assert result.dimensions["policy_narrative_gap"] == 50.0