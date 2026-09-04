import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.skeptic import run_skeptic
from app.models.schemas import Claim, ClaimCategory, ClaimDirection, SkepticOutput


class TestRunSkeptic:
    """Tests for skeptic analysis."""

    @pytest.fixture
    def claim(self):
        return Claim(
            ticker="BBCA",
            category=ClaimCategory.FUNDAMENTAL,
            assertion="profits declined",
            direction=ClaimDirection.BELOW,
            confidence=0.9,
        )

    @pytest.fixture
    def evidence(self):
        return {
            "fundamental": {
                "metrics": {"revenue": 120_000_000_000, "earnings": 45_000_000_000},
                "trend": {"revenue_trend": "declining", "earnings_trend": "declining"},
            }
        }

    @pytest.mark.asyncio
    async def test_returns_skeptic_output(self, claim, evidence):
        llm_response = '{"counter_arguments": [{"point": "test", "evidence_ref": "test", "strength": 80}], "ambiguity_points": ["test"], "missing_evidence": ["test"], "skepticism_score": 75}'

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": llm_response}}]}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_client
        mock_context_manager.__aexit__.return_value = False

        with patch("app.services.skeptic.httpx.AsyncClient", return_value=mock_context_manager):
            result = await run_skeptic(claim, evidence)

            assert isinstance(result, SkepticOutput)
            assert result.claim_ticker == "BBCA"
            assert result.skepticism_score == 75.0

    @pytest.mark.asyncio
    async def test_handles_llm_failure_gracefully(self, claim, evidence):
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("LLM unavailable"))

        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_client
        mock_context_manager.__aexit__.return_value = False

        with patch("app.services.skeptic.httpx.AsyncClient", return_value=mock_context_manager):
            result = await run_skeptic(claim, evidence)

            assert isinstance(result, SkepticOutput)
            assert result.skepticism_score == 50.0  # Default
            assert "Skeptic analysis failed" in result.ambiguity_points

    @pytest.mark.asyncio
    async def test_strips_markdown_code_block(self, claim, evidence):
        llm_response = '```json\n{"counter_arguments": [], "ambiguity_points": [], "missing_evidence": [], "skepticism_score": 60}\n```'

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": llm_response}}]}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_client
        mock_context_manager.__aexit__.return_value = False

        with patch("app.services.skeptic.httpx.AsyncClient", return_value=mock_context_manager):
            result = await run_skeptic(claim, evidence)

            assert result.skepticism_score == 60.0

    @pytest.mark.asyncio
    async def test_builds_correct_prompt(self, claim, evidence):
        llm_response = '{"counter_arguments": [], "ambiguity_points": [], "missing_evidence": [], "skepticism_score": 50}'

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": llm_response}}]}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_client
        mock_context_manager.__aexit__.return_value = False

        with patch("app.services.skeptic.httpx.AsyncClient", return_value=mock_context_manager):
            await run_skeptic(claim, evidence)

            call_args = mock_client.post.call_args
            prompt = call_args[1]["json"]["messages"][0]["content"]
            assert "BBCA" in prompt
            assert "profits declined" in prompt
            assert "fundamental" in prompt
