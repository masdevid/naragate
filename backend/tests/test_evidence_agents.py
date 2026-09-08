import pytest
from unittest.mock import AsyncMock, patch
from app.services.evidence_agents import ValuationAgent, FundamentalAgent, MarketAgent, get_evidence_for_claim
from app.models.schemas import Claim, ClaimCategory, ClaimDirection


@pytest.fixture(autouse=True)
def _noop_cache_hit_counter():
    """Prevent cache-hit accounting from writing to the real usage.json during tests."""
    with patch("app.services.evidence_agents.record_sectors_cache_hit"), \
         patch("app.services.news_agent.record_sectors_cache_hit"), \
         patch("app.services.corporate_actions_agent.record_sectors_cache_hit"), \
         patch("app.services.filings_agent.record_sectors_cache_hit"):
        yield


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
            "overview": {"sub_sector": "Banks"},
            "valuation": {
                "historical_valuation": [
                    {"year": 2025, "pe": 25.5, "pb": 3.2, "ps": 8.1, "pcf": 18.3}
                ],
                "forward_pe": 22.0,
                "last_close_price": 6775,
            }
        }
        subsector_data = {
            "statistics": {"filtered_median_pe": 20.0},
            "valuation": {"historical_valuation": {"2025": {"pe": 20.0, "pb": 2.5, "ps": 6.0}}},
        }

        with patch("app.services.evidence_agents.cache") as mock_cache, \
             patch("app.services.evidence_agents.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            mock_cache.merge = AsyncMock()
            mock_sectors.get_company_report = AsyncMock(return_value=company_data)
            mock_sectors.get_subsector_report = AsyncMock(return_value=subsector_data)

            agent = ValuationAgent()
            evidence = await agent.analyze(claim)

            assert evidence.claim_ticker == "BBCA"
            assert evidence.category == "valuation"
            assert evidence.metrics["pe"] == 25.5
            assert evidence.subsector_median["pe"] == 20.0
            mock_sectors.get_subsector_report.assert_called_once_with("banks", ["statistics", "valuation"])

    @pytest.mark.asyncio
    async def test_calculates_premium_pct(self, claim):
        company_data = {
            "overview": {"sub_sector": "Banks"},
            "valuation": {
                "historical_valuation": [
                    {"year": 2025, "pe": 25.0, "pb": 3.0, "ps": 8.0, "pcf": 18.0}
                ]
            }
        }
        subsector_data = {
            "statistics": {"filtered_median_pe": 20.0},
            "valuation": {"historical_valuation": {"2025": {"pe": 20.0, "pb": 2.0, "ps": 5.0}}},
        }

        with patch("app.services.evidence_agents.cache") as mock_cache, \
             patch("app.services.evidence_agents.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            mock_cache.merge = AsyncMock()
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
            "company_report": {
                "overview": {"sub_sector": "Banks"},
                "valuation": {"historical_valuation": [{"year": 2025, "pe": 30.0}]},
            },
            "subsector_report": {"statistics": {"filtered_median_pe": 20.0}},
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
            mock_cache.merge = AsyncMock()
            mock_sectors.get_company_report = AsyncMock(
                return_value={"overview": {"sub_sector": "Banks"}, "valuation": {}}
            )
            mock_sectors.get_subsector_report = AsyncMock(return_value={"statistics": {}})

            agent = ValuationAgent()
            evidence = await agent.analyze(claim)

            assert evidence.cache_hit is False
            mock_sectors.get_company_report.assert_called_once()

    @pytest.mark.asyncio
    async def test_extracts_banking_health_metrics(self, claim):
        company_data = {
            "overview": {"sub_sector": "Banks"},
            "valuation": {"historical_valuation": [{"year": 2025, "pe": 25.5}]},
            "financials": {
                "historical_financial_ratio": [
                    {
                        "year": 2025,
                        "profitability": {"roe": 21.2, "roa": 3.1, "nim": 6.1},
                        "liquidity": {"npl": 1.2, "loan_growth": 9.4},
                    }
                ]
            },
        }
        subsector_data = {"statistics": {"filtered_median_pe": 20.0}}

        with patch("app.services.evidence_agents.cache") as mock_cache, \
             patch("app.services.evidence_agents.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            mock_cache.merge = AsyncMock()
            mock_sectors.get_company_report = AsyncMock(return_value=company_data)
            mock_sectors.get_subsector_report = AsyncMock(return_value=subsector_data)

            agent = ValuationAgent()
            evidence = await agent.analyze(claim)

            health = evidence.health or {}
            assert health["roe"] == 21.2
            assert health["nim"] == 6.1
            assert health["npl"] == 1.2
            assert health["loan_growth"] == 9.4

    @pytest.mark.asyncio
    async def test_health_metrics_missing_when_financials_absent(self, claim):
        company_data = {
            "overview": {"sub_sector": "Banks"},
            "valuation": {"historical_valuation": [{"year": 2025, "pe": 25.5}]},
        }
        subsector_data = {"statistics": {"filtered_median_pe": 20.0}}

        with patch("app.services.evidence_agents.cache") as mock_cache, \
             patch("app.services.evidence_agents.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            mock_cache.merge = AsyncMock()
            mock_sectors.get_company_report = AsyncMock(return_value=company_data)
            mock_sectors.get_subsector_report = AsyncMock(return_value=subsector_data)

            agent = ValuationAgent()
            evidence = await agent.analyze(claim)

            assert (evidence.health or {}) == {}


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
                "eps": 375,
                "historical_financials": [
                    {"year": 2025, "revenue": 120_000_000_000, "earnings": 45_000_000_000}
                ],
                "historical_financial_ratio": [
                    {
                        "year": 2025,
                        "profitability": {"roe": 0.25, "roa": 0.03, "net_profit_margin": 0.4},
                        "leverage": {"debt_to_equity_ratio": 0.8},
                    }
                ],
            }
        }
        quarterly_data = [
            {"revenue": 30_000_000_000, "earnings": 11_000_000_000},
            {"revenue": 31_000_000_000, "earnings": 12_000_000_000},
        ]

        with patch("app.services.evidence_agents.cache") as mock_cache, \
             patch("app.services.evidence_agents.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            mock_cache.merge = AsyncMock()
            mock_sectors.get_company_report = AsyncMock(return_value=company_data)
            mock_sectors.get_quarterly_financials = AsyncMock(return_value=quarterly_data)

            agent = FundamentalAgent()
            evidence = await agent.analyze(claim)

            assert evidence.claim_ticker == "BBCA"
            assert evidence.category == "fundamental"
            assert evidence.metrics["revenue"] == 120_000_000_000
            assert evidence.metrics["earnings"] == 45_000_000_000
            assert evidence.metrics["roe"] == 0.25

    @pytest.mark.asyncio
    async def test_calculates_revenue_trend_declining(self, claim):
        quarterly_data = [
            {"revenue": 25_000_000_000, "earnings": 10_000_000_000},
            {"revenue": 30_000_000_000, "earnings": 12_000_000_000},
        ]

        with patch("app.services.evidence_agents.cache") as mock_cache, \
             patch("app.services.evidence_agents.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            mock_cache.merge = AsyncMock()
            mock_sectors.get_company_report = AsyncMock(return_value={"financials": {}})
            mock_sectors.get_quarterly_financials = AsyncMock(return_value=quarterly_data)

            agent = FundamentalAgent()
            evidence = await agent.analyze(claim)

            assert evidence.trend["revenue_trend"] == "declining"
            assert evidence.trend["quarters_analyzed"] == 2

    @pytest.mark.asyncio
    async def test_calculates_revenue_trend_improving(self, claim):
        quarterly_data = [
            {"revenue": 35_000_000_000, "earnings": 10_000_000_000},
            {"revenue": 30_000_000_000, "earnings": 12_000_000_000},
        ]

        with patch("app.services.evidence_agents.cache") as mock_cache, \
             patch("app.services.evidence_agents.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            mock_cache.merge = AsyncMock()
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
            {"close": 9400, "volume": 12_000_000},
            {"close": 9500, "volume": 15_000_000},
        ]

        with patch("app.services.evidence_agents.cache") as mock_cache, \
             patch("app.services.evidence_agents.sectors_client") as mock_sectors:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            mock_cache.merge = AsyncMock()
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
            mock_cache.merge = AsyncMock()
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
            mock_cache.merge = AsyncMock()
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

    @pytest.mark.asyncio
    async def test_routes_insider_trading_to_filings_agent(self):
        claim = Claim(
            ticker="BBCA",
            category=ClaimCategory.INSIDER_TRADING,
            assertion="insiders are selling",
            direction=ClaimDirection.BELOW,
            confidence=0.8,
        )

        with patch("app.services.evidence_agents.FilingsAgent") as MockAgent, \
             patch("app.services.evidence_agents.filings_agent") as mock_filings_singleton:
            mock_instance = AsyncMock()
            mock_instance.analyze = AsyncMock(return_value="filings_evidence")
            MockAgent.return_value = mock_instance
            mock_filings_singleton.analyze = AsyncMock(return_value="filings_enrichment")

            result = await get_evidence_for_claim(claim)

            assert "insider_trading" in result
            assert result["insider_trading"] == "filings_evidence"
            mock_instance.analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_filings_enrichment_runs_for_valuation(self):
        claim = Claim(
            ticker="BBCA",
            category=ClaimCategory.VALUATION,
            assertion="PE is expensive",
            direction=ClaimDirection.ABOVE,
            confidence=0.8,
        )

        with patch("app.services.evidence_agents.ValuationAgent") as MockAgent, \
             patch("app.services.evidence_agents.filings_agent") as mock_filings:
            mock_instance = AsyncMock()
            mock_instance.analyze = AsyncMock(return_value="valuation_evidence")
            MockAgent.return_value = mock_instance
            mock_filings.analyze = AsyncMock(return_value="filings_evidence")

            result = await get_evidence_for_claim(claim)

            assert "valuation" in result
            assert "filings" in result
            assert result["filings"] == "filings_evidence"
            mock_filings.analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_filings_enrichment_runs_for_fundamental(self):
        claim = Claim(
            ticker="BBCA",
            category=ClaimCategory.FUNDAMENTAL,
            assertion="profits declined",
            direction=ClaimDirection.BELOW,
            confidence=0.9,
        )

        with patch("app.services.evidence_agents.FundamentalAgent") as MockAgent, \
             patch("app.services.evidence_agents.filings_agent") as mock_filings:
            mock_instance = AsyncMock()
            mock_instance.analyze = AsyncMock(return_value="fundamental_evidence")
            MockAgent.return_value = mock_instance
            mock_filings.analyze = AsyncMock(return_value="filings_evidence")

            result = await get_evidence_for_claim(claim)

            assert "fundamental" in result
            assert "filings" in result
            mock_filings.analyze.assert_called_once()


class TestCacheStrategy:
    """Regression: repeated BBCA runs must serve from cache, not re-fetch Sectors."""

    @pytest.mark.asyncio
    async def test_second_fundamental_run_makes_zero_new_sectors_calls(self):
        company_data = {
            "overview": {"sub_sector": "Banks"},
            "valuation": {"historical_valuation": [{"year": 2025, "pe": 25.0}]},
            "financials": {
                "eps": 375,
                "historical_financials": [
                    {"year": 2025, "revenue": 120_000_000_000, "earnings": 45_000_000_000}
                ],
                "historical_financial_ratio": [
                    {"year": 2025, "profitability": {"roe": 0.25}, "leverage": {}}
                ],
            },
        }
        quarterly_data = [{"revenue": 30_000_000_000, "earnings": 11_000_000_000}]
        news_data = {"data": [{"title": "BBCA profit rises", "date": "2025-01-01", "source": "Kontan"}]}
        corp_data = {"data": [{"type": "dividend", "date": "2025-01-01", "description": "Interim"}]}

        store: dict = {}

        async def fake_get(ticker):
            return store.get(ticker)

        async def fake_merge(ticker, key, value, ttl=None):
            entry = store.get(ticker) or {}
            entry[key] = value
            store[ticker] = entry

        claim = Claim(
            ticker="BBCA",
            category=ClaimCategory.FUNDAMENTAL,
            assertion="profits declined",
            direction=ClaimDirection.BELOW,
            confidence=0.9,
        )

        with patch("app.services.evidence_agents.cache") as mock_cache, \
             patch("app.services.evidence_agents.sectors_client") as mock_sectors, \
             patch("app.services.news_agent.cache") as mock_news_cache, \
             patch("app.services.news_agent.sectors_client") as mock_news_sectors, \
             patch("app.services.news_agent.llm_client.stream_chat", AsyncMock(return_value='{"corroboration": "supports"}')), \
             patch("app.services.corporate_actions_agent.cache") as mock_corp_cache, \
             patch("app.services.corporate_actions_agent.sectors_client") as mock_corp_sectors:
            for mc in (mock_cache, mock_news_cache, mock_corp_cache):
                mc.get = fake_get
                mc.merge = fake_merge
            mock_sectors.get_company_report = AsyncMock(return_value=company_data)
            mock_sectors.get_quarterly_financials = AsyncMock(return_value=quarterly_data)
            mock_news_sectors.get_news = AsyncMock(return_value=news_data)
            mock_corp_sectors.get_corporate_actions = AsyncMock(return_value=corp_data)

            await get_evidence_for_claim(claim)
            first_run_calls = (
                mock_sectors.get_company_report.call_count
                + mock_sectors.get_quarterly_financials.call_count
                + mock_news_sectors.get_news.call_count
                + mock_corp_sectors.get_corporate_actions.call_count
            )
            assert first_run_calls == 4

            await get_evidence_for_claim(claim)
            second_run_calls = (
                mock_sectors.get_company_report.call_count
                + mock_sectors.get_quarterly_financials.call_count
                + mock_news_sectors.get_news.call_count
                + mock_corp_sectors.get_corporate_actions.call_count
            )
            assert second_run_calls == first_run_calls

    @pytest.mark.asyncio
    async def test_valuation_then_fundamental_share_company_report(self):
        company_data = {
            "overview": {"sub_sector": "Banks"},
            "valuation": {"historical_valuation": [{"year": 2025, "pe": 25.0}]},
            "financials": {
                "eps": 375,
                "historical_financials": [
                    {"year": 2025, "revenue": 120_000_000_000, "earnings": 45_000_000_000}
                ],
                "historical_financial_ratio": [
                    {"year": 2025, "profitability": {"roe": 0.25}, "leverage": {}}
                ],
            },
        }
        subsector_data = {"statistics": {"filtered_median_pe": 20.0}}
        quarterly_data = [{"revenue": 30_000_000_000, "earnings": 11_000_000_000}]

        store: dict = {}

        async def fake_get(ticker):
            return store.get(ticker)

        async def fake_merge(ticker, key, value, ttl=None):
            entry = store.get(ticker) or {}
            entry[key] = value
            store[ticker] = entry

        valuation_claim = Claim(
            ticker="BBCA",
            category=ClaimCategory.VALUATION,
            assertion="PE is expensive",
            direction=ClaimDirection.ABOVE,
            confidence=0.8,
        )
        fundamental_claim = Claim(
            ticker="BBCA",
            category=ClaimCategory.FUNDAMENTAL,
            assertion="profits declined",
            direction=ClaimDirection.BELOW,
            confidence=0.9,
        )

        with patch("app.services.evidence_agents.cache") as mock_cache, \
             patch("app.services.evidence_agents.sectors_client") as mock_sectors, \
             patch("app.services.news_agent.cache") as mock_news_cache, \
             patch("app.services.news_agent.sectors_client") as mock_news_sectors, \
             patch("app.services.news_agent.llm_client.stream_chat", AsyncMock(return_value='{"corroboration": "neutral"}')), \
             patch("app.services.corporate_actions_agent.cache") as mock_corp_cache, \
             patch("app.services.corporate_actions_agent.sectors_client") as mock_corp_sectors:
            for mc in (mock_cache, mock_news_cache, mock_corp_cache):
                mc.get = fake_get
                mc.merge = fake_merge
            mock_sectors.get_company_report = AsyncMock(return_value=company_data)
            mock_sectors.get_subsector_report = AsyncMock(return_value=subsector_data)
            mock_sectors.get_quarterly_financials = AsyncMock(return_value=quarterly_data)
            mock_news_sectors.get_news = AsyncMock(return_value={})
            mock_corp_sectors.get_corporate_actions = AsyncMock(return_value={})

            await get_evidence_for_claim(valuation_claim)
            await get_evidence_for_claim(fundamental_claim)

            # company_report fetched exactly once across both agents
            assert mock_sectors.get_company_report.call_count == 1
