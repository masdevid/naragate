import pytest
from unittest.mock import AsyncMock, patch
from app.services.filings_agent import FilingsAgent
from app.models.schemas import Claim, ClaimCategory, ClaimDirection


@pytest.fixture(autouse=True)
def _noop_cache_hit_counter():
    with patch("app.services.filings_agent.record_sectors_cache_hit"):
        yield


class TestFilingsAgent:
    """Tests for insider trading filings evidence retrieval."""

    @pytest.fixture
    def claim(self):
        return Claim(
            ticker="BBCA",
            category=ClaimCategory.INSIDER_TRADING,
            assertion="insiders are selling",
            direction=ClaimDirection.BELOW,
            confidence=0.8,
        )

    @pytest.mark.asyncio
    async def test_returns_filings_evidence(self, claim):
        filings_data = {
            "data": [
                {
                    "date": "2025-08-15",
                    "insider_name": "Budi Santoso",
                    "insider_title": "Direktur",
                    "transaction_type": "sell",
                    "shares": 50000,
                    "price": 9500,
                    "total_value": 475_000_000,
                },
                {
                    "date": "2025-08-10",
                    "insider_name": "Siti Rahayu",
                    "insider_title": "Komisaris",
                    "transaction_type": "buy",
                    "shares": 10000,
                    "price": 9400,
                    "total_value": 94_000_000,
                },
            ]
        }

        with patch("app.services.filings_agent.cache") as mock_cache, \
             patch("app.services.filings_agent.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.merge = AsyncMock()
            mock_sectors.get_filings = AsyncMock(return_value=filings_data)

            agent = FilingsAgent()
            evidence = await agent.analyze(claim)

            assert evidence.claim_ticker == "BBCA"
            assert evidence.category == "insider_trading"
            assert len(evidence.filings) == 2
            assert evidence.filings[0]["insider_name"] == "Budi Santoso"
            assert evidence.filings[1]["transaction_type"] == "buy"

    @pytest.mark.asyncio
    async def test_computes_net_selling_bias(self, claim):
        filings_data = {
            "data": [
                {"date": "2025-08-15", "insider_name": "A", "insider_title": "Dir", "transaction_type": "sell", "shares": 100000, "price": 9500, "total_value": 950_000_000},
                {"date": "2025-08-14", "insider_name": "B", "insider_title": "Kom", "transaction_type": "sell", "shares": 50000, "price": 9400, "total_value": 470_000_000},
                {"date": "2025-08-13", "insider_name": "C", "insider_title": "Dir", "transaction_type": "buy", "shares": 5000, "price": 9300, "total_value": 46_500_000},
            ]
        }

        with patch("app.services.filings_agent.cache") as mock_cache, \
             patch("app.services.filings_agent.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.merge = AsyncMock()
            mock_sectors.get_filings = AsyncMock(return_value=filings_data)

            agent = FilingsAgent()
            evidence = await agent.analyze(claim)

            assert evidence.recent_bias == "net_selling"

    @pytest.mark.asyncio
    async def test_computes_net_buying_bias(self, claim):
        filings_data = {
            "data": [
                {"date": "2025-08-15", "insider_name": "A", "insider_title": "Dir", "transaction_type": "buy", "shares": 100000, "price": 9500, "total_value": 950_000_000},
                {"date": "2025-08-14", "insider_name": "B", "insider_title": "Kom", "transaction_type": "buy", "shares": 50000, "price": 9400, "total_value": 470_000_000},
                {"date": "2025-08-13", "insider_name": "C", "insider_title": "Dir", "transaction_type": "sell", "shares": 5000, "price": 9300, "total_value": 46_500_000},
            ]
        }

        with patch("app.services.filings_agent.cache") as mock_cache, \
             patch("app.services.filings_agent.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.merge = AsyncMock()
            mock_sectors.get_filings = AsyncMock(return_value=filings_data)

            agent = FilingsAgent()
            evidence = await agent.analyze(claim)

            assert evidence.recent_bias == "net_buying"

    @pytest.mark.asyncio
    async def test_balanced_bias(self, claim):
        filings_data = {
            "data": [
                {"date": "2025-08-15", "insider_name": "A", "insider_title": "Dir", "transaction_type": "buy", "shares": 50000, "price": 9500, "total_value": 475_000_000},
                {"date": "2025-08-14", "insider_name": "B", "insider_title": "Kom", "transaction_type": "sell", "shares": 50000, "price": 9400, "total_value": 470_000_000},
            ]
        }

        with patch("app.services.filings_agent.cache") as mock_cache, \
             patch("app.services.filings_agent.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.merge = AsyncMock()
            mock_sectors.get_filings = AsyncMock(return_value=filings_data)

            agent = FilingsAgent()
            evidence = await agent.analyze(claim)

            assert evidence.recent_bias == "balanced"

    @pytest.mark.asyncio
    async def test_uses_cache_when_available(self, claim):
        cached_data = {
            "filings": {
                "data": [
                    {"date": "2025-08-15", "insider_name": "X", "insider_title": "Dir", "transaction_type": "sell", "shares": 1000, "price": 9000, "total_value": 9_000_000}
                ]
            }
        }

        with patch("app.services.filings_agent.cache") as mock_cache, \
             patch("app.services.filings_agent.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=cached_data)
            mock_sectors.get_filings = AsyncMock()

            agent = FilingsAgent()
            evidence = await agent.analyze(claim)

            assert evidence.cache_hit is True
            mock_sectors.get_filings.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_empty_filings(self, claim):
        with patch("app.services.filings_agent.cache") as mock_cache, \
             patch("app.services.filings_agent.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.merge = AsyncMock()
            mock_sectors.get_filings = AsyncMock(return_value={"data": []})

            agent = FilingsAgent()
            evidence = await agent.analyze(claim)

            assert evidence.filings == []
            assert evidence.recent_bias == "balanced"
            assert "Tidak ada" in evidence.summary

    @pytest.mark.asyncio
    async def test_handles_api_failure(self, claim):
        with patch("app.services.filings_agent.cache") as mock_cache, \
             patch("app.services.filings_agent.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.merge = AsyncMock()
            mock_sectors.get_filings = AsyncMock(side_effect=Exception("API down"))

            agent = FilingsAgent()
            evidence = await agent.analyze(claim)

            assert evidence.filings == []
            assert evidence.cache_hit is False

    @pytest.mark.asyncio
    async def test_handles_list_response_format(self, claim):
        filings_data = [
            {"date": "2025-08-15", "insider_name": "A", "insider_title": "Dir", "transaction_type": "buy", "shares": 10000, "price": 9000, "total_value": 90_000_000}
        ]

        with patch("app.services.filings_agent.cache") as mock_cache, \
             patch("app.services.filings_agent.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.merge = AsyncMock()
            mock_sectors.get_filings = AsyncMock(return_value=filings_data)

            agent = FilingsAgent()
            evidence = await agent.analyze(claim)

            assert len(evidence.filings) == 1

    @pytest.mark.asyncio
    async def test_parses_real_sectors_response_shape(self, claim):
        """The live API returns {"results": [...]} with holder_name/
        amount_transaction/timestamp/transaction_value fields."""
        filings_data = {
            "results": [
                {
                    "title": "Budi Santoso Buy Transaction",
                    "timestamp": "2025-08-15T04:52:00",
                    "holder_type": "insider",
                    "holder_name": "Budi Santoso",
                    "transaction_type": "buy",
                    "amount_transaction": 4977,
                    "price": 1000.0,
                    "transaction_value": 4977000.0,
                    "holding_before": 2483523,
                    "holding_after": 2488500,
                },
                {
                    "title": "Siti Rahayu Sell Transaction",
                    "timestamp": "2025-08-10T09:30:00",
                    "holder_type": "commissioner",
                    "holder_name": "Siti Rahayu",
                    "transaction_type": "sell",
                    "amount_transaction": 25000,
                    "price": 9400.0,
                    "transaction_value": 235_000_000,
                },
            ]
        }

        with patch("app.services.filings_agent.cache") as mock_cache, \
             patch("app.services.filings_agent.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.merge = AsyncMock()
            mock_sectors.get_filings = AsyncMock(return_value=filings_data)

            agent = FilingsAgent()
            evidence = await agent.analyze(claim)

            assert len(evidence.filings) == 2
            assert evidence.filings[0]["insider_name"] == "Budi Santoso"
            assert evidence.filings[0]["insider_title"] == "insider"
            assert evidence.filings[0]["date"] == "2025-08-15T04:52:00"
            assert evidence.filings[0]["transaction_type"] == "buy"
            assert evidence.filings[0]["shares"] == 4977
            assert evidence.filings[0]["price"] == 1000.0
            assert evidence.filings[0]["total_value"] == 4977000.0
            assert evidence.filings[1]["transaction_type"] == "sell"
            assert evidence.recent_bias == "net_selling"
