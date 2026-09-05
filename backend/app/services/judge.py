from typing import Optional
from app.models.schemas import (
    Claim, EvidenceAssessment, RealityGapScore, VerdictBand,
    ValuationEvidence, FundamentalEvidence, MarketEvidence, SkepticOutput
)


class EvidenceJudge:
    def assess(self, claim: Claim, evidence: dict, skeptic: Optional[SkepticOutput] = None) -> EvidenceAssessment:
        evidence_summary = {}
        contradictions = []

        valuation = evidence.get("valuation")
        fundamental = evidence.get("fundamental")
        market = evidence.get("market")
        news = evidence.get("news")
        corporate_actions = evidence.get("corporate_actions")

        if valuation:
            evidence_summary["valuation"] = valuation.model_dump(mode="json") if hasattr(valuation, "model_dump") else valuation
        if fundamental:
            evidence_summary["fundamental"] = fundamental.model_dump(mode="json") if hasattr(fundamental, "model_dump") else fundamental
        if market:
            evidence_summary["market"] = market.model_dump(mode="json") if hasattr(market, "model_dump") else market
        if news:
            evidence_summary["news"] = news.model_dump(mode="json") if hasattr(news, "model_dump") else news
        if corporate_actions:
            evidence_summary["corporate_actions"] = corporate_actions.model_dump(mode="json") if hasattr(corporate_actions, "model_dump") else corporate_actions

        if valuation and fundamental:
            v_metrics = valuation.metrics if hasattr(valuation, "metrics") else {}
            f_metrics = fundamental.metrics if hasattr(fundamental, "metrics") else {}
            pe = v_metrics.get("pe")
            earnings_trend = (fundamental.trend if hasattr(fundamental, "trend") else {}).get("earnings_trend")
            if pe and pe > 30 and earnings_trend == "improving":
                contradictions.append("High PE but improving earnings suggests growth premium, not overvaluation")

        if news:
            corroboration = news.corroboration if hasattr(news, "corroboration") else "neutral"
            if corroboration == "contradicts":
                contradictions.append("Recent news contradicts the claim's direction")
            elif corroboration == "supports":
                contradictions.append("Recent news supports the claim's direction")

        if corporate_actions:
            relevant = corporate_actions.relevant_events if hasattr(corporate_actions, "relevant_events") else []
            if relevant and market:
                perf_1d = (market.performance if hasattr(market, "performance") else {}).get("1d", {})
                change = perf_1d.get("price_change_pct", 0)
                if abs(change or 0) > 2:
                    contradictions.append(
                        f"Price movement may be explained by corporate actions ({', '.join(relevant[:3])})"
                    )

        applicable_dimensions = []
        cat = claim.category.value
        if cat == "valuation":
            applicable_dimensions = ["valuation_gap", "peer_relative_gap", "evidence_confidence"]
        elif cat == "fundamental":
            applicable_dimensions = ["earnings_gap", "evidence_confidence", "market_momentum_gap"]
        elif cat == "market":
            applicable_dimensions = ["market_momentum_gap", "evidence_confidence", "valuation_gap"]
        elif cat == "peer_comparison":
            applicable_dimensions = ["peer_relative_gap", "evidence_confidence", "valuation_gap"]

        evidence_count = sum(1 for v in [valuation, fundamental, market, news, corporate_actions] if v is not None)
        confidence = min(1.0, evidence_count / 3.0)
        if skeptic and skeptic.skepticism_score > 70:
            confidence *= 0.8

        return EvidenceAssessment(
            claim_ticker=claim.ticker,
            claim_category=cat,
            evidence_summary=evidence_summary,
            contradictions=contradictions,
            skeptic_challenges=[c.get("point", "") for c in (skeptic.counter_arguments if skeptic else [])],
            evidence_confidence=round(confidence, 2),
            applicable_dimensions=applicable_dimensions,
        )


