import json

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

from app.services import follow_up
from app.services.claims_store import ClaimsStore


@pytest_asyncio.fixture
async def store():
    s = ClaimsStore()
    s.db_path = ":memory:"
    await s.connect()
    yield s
    await s.disconnect()


def sample_state() -> dict:
    return {
        "claim_id": "claim-1",
        "narrative": "BBCA labanya jeblok, PE-nya masih mahal banget",
        "claim": {
            "ticker": "BBCA",
            "assertion": "PE is expensive",
            "category": "valuation",
            "direction": "below",
        },
        "evidence": {"valuation": {"metrics": {"pe": 25.0}}},
        "score": {"reality_gap_score": 72, "verdict": "high_gap"},
        "skeptic": {"counter_arguments": ["ROE premium justifies PE"]},
        "status": "completed",
    }


def llm_suggestions_json():
    return json.dumps({
        "suggestions": [
            {"id": "s1", "text": "Kenapa PE BBCA dianggap mahal?", "text_en": "Why is BBCA PE considered expensive?"},
            {"id": "s2", "text": "Bukti apa yang menaikkan skor?", "text_en": "What evidence raised the score?"},
            {"id": "s3", "text": "Apa yang bisa mengubah verdict?", "text_en": "What would change the verdict?"},
        ]
    })


class TestGenerateSuggestions:
    @pytest.mark.asyncio
    async def test_generates_from_llm(self, store):
        with patch.object(
            follow_up.claims_store, "recent_followup_feedback", AsyncMock(return_value=[])
        ), patch(
            "app.services.follow_up.llm_client.stream_chat",
            AsyncMock(return_value=llm_suggestions_json()),
        ):
            suggestions = await follow_up.generate_suggestions(sample_state())

        assert len(suggestions) == 3
        assert suggestions[0]["id"] == "s1"
        assert suggestions[0]["text"] == "Kenapa PE BBCA dianggap mahal?"
        assert suggestions[0]["text_en"] == "Why is BBCA PE considered expensive?"

    @pytest.mark.asyncio
    async def test_includes_preference_history_in_prompt(self, store):
        history = [
            {
                "suggestion_text": "Kenapa skornya setinggi ini?",
                "ticker": "BBCA",
                "category": "valuation",
                "verdict": "high_gap",
            }
        ]
        with patch.object(
            follow_up.claims_store, "recent_followup_feedback", AsyncMock(return_value=history)
        ), patch(
            "app.services.follow_up.llm_client.stream_chat",
            AsyncMock(return_value=llm_suggestions_json()),
        ) as mock_chat:
            await follow_up.generate_suggestions(sample_state())

        prompt = mock_chat.call_args.args[1][0]["content"]
        assert "Kenapa skornya setinggi ini?" in prompt
        assert "Preferred categories: valuation" in prompt
        assert "BBCA labanya jeblok" in prompt

    @pytest.mark.asyncio
    async def test_falls_back_on_llm_failure(self, store):
        with patch.object(
            follow_up.claims_store, "recent_followup_feedback", AsyncMock(return_value=[])
        ), patch(
            "app.services.follow_up.llm_client.stream_chat",
            AsyncMock(side_effect=Exception("LLM down")),
        ):
            suggestions = await follow_up.generate_suggestions(sample_state())

        assert suggestions == follow_up.DEFAULT_SUGGESTIONS

    @pytest.mark.asyncio
    async def test_falls_back_on_malformed_json(self, store):
        with patch.object(
            follow_up.claims_store, "recent_followup_feedback", AsyncMock(return_value=[])
        ), patch(
            "app.services.follow_up.llm_client.stream_chat",
            AsyncMock(return_value="not json at all"),
        ):
            suggestions = await follow_up.generate_suggestions(sample_state())

        assert suggestions == follow_up.DEFAULT_SUGGESTIONS

    @pytest.mark.asyncio
    async def test_sanitize_drops_invalid_entries(self, store):
        with patch.object(
            follow_up.claims_store, "recent_followup_feedback", AsyncMock(return_value=[])
        ), patch(
            "app.services.follow_up.llm_client.stream_chat",
            AsyncMock(return_value=json.dumps({
                "suggestions": [
                    {"id": "s1", "text": "", "text_en": ""},
                    "junk",
                    {"id": "s2", "text": "Pertanyaan valid?", "text_en": "A valid question?"},
                ]
            })),
        ):
            suggestions = await follow_up.generate_suggestions(sample_state())

        assert len(suggestions) == 1
        assert suggestions[0]["text"] == "Pertanyaan valid?"


