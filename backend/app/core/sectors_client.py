import re
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

    async def _get(self, path: str, params: dict | None = None) -> Any:
        headers = {"Authorization": sectors_api_key()}
        response = await self.client.get(path, params=params, headers=headers)
        record_sectors_call(endpoint=path)
        response.raise_for_status()
        return response.json()

    async def get_company_report(self, ticker: str, sections: list[str]) -> dict:
        return await self._get(f"/v2/company/report/{ticker}/", params={"sections": ",".join(sections)})

    async def get_quarterly_financials(self, ticker: str, n_quarters: int = 8) -> list:
        return await self._get(f"/v2/financials/quarterly/{ticker}/", params={"n_quarters": n_quarters})

    async def get_subsector_report(self, sub_sector: str, sections: list[str] | None = None) -> dict:
        params = {"sections": ",".join(sections)} if sections else None
        return await self._get(f"/v2/subsector/report/{sub_sector}/", params=params)

    async def get_daily_transaction(self, ticker: str) -> list:
        return await self._get(f"/v2/daily/{ticker}/")

    async def get_news(self, ticker: str, limit: int = 20) -> dict:
        return await self._get(f"/v2/news/", params={"symbols": ticker, "limit": limit})

    async def get_corporate_actions(self, ticker: str) -> dict:
        return await self._get(f"/v2/company/corporate-actions/{ticker}/")

    async def get_filings(self, ticker: str, filing_type: str = "insider_trade") -> dict:
        return await self._get("/v2/filings/", params={"symbol": ticker, "type": filing_type})


sectors_client = SectorsClient()