class ScoreGenerator:
    DIMENSION_WEIGHTS = {
        "valuation": {"valuation_gap": 0.4, "peer_relative_gap": 0.3, "evidence_confidence": 0.3},
        "fundamental": {"earnings_gap": 0.4, "evidence_confidence": 0.3, "market_momentum_gap": 0.3},
        "market": {"market_momentum_gap": 0.5, "evidence_confidence": 0.3, "valuation_gap": 0.2},
        "peer_comparison": {"peer_relative_gap": 0.5, "evidence_confidence": 0.3, "valuation_gap": 0.2},
    }

    VERDICT_BANDS = [
        (30, VerdictBand.CONTRADICTED),
        (60, VerdictBand.MIXED),
        (80, VerdictBand.SUPPORTED),
        (100, VerdictBand.STRONGLY_SUPPORTED),
    ]

    def compute(self, assessment: EvidenceAssessment, skeptic_score: float = 50.0) -> RealityGapScore:
        cat = assessment.claim_category
        weights = self.DIMENSION_WEIGHTS.get(cat, self.DIMENSION_WEIGHTS["valuation"])

        dimensions = {}
        total_score = 0.0

        evidence_summary = assessment.evidence_summary or {}

        for dim, weight in weights.items():
            if dim == "evidence_confidence":
                dim_score = assessment.evidence_confidence * 100
            elif dim == "valuation_gap":
                valuation = evidence_summary.get("valuation")
                if valuation:
                    pe_premium = (valuation.get("premium_pct", {}) or {}).get("pe")
                    if pe_premium is not None:
                        dim_score = max(0, min(100, 50 - pe_premium / 2))
                    else:
                        dim_score = 50.0
                else:
                    dim_score = 50.0
            elif dim == "earnings_gap":
                fundamental = evidence_summary.get("fundamental")
                if fundamental:
                    trend = fundamental.get("trend", {})
                    if trend.get("earnings_trend") == "improving":
                        dim_score = 75.0
                    elif trend.get("earnings_trend") == "declining":
                        dim_score = 25.0
                    else:
                        dim_score = 50.0
                else:
                    dim_score = 50.0
            elif dim == "market_momentum_gap":
                market = evidence_summary.get("market")
                if market:
                    perf_1d = (market.get("performance", {}) or {}).get("1d", {})
                    change = perf_1d.get("price_change_pct", 0)
                    dim_score = max(0, min(100, 50 + change * 5))
                else:
                    dim_score = 50.0
            elif dim == "peer_relative_gap":
                valuation = evidence_summary.get("valuation")
                if valuation:
                    pb_premium = (valuation.get("premium_pct", {}) or {}).get("pb")
                    if pb_premium is not None:
                        dim_score = max(0, min(100, 50 - pb_premium / 2))
                    else:
                        dim_score = 50.0
                else:
                    dim_score = 50.0
            else:
                dim_score = 50.0

            dimensions[dim] = round(dim_score, 2)
            total_score += dim_score * weight

        skeptic_adjustment = (100 - skeptic_score) / 100 * 0.1
        total_score = total_score * (0.9 + skeptic_adjustment)
        total_score = max(0, min(100, total_score))

        verdict = VerdictBand.CONTRADICTED
        for threshold, band in self.VERDICT_BANDS:
            if total_score <= threshold:
                verdict = band
                break

        explanation = self._build_explanation(assessment, dimensions, verdict, "id")
        explanation_en = self._build_explanation(assessment, dimensions, verdict, "en")

        return RealityGapScore(
            claim_ticker=assessment.claim_ticker,
            claim_category=cat,
            reality_gap_score=round(total_score, 2),
            verdict=verdict,
            dimensions=dimensions,
            explanation=explanation,
            explanation_en=explanation_en,
            confidence=assessment.evidence_confidence,
        )

    def _build_explanation(self, assessment: EvidenceAssessment, dimensions: dict, verdict: VerdictBand, language: str = "id") -> str:
        if language == "en":
            parts = [f"Verdict: {verdict.value.replace('_', ' ').title()}"]

            if assessment.contradictions:
                parts.append(f"Contradictions found: {'; '.join(assessment.contradictions[:2])}")

            if assessment.skeptic_challenges:
                parts.append(f"Skeptic challenges: {len(assessment.skeptic_challenges)} counter-arguments")

            top_dim = max(dimensions.items(), key=lambda x: x[1]) if dimensions else None
            if top_dim:
                parts.append(f"Strongest dimension: {top_dim[0]} ({top_dim[1]:.0f}/100)")

            parts.append(f"Evidence confidence: {assessment.evidence_confidence:.0%}")
            return ". ".join(parts) + "."

        verdict_names = {
            "contradicted": "Bertentangan",
            "mixed": "Campuran",
            "supported": "Didukung",
            "strongly_supported": "Sangat Didukung",
        }
        verdict_label = verdict_names.get(verdict.value, verdict.value.replace("_", " ").title())
        parts = [f"Verdik: {verdict_label}"]

        if assessment.contradictions:
            parts.append(f"Kontradiksi ditemukan: {'; '.join(assessment.contradictions[:2])}")

        if assessment.skeptic_challenges:
            parts.append(f"Tantangan skeptis: {len(assessment.skeptic_challenges)} argumen balasan")

        top_dim = max(dimensions.items(), key=lambda x: x[1]) if dimensions else None
        if top_dim:
            parts.append(f"Dimensi terkuat: {top_dim[0]} ({top_dim[1]:.0f}/100)")

        parts.append(f"Keyakinan bukti: {assessment.evidence_confidence:.0%}")
        return ". ".join(parts) + "."


evidence_judge = EvidenceJudge()
score_generator = ScoreGenerator()
