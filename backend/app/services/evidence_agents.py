from datetime import date, datetime
from typing import Optional

from app.core.sectors_client import sectors_client, to_slug
from app.core.evidence_cache import cache
from app.core.usage_tracker import record_sectors_cache_hit
from app.config.settings import settings
from app.services.policy_signal import daily_epoch_chunks, DAILY_CHUNK_TTL
from app.models.schemas import (
    Claim, ValuationEvidence, FundamentalEvidence, MarketEvidence
)
from app.services.news_agent import news_agent
from app.services.corporate_actions_agent import corporate_actions_agent
from app.services.filings_agent import filings_agent, FilingsAgent


class ValuationAgent:
    async def analyze(self, claim: Claim) -> ValuationEvidence:
        ticker = claim.ticker

        cached = await cache.get(ticker)
        company_data = (cached or {}).get("company_report")
        if company_data and "overview" in company_data and "valuation" in company_data:
            cache_hit = True
            record_sectors_cache_hit()
        else:
            company_data = await sectors_client.get_company_report(
                ticker, ["valuation", "overview", "financials"]
            )
            await cache.merge(ticker, "company_report", company_data)
            cache_hit = False

        sub_sector_name = ((company_data or {}).get("overview") or {}).get("sub_sector")
        sub_sector_slug = to_slug(sub_sector_name) if sub_sector_name else None

        subsector_data = None
        if sub_sector_slug:
            if cached and "subsector_report" in cached:
                subsector_data = cached["subsector_report"]
                record_sectors_cache_hit()
            else:
                subsector_data = await sectors_client.get_subsector_report(
                    sub_sector_slug, ["statistics", "valuation"]
                )
                await cache.merge(ticker, "subsector_report", subsector_data)

        valuation = {}
        if company_data and "valuation" in company_data:
            v = company_data["valuation"]
            hv = v.get("historical_valuation") or []
            latest = hv[-1] if hv else {}
            valuation = {
                "pe": latest.get("pe"),
                "pb": latest.get("pb"),
                "ps": latest.get("ps"),
                "pcf": latest.get("pcf"),
                "forward_pe": v.get("forward_pe"),
                "last_close_price": v.get("last_close_price"),
            }

        subsector_median = {}
        if subsector_data:
            hv = ((subsector_data.get("valuation") or {}).get("historical_valuation") or {})
            if hv:
                latest_year = max(hv.keys())
                m = hv[latest_year]
                subsector_median = {
                    "pe": m.get("pe"),
                    "pb": m.get("pb"),
                    "ps": m.get("ps"),
                }
            if not subsector_median.get("pe"):
                stats = subsector_data.get("statistics") or {}
                subsector_median["pe"] = stats.get("filtered_median_pe")

        premium_pct = {}
        for metric in ["pe", "pb", "ps"]:
            stock_val = valuation.get(metric)
            median_val = subsector_median.get(metric)
            if stock_val and median_val and median_val != 0:
                premium_pct[metric] = round((stock_val - median_val) / median_val * 100, 2)
            else:
                premium_pct[metric] = None

        health = self._extract_health_metrics(company_data)

        return ValuationEvidence(
            claim_ticker=ticker,
            category="valuation",
            metrics=valuation,
            subsector_median=subsector_median,
            premium_pct=premium_pct,
            evidence_freshness=datetime.now().isoformat(),
            cache_hit=cache_hit,
            health=health,
        )

    def _extract_health_metrics(self, company_data: Optional[dict]) -> dict:
        """Banking-health/quality context from the financials section.
        Never empties the cache; these keys are reused from the same company report."""
        health = {}
        if not company_data:
            return health
        f = company_data.get("financials") or {}
        ratios = f.get("historical_financial_ratio") or []
        latest = ratios[-1] if ratios else {}
        profitability = latest.get("profitability") or {}
        if isinstance(profitability.get("roe"), (int, float)):
            health["roe"] = profitability["roe"]
        if isinstance(profitability.get("roa"), (int, float)):
            health["roa"] = profitability["roa"]
        if isinstance(profitability.get("net_profit_margin"), (int, float)):
            health["net_profit_margin"] = profitability["net_profit_margin"]
        # Banking indicators — field names vary across Sectors releases; probe
        # commonly-observed keys and keep every candidate that is present.
        for key in ("nim", "npl", "loan_growth", "liquidity"):
            if key in profitability and isinstance(profitability[key], (int, float)):
                health[key] = profitability[key]
        liquidity = latest.get("liquidity") or {}
        for key in ("nim", "npl", "loan_growth"):
            if key in liquidity and isinstance(liquidity[key], (int, float)):
                health[key] = liquidity[key]
        return health


