import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from app.services.pipeline import run_pipeline, make_event, _active_narratives
from app.models.schemas import (
    Claim, ClaimCategory, ClaimDirection, ClaimStatus,
    PipelineEvent, ValuationEvidence, FundamentalEvidence, SkepticOutput, RealityGapScore, VerdictBand,
    FilingsEvidence
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

    @pytest.fixture(autouse=True)
    def _mock_sectors_guard(self):
        with patch("app.services.pipeline.sectors_client.validate_ticker", return_value=True), \
             patch("app.services.pipeline.sectors_client.validate_ticker_exists", new_callable=AsyncMock) as mock_exists:
            mock_exists.return_value = True
            yield

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
            mock_store.find_active_by_narrative = AsyncMock(return_value=None)
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
            mock_store.find_active_by_narrative = AsyncMock(return_value=None)
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
            mock_store.find_active_by_narrative = AsyncMock(return_value=None)
            mock_extract.side_effect = Exception("LLM unavailable")

            events = []
            async for event in run_pipeline("test narrative"):
                events.append(event)

            event_types = [e.event_type for e in events]
            assert "pipeline_error" in event_types

            error_event = next(e for e in events if e.event_type == "pipeline_error")
            assert error_event.data["error"] == "LLM unavailable"

            # Claim must be marked failed, not left pending forever
            failed_update = mock_store.update_claim.call_args_list[-1]
            assert failed_update.args[1]["status"] == ClaimStatus.FAILED.value

    @pytest.mark.asyncio
    async def test_pipeline_handles_evidence_error(self, mock_claim):
        with patch("app.services.pipeline.claims_store") as mock_store, \
             patch("app.services.pipeline.extract_claim", new_callable=AsyncMock) as mock_extract, \
             patch("app.services.pipeline.get_evidence_for_claim", new_callable=AsyncMock) as mock_evidence_fn, \
             patch("app.services.pipeline.run_skeptic", new_callable=AsyncMock) as mock_skeptic_fn:
            
            mock_store.create_claim = AsyncMock(return_value="test-claim-id")
            mock_store.update_claim = AsyncMock()
            mock_store.find_active_by_narrative = AsyncMock(return_value=None)
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
            mock_store.find_active_by_narrative = AsyncMock(return_value=None)
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
            mock_store.find_active_by_narrative = AsyncMock(return_value=None)
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

    @pytest.mark.asyncio
    async def test_pipeline_skips_duplicate_narrative_in_memory(self, mock_claim):
        _active_narratives["BBCA labanya jeblok"] = "existing-claim-id"
        try:
            with patch("app.services.pipeline.claims_store") as mock_store, \
                 patch("app.services.pipeline.extract_claim", new_callable=AsyncMock) as mock_extract:
                mock_store.create_claim = AsyncMock(return_value="test-claim-id")
                mock_store.update_claim = AsyncMock()
                mock_extract.return_value = mock_claim

                events = []
                async for event in run_pipeline("BBCA labanya jeblok"):
                    events.append(event)

                event_types = [e.event_type for e in events]
                assert "pipeline_duplicate" in event_types
                assert "pipeline_started" not in event_types
                duplicate = next(e for e in events if e.event_type == "pipeline_duplicate")
                assert duplicate.data["claim_id"] == "existing-claim-id"
                mock_store.create_claim.assert_not_called()
        finally:
            _active_narratives.pop("BBCA labanya jeblok", None)

    @pytest.mark.asyncio
    async def test_pipeline_supersedes_orphaned_claim_in_store_and_proceeds(self, mock_claim, mock_evidence, mock_skeptic):
        _active_narratives.clear()
        with patch("app.services.pipeline.claims_store") as mock_store, \
             patch("app.services.pipeline.extract_claim", new_callable=AsyncMock) as mock_extract, \
             patch("app.services.pipeline.get_evidence_for_claim", new_callable=AsyncMock) as mock_evidence_fn, \
             patch("app.services.pipeline.run_skeptic", new_callable=AsyncMock) as mock_skeptic_fn:
            mock_store.create_claim = AsyncMock(return_value="test-claim-id")
            mock_store.update_claim = AsyncMock()
            # A non-terminal claim exists in storage but is NOT running in this
            # process (orphaned, even if recently touched) -> supersede it.
            mock_store.find_active_by_narrative = AsyncMock(return_value={
                "claim_id": "existing-claim-id",
                "narrative": "BBCA labanya jeblok",
                "status": "parsed",
                "updated_at": datetime.now().isoformat(),
            })
            mock_extract.return_value = mock_claim
            mock_evidence_fn.return_value = mock_evidence
            mock_skeptic_fn.return_value = mock_skeptic

            events = []
            async for event in run_pipeline("BBCA labanya jeblok"):
                events.append(event)

            event_types = [e.event_type for e in events]
            assert "pipeline_duplicate" not in event_types
            assert "pipeline_started" in event_types

            # The orphaned claim is marked failed so it no longer looks in-progress.
            orphan_update = next(
                c for c in mock_store.update_claim.call_args_list
                if c.args[0] == "existing-claim-id"
            )
            assert orphan_update.args[1]["status"] == ClaimStatus.FAILED.value

    @pytest.mark.asyncio
    async def test_pipeline_marks_claim_failed_on_client_disconnect(self, mock_claim, mock_evidence, mock_skeptic):
        _active_narratives.clear()
        with patch("app.services.pipeline.claims_store") as mock_store, \
             patch("app.services.pipeline.extract_claim", new_callable=AsyncMock) as mock_extract, \
             patch("app.services.pipeline.get_evidence_for_claim", new_callable=AsyncMock) as mock_evidence_fn, \
             patch("app.services.pipeline.run_skeptic", new_callable=AsyncMock) as mock_skeptic_fn:
            mock_store.create_claim = AsyncMock(return_value="test-claim-id")
            mock_store.update_claim = AsyncMock()
            mock_store.find_active_by_narrative = AsyncMock(return_value=None)
            mock_extract.return_value = mock_claim
            mock_evidence_fn.return_value = mock_evidence
            mock_skeptic_fn.return_value = mock_skeptic

            agen = run_pipeline("BBCA labanya jeblok")
            events = []
            async for event in agen:
                events.append(event)
                if event.event_type == "claim_parsed":
                    break

            # Simulate the SSE client dropping the connection mid-stream:
            # closing the async generator raises GeneratorExit, which must
            # mark the claim failed instead of leaving it stuck at "parsed".
            await agen.aclose()

            assert "pipeline_complete" not in [e.event_type for e in events]

            failed_update = next(
                c for c in mock_store.update_claim.call_args_list
                if c.args[0] == "test-claim-id" and c.args[1].get("status") == "failed"
            )
            assert "interrupted" in failed_update.args[1]["error"]
            assert "BBCA labanya jeblok" not in _active_narratives

    @pytest.mark.asyncio
    async def test_pipeline_marks_stale_orphan_failed_and_proceeds(self, mock_claim, mock_evidence, mock_skeptic):
        _active_narratives.clear()
        with patch("app.services.pipeline.claims_store") as mock_store, \
             patch("app.services.pipeline.extract_claim", new_callable=AsyncMock) as mock_extract, \
             patch("app.services.pipeline.get_evidence_for_claim", new_callable=AsyncMock) as mock_evidence_fn, \
             patch("app.services.pipeline.run_skeptic", new_callable=AsyncMock) as mock_skeptic_fn:
            mock_store.create_claim = AsyncMock(return_value="test-claim-id")
            mock_store.update_claim = AsyncMock()
            mock_store.find_active_by_narrative = AsyncMock(return_value=None)
            mock_store.find_active_by_narrative = AsyncMock(return_value={
                "claim_id": "orphan-claim-id",
                "narrative": "BBCA labanya jeblok",
                "status": "parsed",
                "updated_at": (datetime.now() - timedelta(minutes=30)).isoformat(),
            })
            mock_extract.return_value = mock_claim
            mock_evidence_fn.return_value = mock_evidence
            mock_skeptic_fn.return_value = mock_skeptic

            events = []
            async for event in run_pipeline("BBCA labanya jeblok"):
                events.append(event)

            event_types = [e.event_type for e in events]
            assert "pipeline_duplicate" not in event_types
            assert "pipeline_started" in event_types

            orphan_update = next(
                c for c in mock_store.update_claim.call_args_list
                if c.args[0] == "orphan-claim-id"
            )
            assert orphan_update.args[1]["status"] == ClaimStatus.FAILED.value

    @pytest.mark.asyncio
    async def test_pipeline_clears_active_registry_after_run(self, mock_claim, mock_evidence, mock_skeptic):
        _active_narratives.clear()
        with patch("app.services.pipeline.claims_store") as mock_store, \
             patch("app.services.pipeline.extract_claim", new_callable=AsyncMock) as mock_extract, \
             patch("app.services.pipeline.get_evidence_for_claim", new_callable=AsyncMock) as mock_evidence_fn, \
             patch("app.services.pipeline.run_skeptic", new_callable=AsyncMock) as mock_skeptic_fn:
            mock_store.create_claim = AsyncMock(return_value="test-claim-id")
            mock_store.update_claim = AsyncMock()
            mock_store.find_active_by_narrative = AsyncMock(return_value=None)
            mock_store.find_active_by_narrative = AsyncMock(return_value=None)
            mock_extract.return_value = mock_claim
            mock_evidence_fn.return_value = mock_evidence
            mock_skeptic_fn.return_value = mock_skeptic

            async for _ in run_pipeline("BBCA labanya jeblok"):
                pass

            assert "BBCA labanya jeblok" not in _active_narratives

    @pytest.mark.asyncio
    async def test_pipeline_streams_filings_evidence_for_insider_trading(self):
        _active_narratives.clear()
        claim = Claim(
            ticker="BBCA",
            category=ClaimCategory.INSIDER_TRADING,
            assertion="insiders are selling",
            direction=ClaimDirection.BELOW,
            confidence=0.8,
            claim_id="test-claim-id",
        )
        filings_evidence = FilingsEvidence(
            claim_ticker="BBCA",
            category="insider_trading",
            filings=[
                {"date": "2025-08-15", "insider_name": "Budi", "insider_title": "Direktur", "transaction_type": "sell", "shares": 50000, "price": 9500, "total_value": 475_000_000}
            ],
            summary="Terdapat 1 transaksi insider: 0 pembelian, 1 penjualan. Pola: net_selling.",
            recent_bias="net_selling",
            evidence_freshness="2024-01-01",
            cache_hit=False,
        )
        skeptic = SkepticOutput(
            claim_ticker="BBCA",
            counter_arguments=[],
            ambiguity_points=[],
            missing_evidence=[],
            skepticism_score=50.0,
        )

        with patch("app.services.pipeline.claims_store") as mock_store, \
             patch("app.services.pipeline.extract_claim", new_callable=AsyncMock) as mock_extract, \
             patch("app.services.pipeline.get_evidence_for_claim", new_callable=AsyncMock) as mock_evidence_fn, \
             patch("app.services.pipeline.run_skeptic", new_callable=AsyncMock) as mock_skeptic_fn:
            mock_store.create_claim = AsyncMock(return_value="test-claim-id")
            mock_store.update_claim = AsyncMock()
            mock_store.find_active_by_narrative = AsyncMock(return_value=None)
            mock_extract.return_value = claim
            mock_evidence_fn.return_value = {"insider_trading": filings_evidence, "filings": filings_evidence}
            mock_skeptic_fn.return_value = skeptic

            events = []
            async for event in run_pipeline("BBCA insiders are dumping shares"):
                events.append(event)

            event_types = [e.event_type for e in events]
            assert "pipeline_complete" in event_types

            evidence_ready = next(e for e in events if e.event_type == "evidence_ready")
            assert "filings" in evidence_ready.data
            assert evidence_ready.data["filings"]["recent_bias"] == "net_selling"
            assert "insider_trading" in evidence_ready.data

            # Claim store must persist filings evidence
            evidence_update = next(
                c for c in mock_store.update_claim.call_args_list
                if c.args[1].get("evidence") is not None
            )
            assert "filings" in evidence_update.args[1]["evidence"]


class TestTickerGuardrail:
    """Tests for the ticker clarification guardrail that halts deep analysis."""

    @pytest.fixture
    def _patch_pipeline(self):
        mock_store = AsyncMock()
        mock_store.create_claim = AsyncMock(return_value="clarify-claim-id")
        mock_store.update_claim = AsyncMock()
        mock_store.find_active_by_narrative = AsyncMock(return_value=None)
        return mock_store

    @pytest.mark.asyncio
    async def test_clarification_halts_pipeline_and_emits_event(self, _patch_pipeline):
        claim = Claim(
            ticker="",
            category=ClaimCategory.VALUATION,
            assertion="Saham mahal",
            direction=ClaimDirection.ABOVE,
            confidence=0.5,
            claim_id="clarify-claim-id",
            ticker_valid=False,
            needs_clarification=True,
            missing=["ticker"],
            reason="No valid 4-letter ticker identified in the narrative",
            reason_id="Mohon berikan kode saham (mis. BBCA)?",
        )
        with patch("app.services.pipeline.claims_store", _patch_pipeline), \
             patch("app.services.pipeline.extract_claim", new_callable=AsyncMock) as mock_extract, \
             patch("app.services.pipeline.get_evidence_for_claim", new_callable=AsyncMock) as mock_evidence:
            mock_extract.return_value = claim

            events = []
            async for event in run_pipeline("Saham perbankan lagi mahal nih"):
                events.append(event)

        event_types = [e.event_type for e in events]
        assert "clarification_required" in event_types
        assert "pipeline_complete" not in event_types
        assert "evidence_fetching" not in event_types

        clarification = next(e for e in events if e.event_type == "clarification_required")
        assert clarification.data["claim_id"] == "clarify-claim-id"
        assert "ticker" in clarification.data["missing"]
        assert clarification.data["reason_id"]

        mock_evidence.assert_not_called()

    @pytest.mark.asyncio
    async def test_clarification_marks_claim_failed(self, _patch_pipeline):
        claim = Claim(
            ticker="",
            category=ClaimCategory.VALUATION,
            assertion="Saham mahal",
            direction=ClaimDirection.ABOVE,
            confidence=0.5,
            claim_id="clarify-claim-id",
            needs_clarification=True,
            missing=["ticker"],
        )
        with patch("app.services.pipeline.claims_store", _patch_pipeline), \
             patch("app.services.pipeline.extract_claim", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = claim

            async for _ in run_pipeline("Saham mahal"):
                pass

        last_update = _patch_pipeline.update_claim.call_args_list[-1].args[1]
        assert last_update["status"] == ClaimStatus.FAILED.value
        assert last_update["needs_clarification"] is True

    @pytest.mark.asyncio
    async def test_invalid_format_ticker_triggers_clarification(self, _patch_pipeline):
        claim = Claim(
            ticker="UNKNOWN",
            category=ClaimCategory.VALUATION,
            assertion="Saham mahal",
            direction=ClaimDirection.ABOVE,
            confidence=0.5,
            claim_id="clarify-claim-id",
            ticker_valid=False,
        )
        with patch("app.services.pipeline.claims_store", _patch_pipeline), \
             patch("app.services.pipeline.extract_claim", new_callable=AsyncMock) as mock_extract, \
             patch("app.services.pipeline.sectors_client.validate_ticker", return_value=False):
            mock_extract.return_value = claim

            events = []
            async for event in run_pipeline("Saham mahal nih"):
                events.append(event)

        event_types = [e.event_type for e in events]
        assert "clarification_required" in event_types
        assert "evidence_fetching" not in event_types
