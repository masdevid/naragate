from datetime import datetime

from app.core.evidence_cache import cache
from app.core.sectors_client import sectors_client
from app.core.usage_tracker import record_sectors_cache_hit
from app.models.schemas import Claim, FilingsEvidence


class FilingsAgent:
    async def analyze(self, claim: Claim) -> FilingsEvidence:
        ticker = claim.ticker

        cached = await cache.get(ticker)
        if cached and "filings" in cached and cached["filings"] != {}:
            # A bare {} means the now-fixed invalid-param request (400) got cached
            # once and would otherwise shadow real data forever. Self-heal.
            filings_data = cached["filings"]
            cache_hit = True
            record_sectors_cache_hit()
        else:
            try:
                filings_data = await sectors_client.get_filings(ticker)
            except Exception:
                filings_data = {}
            await cache.merge(ticker, "filings", filings_data)
            cache_hit = False

        filings = []
        if isinstance(filings_data, dict):
            items = (
                filings_data.get("results")
                or filings_data.get("data")
                or filings_data.get("filings")
                or filings_data.get("items")
                or []
            )
        elif isinstance(filings_data, list):
            items = filings_data
        else:
            items = []

        if isinstance(items, list):
            for item in items[:10]:
                if isinstance(item, dict):
                    tx_raw = (str(item.get("transaction_type") or item.get("type") or "")).lower()
                    if "buy" in tx_raw:
                        tx = "buy"
                    elif "sell" in tx_raw:
                        tx = "sell"
                    else:
                        tx = tx_raw or "others"
                    filings.append({
                        "date": item.get("timestamp") or item.get("date") or item.get("transaction_date") or "",
                        "insider_name": item.get("holder_name") or item.get("insider_name") or item.get("name") or "",
                        "insider_title": item.get("holder_type") or item.get("insider_title") or item.get("title") or item.get("position") or "",
                        "transaction_type": tx,
                        "shares": item.get("amount_transaction") or item.get("shares") or item.get("volume") or 0,
                        "price": item.get("price") or item.get("avg_price") or 0,
                        "total_value": item.get("transaction_value") or item.get("total_value") or item.get("value") or 0,
                    })

        total_buy_shares = sum(f["shares"] for f in filings if "buy" in (f.get("transaction_type") or "").lower())
        total_sell_shares = sum(f["shares"] for f in filings if "sell" in (f.get("transaction_type") or "").lower())

        if total_buy_shares > total_sell_shares * 1.5:
            recent_bias = "net_buying"
        elif total_sell_shares > total_buy_shares * 1.5:
            recent_bias = "net_selling"
        else:
            recent_bias = "balanced"

        buy_count = sum(1 for f in filings if "buy" in (f.get("transaction_type") or "").lower())
        sell_count = sum(1 for f in filings if "sell" in (f.get("transaction_type") or "").lower())

        if filings:
            summary = (
                f"Terdapat {len(filings)} transaksi insider: "
                f"{buy_count} pembelian, {sell_count} penjualan. "
                f"Pola: {recent_bias}."
            )
            summary_en = (
                f"{len(filings)} insider transactions: "
                f"{buy_count} buys, {sell_count} sells. "
                f"Bias: {recent_bias}."
            )
        else:
            summary = "Tidak ada data transaksi insider yang tersedia."
            summary_en = "No insider transaction data available."

        return FilingsEvidence(
            claim_ticker=ticker,
            category="insider_trading",
            filings=filings,
            summary=summary,
            summary_en=summary_en,
            recent_bias=recent_bias,
            evidence_freshness=datetime.now().isoformat(),
            cache_hit=cache_hit,
        )


filings_agent = FilingsAgent()