class FundamentalAgent:
    @staticmethod
    def _summarize_segments(data) -> dict | None:
        """Compact revenue-segment view from `company/get-segments`.

        Documented shape: {financial_year, revenue_breakdown: [{value, source, target}]}.
        Not every company has segment data (404); that degrades to None.
        """
        if not isinstance(data, dict):
            return None
        breakdown = data.get("revenue_breakdown")
        if not isinstance(breakdown, list) or not breakdown:
            return None
        totals: dict[str, float] = {}
        for row in breakdown:
            if not isinstance(row, dict):
                continue
            source, value = row.get("source"), row.get("value")
            if isinstance(source, str) and isinstance(value, (int, float)):
                totals[source] = totals.get(source, 0) + value
        if not totals:
            return None
        total = sum(totals.values()) or 1
        top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:6]
        return {
            "financial_year": data.get("financial_year"),
            "top_sources": [
                {"source": source, "value": value, "share_pct": round(value / total * 100, 2)}
                for source, value in top
            ],
        }

    async def analyze(self, claim: Claim) -> FundamentalEvidence:
        ticker = claim.ticker

        cached = await cache.get(ticker)
        company_data = (cached or {}).get("company_report")
        if company_data and "financials" in company_data:
            cache_hit = True
            record_sectors_cache_hit()
        else:
            company_data = await sectors_client.get_company_report(
                ticker, ["valuation", "overview", "financials"]
            )
            await cache.merge(ticker, "company_report", company_data)
            cache_hit = False

        quarterly_data = None
        if cached and "quarterly_financials" in cached:
            quarterly_data = cached["quarterly_financials"]
            record_sectors_cache_hit()
        else:
            quarterly_data = await sectors_client.get_quarterly_financials(ticker)
            await cache.merge(ticker, "quarterly_financials", quarterly_data)

        segments_raw = None
        if cached and "segments" in cached:
            segments_raw = cached["segments"]
            record_sectors_cache_hit()
        else:
            try:
                segments_raw = await sectors_client.get_segments(ticker)
            except Exception:
                segments_raw = None
            if segments_raw:
                await cache.merge(ticker, "segments", segments_raw)

        metrics = {}
        if company_data and "financials" in company_data:
            f = company_data["financials"]
            hf = f.get("historical_financials") or []
            latest_f = hf[-1] if hf else {}
            hfr = f.get("historical_financial_ratio") or []
            latest_r = hfr[-1] if hfr else {}
            profitability = latest_r.get("profitability") or {}
            leverage = latest_r.get("leverage") or {}
            metrics = {
                "revenue": latest_f.get("revenue"),
                "earnings": latest_f.get("earnings"),
                "eps": f.get("eps"),
                "net_profit_margin": profitability.get("net_profit_margin"),
                "roe": profitability.get("roe"),
                "roa": profitability.get("roa"),
                "debt_to_equity": leverage.get("debt_to_equity_ratio"),
                "yoy_quarter_earnings_growth": f.get("yoy_quarter_earnings_growth"),
                "yoy_quarter_revenue_growth": f.get("yoy_quarter_revenue_growth"),
            }

        trend = {"revenue_trend": "stable", "earnings_trend": "stable", "quarters_analyzed": 0}
        if quarterly_data and isinstance(quarterly_data, list) and len(quarterly_data) >= 2:
            quarters = quarterly_data[:4]
            trend["quarters_analyzed"] = len(quarters)

            revenues = [q.get("revenue", 0) for q in quarters if q.get("revenue")]
            earnings = [q.get("earnings", 0) for q in quarters if q.get("earnings")]

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
            segments=self._summarize_segments(segments_raw),
        )


