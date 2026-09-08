import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.core.sectors_client import SectorsClient


@pytest.fixture
def client():
    c = SectorsClient()
    c._company_cache = {"tickers": set(), "ts": 0.0}
    c._subsector_cache = {"slugs": set(), "ts": 0.0}
    return c


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


class TestValidateTicker:
    """Tests for ticker format validation (free, no API call)."""

    def test_valid_idx_tickers(self, client):
        assert client.validate_ticker("BBCA") is True
        assert client.validate_ticker("BBRI") is True
        assert client.validate_ticker("TLKM") is True
        assert client.validate_ticker("ABCD") is True

    def test_rejects_lowercase(self, client):
        assert client.validate_ticker("bbca") is False
        assert client.validate_ticker("BbCa") is False

    def test_rejects_too_short(self, client):
        assert client.validate_ticker("BBC") is False
        assert client.validate_ticker("BB") is False
        assert client.validate_ticker("B") is False

    def test_rejects_too_long(self, client):
        assert client.validate_ticker("BBCAA") is False
        assert client.validate_ticker("BBCAX") is False

    def test_rejects_numbers(self, client):
        assert client.validate_ticker("1234") is False
        assert client.validate_ticker("BB12") is False

    def test_rejects_special_characters(self, client):
        assert client.validate_ticker("BB.CA") is False
        assert client.validate_ticker("BB-CA") is False
        assert client.validate_ticker("BB CA") is False

    def test_rejects_unknown(self, client):
        assert client.validate_ticker("UNKNOWN") is False

    def test_rejects_empty_and_none(self, client):
        assert client.validate_ticker("") is False
        assert client.validate_ticker(None) is False  # type: ignore

    def test_rejects_suffix(self, client):
        assert client.validate_ticker("BBCA.JK") is False
        assert client.validate_ticker("BBCA SI") is False


class TestCreditRecording:
    """Tests that credits are only recorded on successful API responses."""

    @pytest.mark.asyncio
    async def test_no_credit_on_404(self, client):
        import httpx
        with patch("app.core.sectors_client.record_sectors_call") as mock_record, \
             patch.object(client.client, "get", new_callable=AsyncMock) as mock_http:
            mock_response = Mock()
            mock_response.status_code = 404

            def raise_for_status():
                raise httpx.HTTPStatusError(
                    "404 Not Found", request=Mock(), response=mock_response
                )
            mock_response.raise_for_status = raise_for_status
            mock_http.return_value = mock_response

            with pytest.raises(httpx.HTTPStatusError):
                await client._get("/v2/daily/ZZZZ/")

            mock_record.assert_not_called()

    @pytest.mark.asyncio
    async def test_credit_recorded_on_success(self, client):
        with patch("app.core.sectors_client.record_sectors_call") as mock_record, \
             patch.object(client.client, "get", new_callable=AsyncMock) as mock_http:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"data": []}
            mock_http.return_value = mock_response

            result = await client._get("/v2/daily/BBCA/")

            mock_record.assert_called_once_with(endpoint="/v2/daily/BBCA/")
            assert result == {"data": []}


class TestCompanyCache:
    """Tests for company list caching and ticker existence validation."""

    @pytest.mark.asyncio
    async def test_validate_ticker_exists_with_cache(self, client):
        client._company_cache = {"tickers": {"BBCA", "BBRI", "TLKM"}, "ts": 9999999999.0}
        assert await client.validate_ticker_exists("BBCA") is True
        assert await client.validate_ticker_exists("ZZZZ") is False

    @pytest.mark.asyncio
    async def test_validate_ticker_exists_fetches_when_empty(self, client):
        with patch.object(client.client, "get", new_callable=AsyncMock) as mock_http:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"results": [{"symbol": "BBCA"}, {"symbol": "BBRI"}]}
            mock_http.return_value = mock_response

            with patch("app.core.sectors_client.record_sectors_call"):
                result = await client.validate_ticker_exists("BBCA")

            assert result is True
            assert "BBCA" in client._company_cache["tickers"]

    @pytest.mark.asyncio
    async def test_validate_ticker_exists_returns_true_on_fetch_error(self, client):
        import httpx
        with patch.object(client.client, "get", new_callable=AsyncMock) as mock_http:
            mock_response = Mock()

            def raise_for_status():
                raise httpx.HTTPStatusError(
                    "500 Error", request=Mock(), response=mock_response
                )
            mock_response.raise_for_status = raise_for_status
            mock_http.return_value = mock_response

            result = await client.validate_ticker_exists("BBCA")

            assert result is True
