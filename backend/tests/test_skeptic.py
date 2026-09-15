import pytest
from unittest.mock import AsyncMock, patch
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
        llm_response = '{"counter_arguments": [{"point": "test", "point_en": "test en", "evidence_ref": "test", "strength": 80}], "ambiguity_points": ["test"], "ambiguity_points_en": ["test en"], "missing_evidence": ["test"], "missing_evidence_en": ["test en"], "skepticism_score": 75}'

        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = llm_response
            result = await run_skeptic(claim, evidence)

            assert isinstance(result, SkepticOutput)
            assert result.claim_ticker == "BBCA"
            assert result.skepticism_score == 75.0
            assert result.ambiguity_points_en == ["test en"]
            assert result.missing_evidence_en == ["test en"]
            assert result.counter_arguments[0]["point_en"] == "test en"

    @pytest.mark.asyncio
    async def test_handles_llm_failure_gracefully(self, claim, evidence):
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = Exception("LLM unavailable")
            result = await run_skeptic(claim, evidence)

            assert isinstance(result, SkepticOutput)
            assert result.skepticism_score == 50.0  # Default
            assert "Skeptic analysis failed" in result.ambiguity_points

    @pytest.mark.asyncio
    async def test_handles_empty_llm_output_as_failure(self, claim, evidence):
        """A stream that returns nothing usable must not yield a silently empty
        skeptic section (the bug behind the latest claim's blank skeptic)."""
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_llm, \
             patch("app.core.llm_client.extract_json", return_value=None):
            mock_llm.return_value = ""
            result = await run_skeptic(claim, evidence)

            assert isinstance(result, SkepticOutput)
            assert result.skepticism_score == 50.0
            assert "Skeptic analysis failed" in result.ambiguity_points
            assert "Unable to run skeptic analysis" in result.missing_evidence

    @pytest.mark.asyncio
    async def test_strips_markdown_code_block(self, claim, evidence):
        llm_response = '```json\n{"counter_arguments": [], "ambiguity_points": [], "missing_evidence": [], "skepticism_score": 60}\n```'

        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = llm_response
            result = await run_skeptic(claim, evidence)

            assert result.skepticism_score == 60.0

    @pytest.mark.asyncio
    async def test_builds_correct_prompt(self, claim, evidence):
        llm_response = '{"counter_arguments": [], "ambiguity_points": [], "missing_evidence": [], "skepticism_score": 50}'

        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = llm_response
            await run_skeptic(claim, evidence)

            call_args = mock_llm.call_args
            prompt = call_args[0][1][0]["content"]
            assert "BBCA" in prompt
            assert "profits declined" in prompt
            assert "fundamental" in prompt
            assert "point_en" in prompt
            assert "ambiguity_points_en" in prompt
            assert "missing_evidence_en" in prompt