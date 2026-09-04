import httpx
from app.config.settings import settings
from app.core.usage_tracker import record_sectors_call


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

    async def _get(self, path: str, params: dict | None = None) -> dict:
        response = await self.client.get(path, params=params)
        record_sectors_call(endpoint=path)
        response.raise_for_status()
        return response.json()

    async def get_company_report(self, ticker: str, sections: list[str]) -> dict:
        return await self._get(f"/v2/company/report/{ticker}/", params={"sections": ",".join(sections)})

    async def get_quarterly_financials(self, ticker: str) -> dict:
        return await self._get(f"/v2/company/quarterly-financials/{ticker}/")

    async def get_subsector_report(self, ticker: str) -> dict:
        return await self._get(f"/v2/company/subsector/{ticker}/")

    async def get_daily_transaction(self, ticker: str, window: str = "30D") -> dict:
        return await self._get(f"/v2/transaction/daily/{ticker}/", params={"window": window})

    async def get_news(self, ticker: str, limit: int = 20) -> dict:
        return await self._get(f"/v2/news/", params={"ticker": ticker, "limit": limit})

    async def get_corporate_actions(self, ticker: str) -> dict:
        return await self._get(f"/v2/company/corporate-actions/{ticker}/")


sectors_client = SectorsClient()
