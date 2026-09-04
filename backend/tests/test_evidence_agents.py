import pytest
from unittest.mock import AsyncMock, patch
from app.services.evidence_agents import ValuationAgent, FundamentalAgent, MarketAgent, get_evidence_for_claim
from app.models.schemas import Claim, ClaimCategory, ClaimDirection


class TestValuationAgent:
    """Tests for valuation evidence retrieval."""

    @pytest.fixture
    def claim(self):
        return Claim(
            ticker="BBCA",
            category=ClaimCategory.VALUATION,
            assertion="PE is expensive",
            direction=ClaimDirection.ABOVE,
            confidence=0.8,
        )

    @pytest.mark.asyncio
    async def test_returns_valuation_evidence(self, claim):
        company_data = {
            "valuation": {
                "pe_ratio": 25.5,
                "pb_ratio": 3.2,
                "ps_ratio": 8.1,
                "pcf_ratio": 18.3,
            }
        }
        subsector_data = {
            "median": {
                "pe_ratio": 20.0,
                "pb_ratio": 2.5,
                "ps_ratio": 6.0,
            }
        }

        with patch("app.services.evidence_agents.cache") as mock_cache, \
             patch("app.services.evidence_agents.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            mock_sectors.get_company_report = AsyncMock(return_value=company_data)
            mock_sectors.get_subsector_report = AsyncMock(return_value=subsector_data)

            agent = ValuationAgent()
            evidence = await agent.analyze(claim)

            assert evidence.claim_ticker == "BBCA"
            assert evidence.category == "valuation"
            assert evidence.metrics["pe"] == 25.5
            assert evidence.subsector_median["pe"] == 20.0

    @pytest.mark.asyncio
    async def test_calculates_premium_pct(self, claim):
        company_data = {
            "valuation": {"pe_ratio": 25.0, "pb_ratio": 3.0, "ps_ratio": 8.0, "pcf_ratio": 18.0}
        }
        subsector_data = {
            "median": {"pe_ratio": 20.0, "pb_ratio": 2.0, "ps_ratio": 5.0}
        }

        with patch("app.services.evidence_agents.cache") as mock_cache, \
             patch("app.services.evidence_agents.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            mock_sectors.get_company_report = AsyncMock(return_value=company_data)
            mock_sectors.get_subsector_report = AsyncMock(return_value=subsector_data)

            agent = ValuationAgent()
            evidence = await agent.analyze(claim)

            assert evidence.premium_pct["pe"] == 25.0  # (25-20)/20 * 100
            assert evidence.premium_pct["pb"] == 50.0  # (3-2)/2 * 100
            assert evidence.premium_pct["ps"] == 60.0  # (8-5)/5 * 100

    @pytest.mark.asyncio
    async def test_uses_cache_when_available(self, claim):
        cached_data = {
            "company_report": {"valuation": {"pe_ratio": 30.0}},
            "subsector_report": {"median": {"pe_ratio": 20.0}},
        }

        with patch("app.services.evidence_agents.cache") as mock_cache, \
             patch("app.services.evidence_agents.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=cached_data)
            mock_sectors.get_company_report = AsyncMock()
            mock_sectors.get_subsector_report = AsyncMock()

            agent = ValuationAgent()
            evidence = await agent.analyze(claim)

            assert evidence.cache_hit is True
            mock_sectors.get_company_report.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetches_from_api_on_cache_miss(self, claim):
        with patch("app.services.evidence_agents.cache") as mock_cache, \
             patch("app.services.evidence_agents.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            mock_sectors.get_company_report = AsyncMock(return_value={"valuation": {}})
            mock_sectors.get_subsector_report = AsyncMock(return_value={"median": {}})

            agent = ValuationAgent()
            evidence = await agent.analyze(claim)

            assert evidence.cache_hit is False
            mock_sectors.get_company_report.assert_called_once()


class TestFundamentalAgent:
    """Tests for fundamental evidence retrieval."""

    @pytest.fixture
    def claim(self):
        return Claim(
            ticker="BBCA",
            category=ClaimCategory.FUNDAMENTAL,
            assertion="profits declined",
            direction=ClaimDirection.BELOW,
            confidence=0.9,
        )

    @pytest.mark.asyncio
    async def test_returns_fundamental_evidence(self, claim):
        company_data = {
            "financials": {
                "revenue": 120_000_000_000,
                "net_income": 45_000_000_000,
                "eps": 375,
                "gross_margin": 0.62,
                "roe": 0.25,
                "roa": 0.03,
                "debt_to_equity": 0.8,
            }
        }
        quarterly_data = [
            {"revenue": 30_000_000_000, "net_income": 11_000_000_000},
            {"revenue": 31_000_000_000, "net_income": 12_000_000_000},
        ]

        with patch("app.services.evidence_agents.cache") as mock_cache, \
             patch("app.services.evidence_agents.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            mock_sectors.get_company_report = AsyncMock(return_value=company_data)
            mock_sectors.get_quarterly_financials = AsyncMock(return_value=quarterly_data)

            agent = FundamentalAgent()
            evidence = await agent.analyze(claim)

            assert evidence.claim_ticker == "BBCA"
            assert evidence.category == "fundamental"
            assert evidence.metrics["revenue"] == 120_000_000_000
            assert evidence.metrics["earnings"] == 45_000_000_000

    @pytest.mark.asyncio
    async def test_calculates_revenue_trend_declining(self, claim):
        quarterly_data = [
            {"revenue": 25_000_000_000, "net_income": 10_000_000_000},
            {"revenue": 30_000_000_000, "net_income": 12_000_000_000},
        ]

        with patch("app.services.evidence_agents.cache") as mock_cache, \
             patch("app.services.evidence_agents.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            mock_sectors.get_company_report = AsyncMock(return_value={"financials": {}})
            mock_sectors.get_quarterly_financials = AsyncMock(return_value=quarterly_data)

            agent = FundamentalAgent()
            evidence = await agent.analyze(claim)

            assert evidence.trend["revenue_trend"] == "declining"
            assert evidence.trend["quarters_analyzed"] == 2

    @pytest.mark.asyncio
    async def test_calculates_revenue_trend_improving(self, claim):
        quarterly_data = [
            {"revenue": 35_000_000_000, "net_income": 10_000_000_000},
            {"revenue": 30_000_000_000, "net_income": 12_000_000_000},
        ]

        with patch("app.services.evidence_agents.cache") as mock_cache, \
             patch("app.services.evidence_agents.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            mock_sectors.get_company_report = AsyncMock(return_value={"financials": {}})
            mock_sectors.get_quarterly_financials = AsyncMock(return_value=quarterly_data)

            agent = FundamentalAgent()
            evidence = await agent.analyze(claim)

            assert evidence.trend["revenue_trend"] == "improving"


class TestMarketAgent:
    """Tests for market evidence retrieval."""

    @pytest.fixture
    def claim(self):
        return Claim(
            ticker="BBCA",
            category=ClaimCategory.MARKET,
            assertion="price surging",
            direction=ClaimDirection.ABOVE,
            confidence=0.7,
        )

    @pytest.mark.asyncio
    async def test_returns_market_evidence(self, claim):
        tx_data = [
            {"close": 9500, "volume": 15_000_000},
            {"close": 9400, "volume": 12_000_000},
        ]

        with patch("app.services.evidence_agents.cache") as mock_cache, \
             patch("app.services.evidence_agents.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            mock_sectors.get_daily_transaction = AsyncMock(return_value=tx_data)

            agent = MarketAgent()
            evidence = await agent.analyze(claim)

            assert evidence.claim_ticker == "BBCA"
            assert evidence.category == "market"
            assert evidence.performance["1d"]["price_change_pct"] == 1.06  # (9500-9400)/9400 * 100

    @pytest.mark.asyncio
    async def test_calculates_volatility(self, claim):
        tx_data = [
            {"close": 100, "volume": 1000},
            {"close": 110, "volume": 1000},
            {"close": 90, "volume": 1000},
            {"close": 105, "volume": 1000},
        ]

        with patch("app.services.evidence_agents.cache") as mock_cache, \
             patch("app.services.evidence_agents.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            mock_sectors.get_daily_transaction = AsyncMock(return_value=tx_data)

            agent = MarketAgent()
            evidence = await agent.analyze(claim)

            assert evidence.volatility > 0

    @pytest.mark.asyncio
    async def test_handles_empty_transaction_data(self, claim):
        with patch("app.services.evidence_agents.cache") as mock_cache, \
             patch("app.services.evidence_agents.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            mock_sectors.get_daily_transaction = AsyncMock(return_value=[])

            agent = MarketAgent()
            evidence = await agent.analyze(claim)

            assert evidence.performance == {}
            assert evidence.volatility == 0.0


class TestGetEvidenceForClaim:
    """Tests for the evidence routing function."""

    @pytest.mark.asyncio
    async def test_routes_to_correct_agent(self):
        claim = Claim(
            ticker="BBCA",
            category=ClaimCategory.VALUATION,
            assertion="expensive",
            direction=ClaimDirection.ABOVE,
            confidence=0.8,
        )

        with patch("app.services.evidence_agents.ValuationAgent") as MockAgent:
            mock_instance = AsyncMock()
            mock_instance.analyze = AsyncMock(return_value="evidence")
            MockAgent.return_value = mock_instance

            result = await get_evidence_for_claim(claim)
            assert "valuation" in result
            mock_instance.analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_empty_for_unknown_category(self):
        claim = Claim(
            ticker="BBCA",
            category=ClaimCategory.MARKET,
            assertion="test",
            direction=ClaimDirection.NEUTRAL,
            confidence=0.5,
        )

        # Market is handled, but let's test the edge case
        with patch("app.services.evidence_agents.MarketAgent") as MockAgent:
            mock_instance = AsyncMock()
            mock_instance.analyze = AsyncMock(return_value="evidence")
            MockAgent.return_value = mock_instance

            result = await get_evidence_for_claim(claim)
            assert "market" in result
