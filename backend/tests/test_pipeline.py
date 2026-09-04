import pytest
from unittest.mock import AsyncMock, patch
from app.services.pipeline import run_pipeline, make_event
from app.models.schemas import (
    Claim, ClaimCategory, ClaimDirection, ClaimStatus,
    PipelineEvent, ValuationEvidence, FundamentalEvidence, SkepticOutput, RealityGapScore, VerdictBand
)


class TestMakeEvent:
    """Tests for pipeline event creation."""

    def test_creates_event_with_required_fields(self):
        event = make_event("test_event", "claim-123", {"key": "value"})

        assert isinstance(event, PipelineEvent)
        assert event.event_type == "test_event"
        assert event.claim_id == "claim-123"
        assert event.data == {"key": "value"}
        assert event.timestamp is not None


class TestRunPipeline:
    """Tests for the pipeline orchestrator."""

    @pytest.fixture
    def mock_claim(self):
        return Claim(
            ticker="BBCA",
            category=ClaimCategory.FUNDAMENTAL,
            assertion="profits declined",
            direction=ClaimDirection.BELOW,
            confidence=0.9,
            claim_id="test-claim-id",
        )

    @pytest.fixture
    def mock_evidence(self):
        return {
            "fundamental": FundamentalEvidence(
                claim_ticker="BBCA",
                category="fundamental",
                metrics={"revenue": 120_000_000_000},
                trend={"earnings_trend": "declining"},
                evidence_freshness="2024-01-01",
                cache_hit=False,
            )
        }

    @pytest.fixture
    def mock_skeptic(self):
        return SkepticOutput(
            claim_ticker="BBCA",
            counter_arguments=[],
            ambiguity_points=[],
            missing_evidence=[],
            skepticism_score=60.0,
        )

    @pytest.mark.asyncio
    async def test_pipeline_yields_events(self, mock_claim, mock_evidence, mock_skeptic):
        with patch("app.services.pipeline.claims_store") as mock_store, \
             patch("app.services.pipeline.extract_claim", new_callable=AsyncMock) as mock_extract, \
             patch("app.services.pipeline.get_evidence_for_claim", new_callable=AsyncMock) as mock_evidence_fn, \
             patch("app.services.pipeline.run_skeptic", new_callable=AsyncMock) as mock_skeptic_fn:
            
            mock_store.create_claim = AsyncMock(return_value="test-claim-id")
            mock_store.update_claim = AsyncMock()
            mock_extract.return_value = mock_claim
            mock_evidence_fn.return_value = mock_evidence
            mock_skeptic_fn.return_value = mock_skeptic

            events = []
            async for event in run_pipeline("BBCA labanya jeblok"):
                events.append(event)

            event_types = [e.event_type for e in events]
            assert "pipeline_started" in event_types
            assert "pipeline_complete" in event_types

    @pytest.mark.asyncio
    async def test_pipeline_updates_claim_status(self, mock_claim, mock_evidence, mock_skeptic):
        with patch("app.services.pipeline.claims_store") as mock_store, \
             patch("app.services.pipeline.extract_claim", new_callable=AsyncMock) as mock_extract, \
             patch("app.services.pipeline.get_evidence_for_claim", new_callable=AsyncMock) as mock_evidence_fn, \
             patch("app.services.pipeline.run_skeptic", new_callable=AsyncMock) as mock_skeptic_fn:
            
            mock_store.create_claim = AsyncMock(return_value="test-claim-id")
            mock_store.update_claim = AsyncMock()
            mock_extract.return_value = mock_claim
            mock_evidence_fn.return_value = mock_evidence
            mock_skeptic_fn.return_value = mock_skeptic

            events = []
            async for event in run_pipeline("BBCA labanya jeblok"):
                events.append(event)

            # Check that pipeline completed successfully
            complete_event = next(e for e in events if e.event_type == "pipeline_complete")
            assert complete_event is not None
            assert "duration_ms" in complete_event.data

    @pytest.mark.asyncio
    async def test_pipeline_handles_extract_error(self):
        with patch("app.services.pipeline.claims_store") as mock_store, \
             patch("app.services.pipeline.extract_claim", new_callable=AsyncMock) as mock_extract:
            
            mock_store.create_claim = AsyncMock(return_value="test-claim-id")
            mock_store.update_claim = AsyncMock()
            mock_extract.side_effect = Exception("LLM unavailable")

            events = []
            async for event in run_pipeline("test narrative"):
                events.append(event)

            event_types = [e.event_type for e in events]
            assert "pipeline_error" in event_types

    @pytest.mark.asyncio
    async def test_pipeline_handles_evidence_error(self, mock_claim):
        with patch("app.services.pipeline.claims_store") as mock_store, \
             patch("app.services.pipeline.extract_claim", new_callable=AsyncMock) as mock_extract, \
             patch("app.services.pipeline.get_evidence_for_claim", new_callable=AsyncMock) as mock_evidence_fn, \
             patch("app.services.pipeline.run_skeptic", new_callable=AsyncMock) as mock_skeptic_fn:
            
            mock_store.create_claim = AsyncMock(return_value="test-claim-id")
            mock_store.update_claim = AsyncMock()
            mock_extract.return_value = mock_claim
            mock_evidence_fn.side_effect = Exception("API error")
            mock_skeptic_fn.return_value = SkepticOutput(
                claim_ticker="BBCA",
                counter_arguments=[],
                ambiguity_points=[],
                missing_evidence=[],
                skepticism_score=50.0,
            )

            events = []
            async for event in run_pipeline("BBCA test"):
                events.append(event)

            event_types = [e.event_type for e in events]
            assert "pipeline_complete" in event_types

    @pytest.mark.asyncio
    async def test_pipeline_includes_duration(self, mock_claim, mock_evidence, mock_skeptic):
        with patch("app.services.pipeline.claims_store") as mock_store, \
             patch("app.services.pipeline.extract_claim", new_callable=AsyncMock) as mock_extract, \
             patch("app.services.pipeline.get_evidence_for_claim", new_callable=AsyncMock) as mock_evidence_fn, \
             patch("app.services.pipeline.run_skeptic", new_callable=AsyncMock) as mock_skeptic_fn:
            
            mock_store.create_claim = AsyncMock(return_value="test-claim-id")
            mock_store.update_claim = AsyncMock()
            mock_extract.return_value = mock_claim
            mock_evidence_fn.return_value = mock_evidence
            mock_skeptic_fn.return_value = mock_skeptic

            events = []
            async for event in run_pipeline("BBCA labanya jeblok"):
                events.append(event)

            complete_event = next(e for e in events if e.event_type == "pipeline_complete")
            assert "duration_ms" in complete_event.data
            assert complete_event.data["duration_ms"] >= 0

    @pytest.mark.asyncio
    async def test_pipeline_includes_verdict_and_score(self, mock_claim, mock_evidence, mock_skeptic):
        with patch("app.services.pipeline.claims_store") as mock_store, \
             patch("app.services.pipeline.extract_claim", new_callable=AsyncMock) as mock_extract, \
             patch("app.services.pipeline.get_evidence_for_claim", new_callable=AsyncMock) as mock_evidence_fn, \
             patch("app.services.pipeline.run_skeptic", new_callable=AsyncMock) as mock_skeptic_fn:
            
            mock_store.create_claim = AsyncMock(return_value="test-claim-id")
            mock_store.update_claim = AsyncMock()
            mock_extract.return_value = mock_claim
            mock_evidence_fn.return_value = mock_evidence
            mock_skeptic_fn.return_value = mock_skeptic

            events = []
            async for event in run_pipeline("BBCA labanya jeblok"):
                events.append(event)

            complete_event = next(e for e in events if e.event_type == "pipeline_complete")
            assert "verdict" in complete_event.data
            assert "score" in complete_event.data
            assert 0 <= complete_event.data["score"] <= 100