class MarketAgent:
    async def _enrich(self, ticker: str, key: str, cached: dict | None, fetcher, ttl: int):
        """Cache-first enrichment fetch for the Evidence Graph.

        Reuses the cached section (0 credits) when present; otherwise makes
        exactly one Sectors call and merges the result. A failed enrichment
        never fails the market claim — it degrades to no extra context.
        """
        if cached and key in cached:
            record_sectors_cache_hit()
            return cached[key]
        try:
            data = await fetcher()
        except Exception:
            return None
        if data:
            await cache.merge(ticker, key, data, ttl=ttl)
        return data

    @staticmethod
    def _summarize_flows(foreign_flow, broker_flow) -> dict:
        """Normalize foreign/broker flow into a compact summary.

        Documented shapes (docs.sectors.app/schema.json):
          foreign-flow:  {symbol, start, end, data: [{date, net_foreign_inflow}]}
          broker-summary:{symbol, start, end, data: [{date, summary: [{bval, sval, nval, ...}]}]}
        Alternate/flat shapes are still probed defensively so a schema change
        degrades to an empty summary rather than a wrong number.
        """
        summary: dict = {}

        rows = foreign_flow
        if isinstance(foreign_flow, dict):
            rows = foreign_flow.get("data") or foreign_flow.get("results") or foreign_flow.get("flow") or []
        if isinstance(rows, list):
            net = 0.0
            found = False
            for row in rows:
                if not isinstance(row, dict):
                    continue
                for k in ("net_foreign_inflow", "net_foreign", "foreign_net", "net", "net_buy"):
                    if isinstance(row.get(k), (int, float)):
                        net += row[k]
                        found = True
                        break
                else:
                    buy = row.get("foreign_buy") if isinstance(row.get("foreign_buy"), (int, float)) else row.get("buy")
                    sell = row.get("foreign_sell") if isinstance(row.get("foreign_sell"), (int, float)) else row.get("sell")
                    if isinstance(buy, (int, float)) or isinstance(sell, (int, float)):
                        net += (buy or 0) - (sell or 0)
                        found = True
            if found:
                summary["foreign_net"] = round(net, 2)
                summary["foreign_bias"] = "net_inflow" if net > 0 else "net_outflow" if net < 0 else "balanced"

        days = broker_flow
        if isinstance(broker_flow, dict):
            days = broker_flow.get("data") or broker_flow.get("results") or broker_flow.get("brokers") or []
        if isinstance(days, list):
            buy = sell = 0.0
            found = False
            for day in days:
                if not isinstance(day, dict):
                    continue
                # Documented shape nests per-broker rows under `summary`.
                nested = day.get("summary")
                broker_rows = nested if isinstance(nested, list) else [day]
                for row in broker_rows:
                    if not isinstance(row, dict):
                        continue
                    b = next((row.get(k) for k in ("bval", "buy_value", "buy") if isinstance(row.get(k), (int, float))), None)
                    s = next((row.get(k) for k in ("sval", "sell_value", "sell") if isinstance(row.get(k), (int, float))), None)
                    if isinstance(b, (int, float)):
                        buy += b
                        found = True
                    if isinstance(s, (int, float)):
                        sell += s
                        found = True
            if found:
                net = buy - sell
                summary["broker_net"] = round(net, 2)
                summary["broker_bias"] = "net_buy" if net > 0 else "net_sell" if net < 0 else "balanced"

        return summary

    @staticmethod
    def _find_in_movers(ticker: str, data) -> dict | None:
        """Locate the ticker in the top-gainers/losers payload, if present."""
        if not isinstance(data, dict):
            return None
        symbol = ticker.upper()
        for classification in ("top_gainers", "top_losers"):
            periods = data.get(classification) or {}
            if not isinstance(periods, dict):
                continue
            for period, rows in periods.items():
                if not isinstance(rows, list):
                    continue
                for i, row in enumerate(rows):
                    if not isinstance(row, dict):
                        continue
                    code = str(row.get("symbol") or "").split(".")[0].upper()
                    if code == symbol:
                        return {
                            "classification": classification,
                            "period": period,
                            "rank": i + 1,
                            "price_change": row.get("price_change"),
                        }
        return None

    async def _market_movers(self, ticker: str) -> dict | None:
        """Daily top-mover membership, cached market-wide (2 credits/day, shared
        by every claim). A cache miss on a whole day is still 0 per-claim credit
        once the day's ranking is warm."""
        day = date.today().isoformat()
        key = f"top-changes:{day}:1d"
        data = await cache.get_market(key)
        if data is None:
            try:
                data = await sectors_client.get_top_changes("top_gainers,top_losers", "1d", n_stock=10)
            except Exception:
                return None
            await cache.set_market(key, data, ttl=settings.EVIDENCE_CACHE_TTL_DAILY)
        else:
            record_sectors_cache_hit()
        return self._find_in_movers(ticker, data)

    async def _index_closes(self, index_code: str, start: date, end: date) -> dict | None:
        """Index closes keyed by date, assembled from the fixed 90-day epoch grid
        (a re-run reuses cached epochs, so only a new epoch costs a call)."""
        merged: dict[str, float] = {}
        for epoch_start, epoch_end, fetch_start, fetch_end in daily_epoch_chunks(start, end):
            rows = await cache.get_index_chunk(index_code, epoch_start.isoformat())
            if rows is None:
                try:
                    rows = await sectors_client.get_index_daily(
                        index_code, epoch_start.isoformat(), epoch_end.isoformat()
                    )
                except Exception:
                    return merged or None
                await cache.set_index_chunk(index_code, epoch_start.isoformat(), rows or [], ttl=DAILY_CHUNK_TTL)
            else:
                record_sectors_cache_hit()
            for row in rows or []:
                if not isinstance(row, dict):
                    continue
                day = str(row.get("date", ""))[:10]
                price = row.get("price")
                if day and fetch_start.isoformat() <= day <= fetch_end.isoformat() and isinstance(price, (int, float)):
                    merged[day] = price
        return merged or None

    async def _relative_strength(self, tx_data: list, prices: list, index_code: str = "ihsg") -> dict | None:
        """Stock return minus index return per window — the beta-adjusted move.

        `tx_data` is newest-first and `prices` aligns with it. Returns None when
        the index series is unavailable, so momentum falls back to the raw move.
        """
        if not prices or len(prices) < 2 or not tx_data:
            return None
        dates = [str(d.get("date", ""))[:10] for d in tx_data if isinstance(d, dict)]
        dates = [d for d in dates if d]
        if len(dates) < 2:
            return None
        try:
            start, end = date.fromisoformat(min(dates)), date.fromisoformat(max(dates))
        except ValueError:
            return None
        closes = await self._index_closes(index_code, start, end)
        if not closes:
            return None

        idx_dates = sorted(closes)

        def idx_on_or_before(target: str) -> float | None:
            prior = [d for d in idx_dates if d <= target]
            return closes[prior[-1]] if prior else None

        latest_idx = idx_on_or_before(dates[0])
        if not latest_idx:
            return None
        out: dict[str, float] = {}
        for window in (1, 7, 30):
            if len(prices) <= window or not prices[window]:
                continue
            base_idx = idx_on_or_before(dates[window])
            if not base_idx:
                continue
            stock_ret = (prices[0] - prices[window]) / prices[window] * 100
            idx_ret = (latest_idx - base_idx) / base_idx * 100
            out[f"{window}d"] = round(stock_ret - idx_ret, 2)
        return out or None

    async def analyze(self, claim: Claim) -> MarketEvidence:
        ticker = claim.ticker

        cached = await cache.get(ticker)
        if cached and "daily_transaction" in cached:
            tx_data = cached["daily_transaction"]
            cache_hit = True
            record_sectors_cache_hit()
        else:
            tx_data = await sectors_client.get_daily_transaction(ticker)
            await cache.merge(ticker, "daily_transaction", tx_data, ttl=settings.EVIDENCE_CACHE_TTL_DAILY)
            cache_hit = False

        foreign_flow = await self._enrich(
            ticker, "foreign_flow", cached,
            lambda: sectors_client.get_foreign_flow(ticker),
            settings.EVIDENCE_CACHE_TTL_DAILY,
        )
        broker_flow = await self._enrich(
            ticker, "broker_summary", cached,
            lambda: sectors_client.get_broker_summary(ticker),
            settings.EVIDENCE_CACHE_TTL_DAILY,
        )
        flow_summary = self._summarize_flows(foreign_flow, broker_flow)
        try:
            market_movers = await self._market_movers(ticker)
        except Exception:
            market_movers = None

        performance = {}
        volatility = 0.0
        prices: list = []
        relative_strength = None

        if tx_data and isinstance(tx_data, list) and len(tx_data) > 0:
            tx_data = list(reversed(tx_data))
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

            try:
                relative_strength = await self._relative_strength(tx_data, prices)
            except Exception:
                relative_strength = None

        return MarketEvidence(
            claim_ticker=ticker,
            category="market",
            performance=performance,
            volatility=volatility,
            evidence_freshness=datetime.now().isoformat(),
            cache_hit=cache_hit,
            foreign_flow=foreign_flow if isinstance(foreign_flow, (list, dict)) else None,
            broker_flow=broker_flow if isinstance(broker_flow, dict) else None,
            flow_summary=flow_summary or None,
            market_movers=market_movers,
            relative_strength=relative_strength,
        )


async def get_evidence_for_claim(claim: Claim) -> dict:
    agents = {
        "valuation": ValuationAgent(),
        "fundamental": FundamentalAgent(),
        "market": MarketAgent(),
        "insider_trading": FilingsAgent(),
    }

    evidence = {}

    agent = agents.get(claim.category.value)
    if agent:
        result = await agent.analyze(claim)
        evidence[claim.category.value] = result

    try:
        news = await news_agent.analyze(claim)
        evidence["news"] = news
    except Exception:
        pass

    try:
        corp = await corporate_actions_agent.analyze(claim)
        evidence["corporate_actions"] = corp
    except Exception:
        pass

    try:
        filings = await filings_agent.analyze(claim)
        evidence["filings"] = filings
    except Exception:
        pass

    return evidence
