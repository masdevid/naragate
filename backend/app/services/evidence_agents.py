from datetime import datetime
from typing import Optional

from app.core.sectors_client import sectors_client
from app.core.evidence_cache import cache
from app.config.settings import settings
from app.models.schemas import (
    Claim, ValuationEvidence, FundamentalEvidence, MarketEvidence
)


class ValuationAgent:
    async def analyze(self, claim: Claim) -> ValuationEvidence:
        ticker = claim.ticker

        cached = await cache.get(ticker)
        if cached and "company_report" in cached:
            company_data = cached["company_report"]
            cache_hit = True
        else:
            company_data = await sectors_client.get_company_report(ticker, ["valuation"])
            await cache.set(ticker, {"company_report": company_data})
            cache_hit = False

        subsector_data = None
        if cached and "subsector_report" in cached:
            subsector_data = cached["subsector_report"]
        else:
            subsector_data = await sectors_client.get_subsector_report(ticker)
            existing = cached or {}
            existing["subsector_report"] = subsector_data
            await cache.set(ticker, existing)

        valuation = {}
        if company_data and "valuation" in company_data:
            v = company_data["valuation"]
            valuation = {
                "pe": v.get("pe_ratio"),
                "pb": v.get("pb_ratio"),
                "ps": v.get("ps_ratio"),
                "pcf": v.get("pcf_ratio"),
            }

        subsector_median = {}
        if subsector_data and "median" in subsector_data:
            m = subsector_data["median"]
            subsector_median = {
                "pe": m.get("pe_ratio"),
                "pb": m.get("pb_ratio"),
                "ps": m.get("ps_ratio"),
            }

        premium_pct = {}
        for metric in ["pe", "pb", "ps"]:
            stock_val = valuation.get(metric)
            median_val = subsector_median.get(metric)
            if stock_val and median_val and median_val != 0:
                premium_pct[metric] = round((stock_val - median_val) / median_val * 100, 2)
            else:
                premium_pct[metric] = None

        return ValuationEvidence(
            claim_ticker=ticker,
            category="valuation",
            metrics=valuation,
            subsector_median=subsector_median,
            premium_pct=premium_pct,
            evidence_freshness=datetime.now().isoformat(),
            cache_hit=cache_hit,
        )


class FundamentalAgent:
    async def analyze(self, claim: Claim) -> FundamentalEvidence:
        ticker = claim.ticker

        cached = await cache.get(ticker)
        if cached and "company_report" in cached:
            company_data = cached["company_report"]
            cache_hit = True
        else:
            company_data = await sectors_client.get_company_report(ticker, ["financials"])
            await cache.set(ticker, {"company_report": company_data})
            cache_hit = False

        quarterly_data = None
        if cached and "quarterly_financials" in cached:
            quarterly_data = cached["quarterly_financials"]
        else:
            quarterly_data = await sectors_client.get_quarterly_financials(ticker)
            existing = cached or {}
            existing["quarterly_financials"] = quarterly_data
            await cache.set(ticker, existing)

        metrics = {}
        if company_data and "financials" in company_data:
            f = company_data["financials"]
            metrics = {
                "revenue": f.get("revenue"),
                "earnings": f.get("net_income"),
                "eps": f.get("eps"),
                "gross_margin": f.get("gross_margin"),
                "roe": f.get("roe"),
                "roa": f.get("roa"),
                "debt_to_equity": f.get("debt_to_equity"),
            }

        trend = {"revenue_trend": "stable", "earnings_trend": "stable", "quarters_analyzed": 0}
        if quarterly_data and isinstance(quarterly_data, list) and len(quarterly_data) >= 2:
            quarters = quarterly_data[:4]
            trend["quarters_analyzed"] = len(quarters)

            revenues = [q.get("revenue", 0) for q in quarters if q.get("revenue")]
            earnings = [q.get("net_income", 0) for q in quarters if q.get("net_income")]

            if len(revenues) >= 2:
                if revenues[0] > revenues[-1] * 1.05:
                    trend["revenue_trend"] = "improving"
                elif revenues[0] < revenues[-1] * 0.95:
                    trend["revenue_trend"] = "declining"

            if len(earnings) >= 2:
                if earnings[0] > earnings[-1] * 1.05:
                    trend["earnings_trend"] = "improving"
                elif earnings[0] < earnings[-1] * 0.95:
                    trend["earnings_trend"] = "declining"

        return FundamentalEvidence(
            claim_ticker=ticker,
            category="fundamental",
            metrics=metrics,
            trend=trend,
            evidence_freshness=datetime.now().isoformat(),
            cache_hit=cache_hit,
        )


class MarketAgent:
    async def analyze(self, claim: Claim) -> MarketEvidence:
        ticker = claim.ticker

        cached = await cache.get(ticker)
        if cached and "daily_transaction" in cached:
            tx_data = cached["daily_transaction"]
            cache_hit = True
        else:
            tx_data = await sectors_client.get_daily_transaction(ticker, window="30D")
            existing = cached or {}
            existing["daily_transaction"] = tx_data
            await cache.set(ticker, existing, ttl=settings.EVIDENCE_CACHE_TTL_DAILY)
            cache_hit = False

        performance = {}
        volatility = 0.0

        if tx_data and isinstance(tx_data, list) and len(tx_data) > 0:
            prices = [d.get("close", 0) for d in tx_data if d.get("close")]
            volumes = [d.get("volume", 0) for d in tx_data if d.get("volume")]

            if len(prices) >= 2:
                current = prices[0]
                if len(prices) >= 2:
                    performance["1d"] = {
                        "price_change_pct": round((prices[0] - prices[1]) / prices[1] * 100, 2) if prices[1] else 0,
                        "volume": volumes[0] if volumes else 0,
                    }
                if len(prices) >= 7:
                    performance["7d"] = {
                        "price_change_pct": round((prices[0] - prices[6]) / prices[6] * 100, 2) if prices[6] else 0,
                        "volume": sum(volumes[:7]) // min(7, len(volumes)),
                    }
                if len(prices) >= 30:
                    performance["30d"] = {
                        "price_change_pct": round((prices[0] - prices[29]) / prices[29] * 100, 2) if prices[29] else 0,
                        "volume": sum(volumes[:30]) // min(30, len(volumes)),
                    }

            if len(prices) >= 2:
                returns = [(prices[i] - prices[i+1]) / prices[i+1] for i in range(len(prices)-1) if prices[i+1]]
                if returns:
                    mean_ret = sum(returns) / len(returns)
                    variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
                    volatility = round(variance ** 0.5 * 100, 4)

        return MarketEvidence(
            claim_ticker=ticker,
            category="market",
            performance=performance,
            volatility=volatility,
            evidence_freshness=datetime.now().isoformat(),
            cache_hit=cache_hit,
        )


async def get_evidence_for_claim(claim: Claim) -> dict:
    agents = {
        "valuation": ValuationAgent(),
        "fundamental": FundamentalAgent(),
        "market": MarketAgent(),
    }

    agent = agents.get(claim.category.value)
    if agent:
        evidence = await agent.analyze(claim)
        return {claim.category.value: evidence}

    return {}
