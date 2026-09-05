import pytest
from unittest.mock import AsyncMock, patch

from app.services.chat import answer_followup


class TestFollowUpChat:
    def test_answer_followup_with_evidence(self):
        state = {
            "narrative": "BBCA is overvalued",
            "claim": {"ticker": "BBCA", "assertion": "PE is expensive", "category": "valuation"},
            "evidence": {"valuation": {"metrics": {"pe": 25.0}}},
            "score": {"reality_gap_score": 72, "verdict": "high_gap"},
            "skeptic": {"counter_arguments": ["PE premium is justified by ROE"]},
        }
        with patch(
            "app.services.chat.llm_client.stream_chat",
            AsyncMock(return_value='{"answer": "PE BBCA di atas rata-rata sektor.", "answer_en": "BBCA PE is above sector average."}'),
        ):
            result = asyncio_run(answer_followup(state, "Is BBCA expensive?"))

        assert result["answer"] == "PE BBCA di atas rata-rata sektor."
        assert result["answer_en"] == "BBCA PE is above sector average."

    def test_answer_followup_llm_failure(self):
        state = {"narrative": "test", "claim": {}, "evidence": {}, "score": {}, "skeptic": {}}
        with patch(
            "app.services.chat.llm_client.stream_chat",
            AsyncMock(side_effect=Exception("LLM down")),
        ):
            result = asyncio_run(answer_followup(state, "Any question"))

        assert "Tidak dapat menjawab" in result["answer"]
        assert "Unable to answer" in result["answer_en"]

    def test_answer_followup_malformed_json(self):
        state = {"narrative": "test", "claim": {}, "evidence": {}, "score": {}, "skeptic": {}}
        with patch(
            "app.services.chat.llm_client.stream_chat",
            AsyncMock(return_value="not json at all"),
        ):
            result = asyncio_run(answer_followup(state, "Any question"))

        assert "Tidak dapat menjawab" in result["answer"]


def asyncio_run(coro):
    import asyncio
    return asyncio.run(coro)