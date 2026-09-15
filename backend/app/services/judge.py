from typing import Optional
from app.models.schemas import (
    Claim, EvidenceAssessment, RealityGapScore, VerdictBand,
    ValuationEvidence, FundamentalEvidence, MarketEvidence, SkepticOutput
)

# T5 — policy narrative gap dimension thresholds.
MAX_PRIOR_DRIFT = 0.3        # % — run-up drift that disqualifies a "reaction"
MIN_POLICY_REACTION = 0.3    # % — post-announcement move floor for a signal
POLICY_REACTION_SCALE = 5.0  # multiplies % move, mirroring market_momentum_gap

# Foreign-flow / broker-summary corroboration for market_momentum_gap. Flow is a
# secondary signal: it shifts the momentum dimension by at most this many points,
# and only when a clear bias is present (balanced/absent flow is neutral).
FLOW_MOMENTUM_WEIGHT = 10.0
MARKET_MOVER_WEIGHT = 5.0    # bounded nudge for top-gainer/loser membership
FLOW_CONTRADICTION_THRESHOLD = 0.5  # |alignment| needed to flag flow as a contradiction
FLOW_SIGNAL = {
    "net_inflow": 1.0,
    "net_buy": 1.0,
    "net_outflow": -1.0,
    "net_sell": -1.0,
    "balanced": 0.0,
}


def direction_factor(direction: str) -> float:
    # "below" claims are the mirror image: a positive metric contradicts them.
    return -1.0 if direction == "below" else 1.0


def flow_net_signal(flow_summary: Optional[dict]) -> float:
    """Net price-supportive flow signal in [-1, 1].

    +1 = foreign inflow / broker net buy, -1 = outflow / net sell. Foreign and
    broker biases are averaged, so disagreement dilutes toward 0 and no clear
    bias yields exactly 0 (flow never fabricates a signal).
    """
    if not flow_summary:
        return 0.0
    signals = []
    for key in ("foreign_bias", "broker_bias"):
        bias = flow_summary.get(key)
        signal = FLOW_SIGNAL.get(bias) if isinstance(bias, str) else None
        if signal:
            signals.append(signal)
    if not signals:
        return 0.0
    return sum(signals) / len(signals)


def _clean_policy_reactions(policy_evidence: Optional[dict]) -> list[dict]:
    """Reactions respecting timing discipline.

    The move must be measured strictly AFTER the policy date (structural in how
    reactions are gathered) and the same name must not already have been
    drifting in the prior period — otherwise the post-policy move is not
    attributable to the policy event.
    """
    reactions = ((policy_evidence or {}).get("reactions")) or []
    clean = []
    for r in reactions:
        prior = r.get("prior_return")
        post = r.get("post_return")
        if not isinstance(prior, (int, float)) or not isinstance(post, (int, float)):
            continue
        if abs(prior) >= MAX_PRIOR_DRIFT:
            continue
        clean.append(r)
    return clean


def policy_narrative_dimension(policy_evidence: Optional[dict], direction: str) -> float:
    """Score the sector's reaction to the labeled policy event.

    Any timing violation (run-up drift, no clean reactions, no meaningful
    post-policy move) scores neutral (50) — never a fabricated signal.
    """
    clean = _clean_policy_reactions(policy_evidence)
    if not clean:
        return 50.0
    post = sum(r["post_return"] for r in clean) / len(clean)
    if abs(post) < MIN_POLICY_REACTION:
        return 50.0
    factor = -1.0 if direction == "below" else 1.0
    return round(max(0.0, min(100.0, 50.0 + factor * post * POLICY_REACTION_SCALE)), 2)


