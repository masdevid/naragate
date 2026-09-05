import re
from typing import Any

import httpx
from app.config.settings import settings
from app.core.usage_tracker import record_sectors_call


def to_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug


class SectorsClient:
    def __init__(self):
        self.base_url = "https://api.sectors.app"
        self.api_key = settings.SECTORS_API_KEY
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": self.api_key},
            follow_redirects=True,
            timeout=10.0
        )

    async def _get(self, path: str, params: dict | None = None) -> Any:
        response = await self.client.get(path, params=params)
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
        return await self._get(f"/v2/news/", params={"ticker": ticker, "limit": limit})

    async def get_corporate_actions(self, ticker: str) -> dict:
        return await self._get(f"/v2/company/corporate-actions/{ticker}/")


sectors_client = SectorsClient()