class TestGetSuggestionsCaching:
    @pytest.mark.asyncio
    async def test_generates_once_then_caches(self, store):
        claim_id = await store.create_claim("BBCA labanya jeblok")
        await store.update_claim(claim_id, sample_state())

        with patch.object(follow_up, "claims_store", store), patch(
            "app.services.follow_up.llm_client.stream_chat",
            AsyncMock(return_value=llm_suggestions_json()),
        ) as mock_chat:
            first = await follow_up.get_suggestions(claim_id, sample_state())
            state_after = await store.get_claim(claim_id)
            second = await follow_up.get_suggestions(claim_id, state_after)

        assert first["cached"] is False
        assert len(first["suggestions"]) == 3
        assert state_after["followup_suggestions"] == first["suggestions"]
        assert second["cached"] is True
        assert second["suggestions"] == first["suggestions"]
        mock_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_cached_without_llm_call(self, store):
        claim_id = await store.create_claim("BBCA test")
        cached = [{"id": "s9", "text": "Dari cache?", "text_en": "From cache?"}]
        await store.update_claim(claim_id, {"followup_suggestions": cached})

        with patch.object(follow_up, "claims_store", store), patch(
            "app.services.follow_up.llm_client.stream_chat",
            AsyncMock(return_value=llm_suggestions_json()),
        ) as mock_chat:
            state_after = await store.get_claim(claim_id)
            result = await follow_up.get_suggestions(claim_id, state_after)

        assert result["cached"] is True
        assert result["suggestions"] == cached
        mock_chat.assert_not_called()


class TestRecordFeedback:
    @pytest.mark.asyncio
    async def test_records_clicked_template(self, store):
        with patch.object(follow_up, "claims_store", store):
            recorded = await follow_up.record_feedback(
                "claim-1",
                sample_state(),
                {"id": "s1", "text": "Kenapa PE BBCA dianggap mahal?"},
            )

        assert recorded is True

        recent = await store.recent_followup_feedback(limit=10)
        assert len(recent) == 1
        row = recent[0]
        assert row["claim_id"] == "claim-1"
        assert row["ticker"] == "BBCA"
        assert row["category"] == "valuation"
        assert row["verdict"] == "high_gap"
        assert row["score"] == 72.0
        assert row["suggestion_text"] == "Kenapa PE BBCA dianggap mahal?"

    @pytest.mark.asyncio
    async def test_rejects_empty_text(self, store):
        with patch.object(follow_up, "claims_store", store):
            recorded = await follow_up.record_feedback(
                "claim-1", sample_state(), {"id": "s1", "text": ""}
            )

        assert recorded is False
        recent = await store.recent_followup_feedback(limit=10)
        assert recent == []

    @pytest.mark.asyncio
    async def test_topic_counts(self, store):
        for category in ("valuation", "valuation", "market"):
            await store.record_followup_feedback(
                claim_id="c1",
                ticker="BBCA",
                category=category,
                verdict="high_gap",
                score=70.0,
                suggestion_id="s1",
                suggestion_text="tanya?",
            )

        counts = await store.followup_topic_counts("category")
        assert counts[0] == {"value": "valuation", "clicks": 2}
        assert counts[1] == {"value": "market", "clicks": 1}

    @pytest.mark.asyncio
    async def test_topic_counts_rejects_unknown_field(self, store):
        with pytest.raises(ValueError):
            await store.followup_topic_counts("drop table")


