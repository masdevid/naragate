import re
import time
from typing import Any

import httpx
from app.core.sectors_config import sectors_api_key
from app.core.usage_tracker import record_sectors_call


def to_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug


class SectorsClient:
    def __init__(self):
        self.base_url = "https://api.sectors.app"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            follow_redirects=True,
            timeout=10.0
        )
        self._company_cache: dict[str, Any] = {"tickers": set(), "ts": 0.0}
        self._subsector_cache: dict[str, Any] = {"slugs": set(), "ts": 0.0}
        self._CACHE_TTL = 86400  # 24 hours

    async def _get(self, path: str, params: dict | None = None) -> Any:
        headers = {"Authorization": sectors_api_key()}
        response = await self.client.get(path, params=params, headers=headers)
        response.raise_for_status()
        record_sectors_call(endpoint=path)
        return response.json()

    async def _get_raw(self, path: str, params: dict | None = None) -> httpx.Response:
        """Low-level GET that returns the response object without raising or recording."""
        headers = {"Authorization": sectors_api_key()}
        return await self.client.get(path, params=params, headers=headers)

    def validate_ticker(self, ticker: str) -> bool:
        """Quick format check for IDX tickers (4 uppercase letters). Free, no API call."""
        if not ticker or not isinstance(ticker, str):
            return False
        return bool(re.match(r'^[A-Z]{4}$', ticker))

    async def _ensure_company_cache(self) -> set[str]:
        """Fetch and cache all valid IDX tickers (once per 24 hours)."""
        now = time.time()
        if self._company_cache["tickers"] and (now - self._company_cache["ts"]) < self._CACHE_TTL:
            return self._company_cache["tickers"]

        try:
            resp = await self._get_raw("/v2/companies/", params={"limit": 10000})
            resp.raise_for_status()
            data = resp.json()
            symbols = {c.get("symbol", "") for c in data.get("results", []) if c.get("symbol")}
            if symbols:
                self._company_cache["tickers"] = symbols
                self._company_cache["ts"] = now
                record_sectors_call(endpoint="/v2/companies/")
        except Exception:
            pass

        return self._company_cache["tickers"]

    async def _ensure_subsector_cache(self) -> set[str]:
        """Fetch and cache all valid subsector slugs (once per 24 hours)."""
        now = time.time()
        if self._subsector_cache["slugs"] and (now - self._subsector_cache["ts"]) < self._CACHE_TTL:
            return self._subsector_cache["slugs"]

        try:
            resp = await self._get_raw("/v2/subsectors/")
            resp.raise_for_status()
            data = resp.json()
            slugs = {s.get("slug", "") for s in data if isinstance(s, dict) and s.get("slug")}
            if not slugs and isinstance(data, list):
                slugs = {s for s in data if isinstance(s, str)}
            if slugs:
                self._subsector_cache["slugs"] = slugs
                self._subsector_cache["ts"] = now
                record_sectors_call(endpoint="/v2/subsectors/")
        except Exception:
            pass

        return self._subsector_cache["slugs"]

    async def validate_ticker_exists(self, ticker: str) -> bool:
        """Full validation against cached company list."""
        tickers = await self._ensure_company_cache()
        if not tickers:
            return True
        return ticker in tickers

    async def validate_subsector(self, sub_sector: str) -> bool:
        """Validate subsector slug against cached subsector list."""
        slugs = await self._ensure_subsector_cache()
        if not slugs:
            return True
        return sub_sector in slugs

    async def get_company_report(self, ticker: str, sections: list[str]) -> dict:
        return await self._get(f"/v2/company/report/{ticker}/", params={"sections": ",".join(sections)})

    async def get_quarterly_financials(self, ticker: str, n_quarters: int = 8) -> list:
        return await self._get(f"/v2/financials/quarterly/{ticker}/", params={"n_quarters": n_quarters})

    async def get_subsector_report(self, sub_sector: str, sections: list[str] | None = None) -> dict:
        params = {"sections": ",".join(sections)} if sections else None
        return await self._get(f"/v2/subsector/report/{sub_sector}/", params=params)

    async def get_daily_transaction(self, ticker: str, start: str | None = None, end: str | None = None) -> list:
        params = {}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        return await self._get(f"/v2/daily/{ticker}/", params=params or None)

    async def get_news(self, ticker: str, limit: int = 20) -> dict:
        return await self._get(f"/v2/news/", params={"symbols": ticker, "limit": limit})

    async def get_corporate_actions(self, ticker: str) -> dict:
        return await self._get(f"/v2/company/corporate-actions/{ticker}/")

    async def get_filings(self, ticker: str, filing_type: str | None = None) -> dict:
        """Insider-trade filings for a ticker.

        The Sectors API does not accept a `type` query param (400 otherwise);
        it only allows transaction_type in {buy, sell, others}. The default
        call asks for all filings for the symbol.
        """
        params = {"symbol": ticker}
        if filing_type and filing_type in ("buy", "sell", "others"):
            params["transaction_type"] = filing_type
        return await self._get("/v2/filings/", params=params)


sectors_client = SectorsClient()
