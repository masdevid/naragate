import pytest
from unittest.mock import AsyncMock, patch

from app.models.schemas import Claim, ClaimCategory, ClaimDirection
from app.services.news_agent import NewsAgent
from app.services.corporate_actions_agent import CorporateActionsAgent


class TestNewsAgent:
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
    async def test_analyze_with_news(self, claim):
        news_data = {
            "data": [
                {"title": "BBCA posts record profit", "date": "2024-01-10", "source": "Kontan"},
                {"title": "BBCA expands digital banking", "date": "2024-01-05", "source": "Bisnis"},
            ]
        }
        with patch("app.services.news_agent.cache.get", AsyncMock(return_value=None)), \
             patch("app.services.news_agent.cache.merge", AsyncMock()), \
             patch("app.services.news_agent.sectors_client.get_news", AsyncMock(return_value=news_data)), \
             patch("app.services.news_agent.llm_client.stream_chat", AsyncMock(return_value='{"corroboration": "supports", "summary": "Berita mendukung klaim.", "summary_en": "News supports the claim."}')):
            result = await NewsAgent().analyze(claim)

        assert result.claim_ticker == "BBCA"
        assert result.category == "news"
        assert len(result.headlines) == 2
        assert result.corroboration == "supports"
        assert result.summary == "Berita mendukung klaim."
        assert result.summary_en == "News supports the claim."

    @pytest.mark.asyncio
    async def test_analyze_no_news(self, claim):
        with patch("app.services.news_agent.cache.get", AsyncMock(return_value=None)), \
             patch("app.services.news_agent.cache.merge", AsyncMock()), \
             patch("app.services.news_agent.sectors_client.get_news", AsyncMock(return_value={})):
            result = await NewsAgent().analyze(claim)

        assert result.corroboration == "no_news"
        assert result.headlines == []

    @pytest.mark.asyncio
    async def test_analyze_llm_failure_falls_back(self, claim):
        news_data = {"data": [{"title": "BBCA news", "date": "2024-01-10", "source": "Kontan"}]}
        with patch("app.services.news_agent.cache.get", AsyncMock(return_value=None)), \
             patch("app.services.news_agent.cache.merge", AsyncMock()), \
             patch("app.services.news_agent.sectors_client.get_news", AsyncMock(return_value=news_data)), \
             patch("app.services.news_agent.llm_client.stream_chat", AsyncMock(side_effect=Exception("LLM down"))):
            result = await NewsAgent().analyze(claim)

        assert result.corroboration == "neutral"
        assert len(result.headlines) == 1


class TestCorporateActionsAgent:
    @pytest.fixture
    def claim(self):
        return Claim(
            ticker="BBCA",
            category=ClaimCategory.MARKET,
            assertion="Price dropped sharply",
            direction=ClaimDirection.BELOW,
            confidence=0.8,
        )

    @pytest.mark.asyncio
    async def test_analyze_with_actions(self, claim):
        actions_data = {
            "data": [
                {"type": "dividend", "date": "2024-01-15", "description": "Interim dividend"},
                {"type": "stock_split", "date": "2024-02-01", "description": "1:2 split"},
            ]
        }
        with patch("app.services.corporate_actions_agent.cache.get", AsyncMock(return_value=None)), \
             patch("app.services.corporate_actions_agent.cache.merge", AsyncMock()), \
             patch("app.services.corporate_actions_agent.sectors_client.get_corporate_actions", AsyncMock(return_value=actions_data)):
            result = await CorporateActionsAgent().analyze(claim)

        assert result.claim_ticker == "BBCA"
        assert result.category == "corporate_actions"
        assert len(result.actions) == 2
        assert "dividend" in result.relevant_events
        assert "stock split" in result.relevant_events

    @pytest.mark.asyncio
    async def test_parses_real_sectors_response_shape(self, claim):
        """The live API returns {"corporate_actions": {category: [...]}}."""
        actions_data = {
            "symbol": "BBCA.JK",
            "corporate_actions": {
                "dividend": [
                    {"ex_date": "2024-01-15", "payment_date": "2024-01-30", "dividend_yield": 0.0174, "dividend_amount": 150}
                ],
                "stock_split": [{"date": "2024-02-01", "split_ratio": 2}],
                "bonus": None,
                "agm": [{"agm_date": "2024-03-01"}],
            },
        }
        with patch("app.services.corporate_actions_agent.cache.get", AsyncMock(return_value=None)), \
             patch("app.services.corporate_actions_agent.cache.merge", AsyncMock()), \
             patch("app.services.corporate_actions_agent.sectors_client.get_corporate_actions", AsyncMock(return_value=actions_data)):
            result = await CorporateActionsAgent().analyze(claim)

        assert len(result.actions) == 3
        assert result.actions[0]["type"] == "dividend"
        assert result.actions[0]["date"] == "2024-01-15"
        assert result.actions[1]["type"] == "stock split"
        assert result.actions[1]["date"] == "2024-02-01"
        assert result.actions[2]["type"] == "annual general meeting"
        assert result.relevant_events == ["dividend", "stock split", "annual general meeting"]
        assert "3" in result.summary

    @pytest.mark.asyncio
    async def test_analyze_no_actions(self, claim):
        with patch("app.services.corporate_actions_agent.cache.get", AsyncMock(return_value=None)), \
             patch("app.services.corporate_actions_agent.cache.merge", AsyncMock()), \
             patch("app.services.corporate_actions_agent.sectors_client.get_corporate_actions", AsyncMock(return_value={})):
            result = await CorporateActionsAgent().analyze(claim)

        assert result.relevant_events == []
        assert "Tidak ada aksi korporasi" in result.summary

    @pytest.mark.asyncio
    async def test_analyze_api_failure(self, claim):
        with patch("app.services.corporate_actions_agent.cache.get", AsyncMock(return_value=None)), \
             patch("app.services.corporate_actions_agent.cache.merge", AsyncMock()), \
             patch("app.services.corporate_actions_agent.sectors_client.get_corporate_actions", AsyncMock(side_effect=Exception("API down"))):
            result = await CorporateActionsAgent().analyze(claim)

        assert result.actions == []
        assert result.relevant_events == []