class EvidenceJudge:
    def assess(self, claim: Claim, evidence: dict, skeptic: Optional[SkepticOutput] = None) -> EvidenceAssessment:
        evidence_summary = {}
        contradictions: list[str] = []
        contradictions_i18n: list[dict] = []

        def _add(en: str, id_: str) -> None:
            """Record a contradiction in both languages (EN canonical list kept
            for compatibility; the i18n list drives the localised result page)."""
            contradictions.append(en)
            contradictions_i18n.append({"en": en, "id": id_})

        valuation = evidence.get("valuation")
        fundamental = evidence.get("fundamental")
        market = evidence.get("market")
        news = evidence.get("news")
        policy = evidence.get("policy")
        corporate_actions = evidence.get("corporate_actions")
        filings = evidence.get("filings")

        if valuation:
            evidence_summary["valuation"] = valuation.model_dump(mode="json") if hasattr(valuation, "model_dump") else valuation
        if fundamental:
            evidence_summary["fundamental"] = fundamental.model_dump(mode="json") if hasattr(fundamental, "model_dump") else fundamental
        if market:
            evidence_summary["market"] = market.model_dump(mode="json") if hasattr(market, "model_dump") else market
        if news:
            evidence_summary["news"] = news.model_dump(mode="json") if hasattr(news, "model_dump") else news
        if policy:
            evidence_summary["policy"] = policy.model_dump(mode="json") if hasattr(policy, "model_dump") else policy
        if corporate_actions:
            evidence_summary["corporate_actions"] = corporate_actions.model_dump(mode="json") if hasattr(corporate_actions, "model_dump") else corporate_actions
        if filings:
            evidence_summary["filings"] = filings.model_dump(mode="json") if hasattr(filings, "model_dump") else filings

        if valuation and fundamental:
            v_metrics = valuation.metrics if hasattr(valuation, "metrics") else {}
            f_metrics = fundamental.metrics if hasattr(fundamental, "metrics") else {}
            pe = v_metrics.get("pe")
            earnings_trend = (fundamental.trend if hasattr(fundamental, "trend") else {}).get("earnings_trend")
            if pe and pe > 30 and earnings_trend == "improving":
                _add(
                    "High PE but improving earnings suggests growth premium, not overvaluation",
                    "PE tinggi namun laba membaik menunjukkan premi pertumbuhan, bukan overvaluasi",
                )

        if news and claim.category.value != "valuation":
            corroboration = news.corroboration if hasattr(news, "corroboration") else "neutral"
            if corroboration == "contradicts":
                _add(
                    "Recent news contradicts the claim's direction",
                    "Berita terbaru bertentangan dengan arah klaim",
                )

        # T5: a sector that reacts against the claim's direction is a contradiction —
        # but only for non-valuation categories (anti-dilution guardrail).
        if policy and claim.category.value != "valuation":
            clean = _clean_policy_reactions(evidence_summary.get("policy"))
            if clean:
                post = sum(r["post_return"] for r in clean) / len(clean)
                direction = claim.direction.value
                contradicts = (
                    (direction == "below" and post >= MIN_POLICY_REACTION)
                    or (direction == "above" and post <= -MIN_POLICY_REACTION)
                )
                if contradicts:
                    _add(
                        "The sector's reaction to the policy announcement contradicts the claim's direction",
                        "Reaksi sektor terhadap pengumuman kebijakan bertentangan dengan arah klaim",
                    )

        if corporate_actions:
            relevant = corporate_actions.relevant_events if hasattr(corporate_actions, "relevant_events") else []
            if relevant and market:
                perf_1d = (market.performance if hasattr(market, "performance") else {}).get("1d", {})
                change = perf_1d.get("price_change_pct", 0)
                if abs(change or 0) > 2:
                    names = ", ".join(relevant[:3])
                    _add(
                        f"Price movement may be explained by corporate actions ({names})",
                        f"Pergerakan harga dapat dijelaskan oleh aksi korporasi ({names})",
                    )

        # Flow that runs against the claim's direction is a contradiction — but,
        # like news/policy, it must not dilute a valuation claim.
        if market and claim.category.value != "valuation":
            flow = (evidence_summary.get("market") or {}).get("flow_summary")
            alignment = direction_factor(claim.direction.value) * flow_net_signal(flow)
            if alignment <= -FLOW_CONTRADICTION_THRESHOLD:
                _add(
                    "Foreign/broker flow moved against the claim's direction",
                    "Arus asing/broker bergerak berlawanan dengan arah klaim",
                )

        if filings:
            recent_bias = filings.recent_bias if hasattr(filings, "recent_bias") else "balanced"
            if recent_bias == "net_selling":
                _add(
                    "Insiders are net selling — bearish signal that may contradict bullish narratives",
                    "Insider net sell — sinyal bearish yang dapat bertentangan dengan narasi bullish",
                )
            elif recent_bias == "net_buying":
                _add(
                    "Insiders are net buying — bullish signal that may contradict bearish narratives",
                    "Insider net buy — sinyal bullish yang dapat bertentangan dengan narasi bearish",
                )

        applicable_dimensions = []
        cat = claim.category.value
        if cat == "valuation":
            applicable_dimensions = ["valuation_gap", "peer_relative_gap", "evidence_confidence"]
        elif cat == "fundamental":
            applicable_dimensions = ["earnings_gap", "policy_narrative_gap", "evidence_confidence", "market_momentum_gap"]
        elif cat == "market":
            applicable_dimensions = ["market_momentum_gap", "policy_narrative_gap", "evidence_confidence", "valuation_gap"]
        elif cat == "peer_comparison":
            applicable_dimensions = ["peer_relative_gap", "evidence_confidence", "valuation_gap"]
        elif cat == "insider_trading":
            applicable_dimensions = ["insider_bias_gap", "evidence_confidence", "market_momentum_gap"]

        if cat == "valuation":
            # Valuation claims are judged strictly on intrinsic/relative ratios.
            # Market flow and news sentiment must NOT dilute evidence confidence.
            evidence_count = sum(1 for v in [valuation, fundamental] if v is not None)
        else:
            evidence_count = sum(1 for v in [valuation, fundamental, market, news, corporate_actions, filings] if v is not None)
        confidence = min(1.0, evidence_count / (2.0 if cat == "valuation" else 3.0))
        if skeptic and skeptic.skepticism_score > 70:
            confidence *= 0.8

        return EvidenceAssessment(
            claim_ticker=claim.ticker,
            claim_category=cat,
            direction=claim.direction.value,
            evidence_summary=evidence_summary,
            contradictions=contradictions,
            contradictions_i18n=contradictions_i18n,
            skeptic_challenges=[c.get("point", "") for c in (skeptic.counter_arguments if skeptic else [])],
            evidence_confidence=round(confidence, 2),
            applicable_dimensions=applicable_dimensions,
        )


