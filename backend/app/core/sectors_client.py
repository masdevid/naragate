import httpx
from app.config.settings import settings

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

    async def get_company_report(self, ticker: str, sections: list[str]) -> dict:
        response = await self.client.get(f"/v2/company/report/{ticker}/", params={"sections": ",".join(sections)})
        response.raise_for_status()
        return response.json()

    async def get_quarterly_financials(self, ticker: str) -> dict:
        response = await self.client.get(f"/v2/company/quarterly-financials/{ticker}/")
        response.raise_for_status()
        return response.json()

    async def get_subsector_report(self, ticker: str) -> dict:
        response = await self.client.get(f"/v2/company/subsector/{ticker}/")
        response.raise_for_status()
        return response.json()

    async def get_daily_transaction(self, ticker: str, window: str = "30D") -> dict:
        response = await self.client.get(f"/v2/transaction/daily/{ticker}/", params={"window": window})
        response.raise_for_status()
        return response.json()

    async def get_news(self, ticker: str, limit: int = 20) -> dict:
        response = await self.client.get(f"/v2/news/", params={"ticker": ticker, "limit": limit})
        response.raise_for_status()
        return response.json()

    async def get_corporate_actions(self, ticker: str) -> dict:
        response = await self.client.get(f"/v2/company/corporate-actions/{ticker}/")
        response.raise_for_status()
        return response.json()

sectors_client = SectorsClient()