class TestSuggestionsEndpoints:
    @pytest.mark.asyncio
    async def test_get_suggestions_returns_generated_list(self):
        from httpx import AsyncClient, ASGITransport
        from app.main import app

        suggestions = [
            {"id": "s1", "text": "Kenapa skor?", "text_en": "Why the score?"},
        ]
        state = sample_state()
        state["status"] = "completed"

        with patch("app.api.v1.endpoints.claims.claims_store") as mock_store:
            mock_store.get_claim = AsyncMock(return_value=state)
            with patch(
                "app.api.v1.endpoints.claims.get_suggestions",
                AsyncMock(return_value={"claim_id": "claim-1", "suggestions": suggestions, "cached": False}),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get("/api/v1/claims/claim-1/suggestions")

            assert response.status_code == 200
            assert response.json()["suggestions"] == suggestions

    @pytest.mark.asyncio
    async def test_get_suggestions_rejects_non_completed(self):
        from httpx import AsyncClient, ASGITransport
        from app.main import app

        state = sample_state()
        state["status"] = "scored"

        with patch("app.api.v1.endpoints.claims.claims_store") as mock_store:
            mock_store.get_claim = AsyncMock(return_value=state)
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/claims/claim-1/suggestions")

            assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_get_suggestions_404_for_missing_claim(self):
        from httpx import AsyncClient, ASGITransport
        from app.main import app

        with patch("app.api.v1.endpoints.claims.claims_store") as mock_store:
            mock_store.get_claim = AsyncMock(return_value=None)
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/claims/missing/suggestions")

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_record_feedback_endpoint(self):
        from httpx import AsyncClient, ASGITransport
        from app.main import app

        state = sample_state()
        state["status"] = "completed"

        with patch("app.api.v1.endpoints.claims.claims_store") as mock_store:
            mock_store.get_claim = AsyncMock(return_value=state)
            with patch(
                "app.api.v1.endpoints.claims.record_feedback",
                AsyncMock(return_value=True),
            ) as mock_record:
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/claims/claim-1/suggestions/feedback",
                        json={"suggestion_id": "s1", "text": "Kenapa skor?"},
                    )

            assert response.status_code == 200
            assert response.json()["recorded"] is True
            mock_record.assert_awaited_once()


class TestGenerateReplacement:
    @pytest.mark.asyncio
    async def test_replacement_avoids_excluded_questions(self, store):
        with patch.object(
            follow_up.claims_store, "recent_followup_feedback", AsyncMock(return_value=[])
        ), patch(
            "app.services.follow_up.llm_client.stream_chat",
            AsyncMock(return_value=llm_suggestions_json()),
        ):
            replacement = await follow_up.generate_replacement(
                sample_state(),
                exclude=[
                    "Kenapa PE BBCA dianggap mahal?",
                    "Bukti apa yang menaikkan skor?",
                ],
            )

        assert replacement["text"] == "Apa yang bisa mengubah verdict?"

    @pytest.mark.asyncio
    async def test_replacement_falls_back_to_default_when_all_excluded(self, store):
        with patch.object(
            follow_up.claims_store, "recent_followup_feedback", AsyncMock(return_value=[])
        ), patch(
            "app.services.follow_up.llm_client.stream_chat",
            AsyncMock(return_value=llm_suggestions_json()),
        ):
            replacement = await follow_up.generate_replacement(
                sample_state(),
                exclude=[
                    "Kenapa PE BBCA dianggap mahal?",
                    "Bukti apa yang menaikkan skor?",
                    "Apa yang bisa mengubah verdict?",
                ],
            )

        assert replacement["text"] == follow_up.DEFAULT_SUGGESTIONS[0]["text"]