class ScoreGenerator:
    DIMENSION_WEIGHTS = {
        "valuation": {"valuation_gap": 0.4, "peer_relative_gap": 0.3, "evidence_confidence": 0.3},
        "fundamental": {"earnings_gap": 0.3, "policy_narrative_gap": 0.2, "evidence_confidence": 0.3, "market_momentum_gap": 0.2},
        "market": {"market_momentum_gap": 0.4, "policy_narrative_gap": 0.2, "evidence_confidence": 0.3, "valuation_gap": 0.1},
        "peer_comparison": {"peer_relative_gap": 0.5, "evidence_confidence": 0.3, "valuation_gap": 0.2},
        "insider_trading": {"insider_bias_gap": 0.5, "evidence_confidence": 0.3, "market_momentum_gap": 0.2},
    }

    VERDICT_BANDS = [
        (30, VerdictBand.CONTRADICTED),
        (60, VerdictBand.MIXED),
        (80, VerdictBand.SUPPORTED),
        (100, VerdictBand.STRONGLY_SUPPORTED),
    ]

    BAND_RANK = {
        VerdictBand.CONTRADICTED: 0,
        VerdictBand.MIXED: 1,
        VerdictBand.SUPPORTED: 2,
        VerdictBand.STRONGLY_SUPPORTED: 3,
    }

    def _band_for_score(self, total_score: float) -> VerdictBand:
        verdict = VerdictBand.CONTRADICTED
        for threshold, band in self.VERDICT_BANDS:
            if total_score <= threshold:
                verdict = band
                break
        return verdict

    @staticmethod
    def _direction_factor(direction: str) -> float:
        return direction_factor(direction)

    def _flow_momentum_adjustment(self, flow_summary: Optional[dict], direction: str) -> float:
        """Bounded corroboration from foreign/broker flow, in score points.

        Positive flow (foreign inflow / broker net buy) is price-supportive: it
        corroborates an "above" claim and undercuts a "below" one. Returns 0
        when no clear bias is present — flow never fabricates signal.
        """
        signal = flow_net_signal(flow_summary)
        if not signal:
            return 0.0
        return direction_factor(direction) * signal * FLOW_MOMENTUM_WEIGHT

    def _market_mover_adjustment(self, movers: Optional[dict], direction: str) -> float:
        """Small bounded nudge when the ticker is an extreme market mover."""
        if not movers:
            return 0.0
        classification = movers.get("classification")
        if classification == "top_gainers":
            signal = 1.0
        elif classification == "top_losers":
            signal = -1.0
        else:
            return 0.0
        return direction_factor(direction) * signal * MARKET_MOVER_WEIGHT

    def _momentum_tension_note(self, evidence_summary: dict, direction: str) -> str:
        """Explain a dimension propped up by flow while the index-relative move opposes.

        The score sums corroboration (flow/movers) on top of the beta-adjusted
        move, so a bullish claim can read supportive even when the stock lagged
        IHSG. This note keeps that tension visible in the human-facing summary.
        """
        market = evidence_summary.get("market") or {}
        relative = (market.get("relative_strength") or {}).get("1d")
        if not isinstance(relative, (int, float)) or relative == 0:
            return ""
        if direction_factor(direction) * relative >= 0:
            return ""  # relative move does not oppose the claim

        flow = flow_net_signal(market.get("flow_summary"))
        classification = (market.get("market_movers") or {}).get("classification")
        mover = 1.0 if classification == "top_gainers" else -1.0 if classification == "top_losers" else 0.0
        if direction_factor(direction) * (flow + mover) <= 0:
            return ""  # nothing is propping it up; not a tension case

        return (
            f"Momentum ditopang arus dana/broker meski pergerakan relatif saham "
            f"terhadap indeks berlawanan arah klaim (relatif 1H {relative}%). / "
            f"Momentum is propped up by fund/broker flow even though the stock's "
            f"move relative to the index runs against the claim (1d relative {relative}%)."
        )

    @staticmethod
    def _premium_support(premium: float, direction: str) -> float:
        # Alignment between the premium's sign and the claim's direction.
        if direction == "below":
            signal = -premium
        elif direction in ("between", "neutral"):
            signal = -abs(premium)
        else:  # above
            signal = premium
        return max(0.0, min(100.0, 50.0 + signal / 2.0))

    def _agreement_direction(self, evidence_summary: dict) -> Optional[str]:
        """If every available valuation ratio (PE, PB, PS, forward PE) agrees
        strictly on direction, return that direction; otherwise None."""
        valuation = evidence_summary.get("valuation") or {}
        premiums = list((valuation.get("premium_pct") or {}).values())
        metrics = valuation.get("metrics") or {}
        forward_pe = metrics.get("forward_pe")
        median_pe = (valuation.get("subsector_median") or {}).get("pe")
        if forward_pe and median_pe:
            premiums.append((forward_pe - median_pe) / median_pe * 100.0)
        ratios = [p for p in premiums if isinstance(p, (int, float))]
        if len(ratios) < 2:
            return None
        signs = {">" if r > 0 else "<" if r < 0 else "=" for r in ratios}
        if len(signs) != 1 or "=" in signs:
            return None
        return "above" if ">" in signs else "below"

    def _quality_premium_note(self, evidence_summary: dict, direction: str) -> str:
        """Contextualize a rich valuation with banking health — never a score penalty."""
        valuation = evidence_summary.get("valuation") or {}
        health = valuation.get("health") or {}
        roe = health.get("roe")
        premium_pct = valuation.get("premium_pct") or {}
        rich = (premium_pct.get("pe") or 0) > 0 or (premium_pct.get("pb") or 0) > 0
        if direction == "above" and rich and isinstance(roe, (int, float)) and roe >= 15:
            return (
                f"Premium sebagian merefleksikan kualitas emiten (ROE {roe:.1f}%), "
                "bukan murni overvaluasi. / Part of the premium reflects a quality premium "
                f"(ROE {roe:.1f}%), not pure overvaluation."
            )
        return ""

    def compute(self, assessment: EvidenceAssessment, skeptic_score: float = 50.0) -> RealityGapScore:
        cat = assessment.claim_category
        weights = self.DIMENSION_WEIGHTS.get(cat, self.DIMENSION_WEIGHTS["valuation"])
        direction = getattr(assessment, "direction", "neutral") or "neutral"

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
                    dim_score = self._premium_support(pe_premium, direction) if pe_premium is not None else 50.0
                else:
                    dim_score = 50.0
            elif dim == "earnings_gap":
                fundamental = evidence_summary.get("fundamental")
                if fundamental:
                    trend = fundamental.get("trend", {}).get("earnings_trend")
                    if trend == "improving":
                        dim_score = 75.0 if direction in ("above", "neutral", "between") else 25.0
                    elif trend == "declining":
                        dim_score = 75.0 if direction == "below" else 25.0
                    else:
                        dim_score = 50.0
                else:
                    dim_score = 50.0
            elif dim == "market_momentum_gap":
                market = evidence_summary.get("market")
                if market:
                    perf = (market.get("performance") or {}).get("1d", {}) or {}
                    relative = (market.get("relative_strength") or {}).get("1d")
                    # Prefer the beta-adjusted (index-excess) move when available:
                    # +3% while IHSG is +5% is underperformance, not strength.
                    change = relative if isinstance(relative, (int, float)) else perf.get("price_change_pct", 0)
                    dim_score = 50 + self._direction_factor(direction) * change * 5
                    dim_score += self._flow_momentum_adjustment(market.get("flow_summary"), direction)
                    dim_score += self._market_mover_adjustment(market.get("market_movers"), direction)
                    dim_score = max(0, min(100, dim_score))
                else:
                    dim_score = 50.0
            elif dim == "peer_relative_gap":
                valuation = evidence_summary.get("valuation")
                if valuation:
                    pb_premium = (valuation.get("premium_pct", {}) or {}).get("pb")
                    dim_score = self._premium_support(pb_premium, direction) if pb_premium is not None else 50.0
                else:
                    dim_score = 50.0
            elif dim == "insider_bias_gap":
                filings = evidence_summary.get("filings")
                if filings:
                    recent_bias = filings.get("recent_bias", "balanced")
                    if recent_bias == "net_buying":
                        dim_score = 75.0 if direction in ("above", "neutral", "between") else 25.0
                    elif recent_bias == "net_selling":
                        dim_score = 75.0 if direction == "below" else 25.0
                    else:
                        dim_score = 50.0
                else:
                    dim_score = 50.0
            elif dim == "policy_narrative_gap":
                policy = evidence_summary.get("policy")
                dim_score = policy_narrative_dimension(policy, direction) if policy else 50.0
            else:
                dim_score = 50.0

            dimensions[dim] = round(dim_score, 2)
            total_score += dim_score * weight

        skeptic_adjustment = (100 - skeptic_score) / 100 * 0.1
        total_score = total_score * (0.9 + skeptic_adjustment)
        total_score = max(0, min(100, total_score))

        verdict = self._band_for_score(total_score)

        # GUARDRAIL: if 100% of the valuation ratios agree with (or against) the
        # claim's direction, the verdict cannot sit in the ambiguous MIXED band.
        if cat == "valuation" and direction in ("above", "below"):
            agreement = self._agreement_direction(evidence_summary)
            if agreement is not None:
                if agreement == direction and self.BAND_RANK[verdict] < self.BAND_RANK[VerdictBand.SUPPORTED]:
                    verdict = VerdictBand.SUPPORTED
                    total_score = max(total_score, 61.0)
                elif agreement != direction and self.BAND_RANK[verdict] > self.BAND_RANK[VerdictBand.CONTRADICTED]:
                    verdict = VerdictBand.CONTRADICTED
                    total_score = min(total_score, 30.0)

        quality_note = self._quality_premium_note(evidence_summary, direction)
        momentum_note = self._momentum_tension_note(evidence_summary, direction)
        explanation = self._build_explanation(
            assessment, dimensions, verdict, "id",
            quality_note=quality_note, momentum_note=momentum_note,
        )
        explanation_en = self._build_explanation(
            assessment, dimensions, verdict, "en",
            quality_note=quality_note, momentum_note=momentum_note,
        )

        return RealityGapScore(
            claim_ticker=assessment.claim_ticker,
            claim_category=cat,
            reality_gap_score=round(total_score, 2),
            verdict=verdict,
            dimensions=dimensions,
            explanation=explanation,
            explanation_en=explanation_en,
            confidence=assessment.evidence_confidence,
            direction=direction,
        )

    @staticmethod
    def _contradictions_for(assessment: EvidenceAssessment, language: str) -> list[str]:
        """Localised contradiction texts, falling back to the canonical EN list."""
        items = getattr(assessment, "contradictions_i18n", None) or []
        if items:
            key = "en" if language == "en" else "id"
            return [c.get(key) or c.get("en", "") for c in items]
        return list(assessment.contradictions)

    def _build_explanation(self, assessment: EvidenceAssessment, dimensions: dict, verdict: VerdictBand, language: str = "id", quality_note: str = "", momentum_note: str = "") -> str:
        if language == "en":
            parts = [f"Verdict: {verdict.value.replace('_', ' ').title()}"]

            en_contradictions = self._contradictions_for(assessment, "en")
            if en_contradictions:
                parts.append(f"Contradictions found: {'; '.join(en_contradictions[:2])}")

            if assessment.skeptic_challenges:
                parts.append(f"Skeptic challenges: {len(assessment.skeptic_challenges)} counter-arguments")

            top_dim = max(dimensions.items(), key=lambda x: x[1]) if dimensions else None
            if top_dim:
                parts.append(f"Strongest dimension: {top_dim[0]} ({top_dim[1]:.0f}/100)")

            parts.append(f"Evidence confidence: {assessment.evidence_confidence:.0%}")
            if quality_note:
                parts.append(quality_note.split(" / ")[-1])
            if momentum_note:
                parts.append(momentum_note.split(" / ")[-1])
            return ". ".join(parts) + "."

        verdict_names = {
            "contradicted": "Bertentangan",
            "mixed": "Campuran",
            "supported": "Didukung",
            "strongly_supported": "Sangat Didukung",
        }
        verdict_label = verdict_names.get(verdict.value, verdict.value.replace("_", " ").title())
        parts = [f"Verdik: {verdict_label}"]

        id_contradictions = self._contradictions_for(assessment, "id")
        if id_contradictions:
            parts.append(f"Kontradiksi ditemukan: {'; '.join(id_contradictions[:2])}")

        if assessment.skeptic_challenges:
            parts.append(f"Tantangan skeptis: {len(assessment.skeptic_challenges)} argumen balasan")

        top_dim = max(dimensions.items(), key=lambda x: x[1]) if dimensions else None
        if top_dim:
            parts.append(f"Dimensi terkuat: {top_dim[0]} ({top_dim[1]:.0f}/100)")

        parts.append(f"Keyakinan bukti: {assessment.evidence_confidence:.0%}")
        if quality_note:
            parts.append(quality_note.split(" / ")[0])
        if momentum_note:
            parts.append(momentum_note.split(" / ")[0])
        return ". ".join(parts) + "."


evidence_judge = EvidenceJudge()
score_generator = ScoreGenerator()
