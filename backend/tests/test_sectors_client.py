import pytest
from unittest.mock import AsyncMock, patch
from app.core.sectors_client import SectorsClient


@pytest.fixture
def client():
    return SectorsClient()


class TestGetFilings:
    """Tests for SectorsClient.get_filings method."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, client):
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"data": []}
            await client.get_filings("BBCA")
            mock_get.assert_called_once_with(
                "/v2/filings/", params={"symbol": "BBCA", "type": "insider_trade"}
            )

    @pytest.mark.asyncio
    async def test_returns_filing_data(self, client):
        sample_response = {
            "data": [
                {
                    "date": "2025-08-15",
                    "insider_name": "Budi Santoso",
                    "insider_title": "Direktur",
                    "transaction_type": "sell",
                    "shares": 50000,
                    "price": 9500,
                    "total_value": 475_000_000,
                }
            ]
        }
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_response
            result = await client.get_filings("BBCA")
            assert result == sample_response
            assert len(result["data"]) == 1
            assert result["data"][0]["insider_name"] == "Budi Santoso"

    @pytest.mark.asyncio
    async def test_default_filing_type_is_insider_trade(self, client):
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"data": []}
            await client.get_filings("BBCA")
            call_params = mock_get.call_args[1]["params"]
            assert call_params["type"] == "insider_trade"

    @pytest.mark.asyncio
    async def test_custom_filing_type(self, client):
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"data": []}
            await client.get_filings("BBCA", filing_type="annual_report")
            call_params = mock_get.call_args[1]["params"]
            assert call_params["type"] == "annual_report"

    @pytest.mark.asyncio
    async def test_handles_empty_response(self, client):
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"data": []}
            result = await client.get_filings("ZZZZ")
            assert result == {"data": []}

    @pytest.mark.asyncio
    async def test_propagates_http_error(self, client):
        import httpx
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=AsyncMock(), response=AsyncMock(status_code=404)
            )
            with pytest.raises(httpx.HTTPStatusError):
                await client.get_filings("ZZZZ")
