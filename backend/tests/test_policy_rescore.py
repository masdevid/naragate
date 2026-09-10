import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.schemas import (
    Claim, ClaimCategory, ClaimDirection, ClaimStatus
)
from app.services.policy_rescore import (
    rescore_sector, rescore_claim, schedule_sector_rescore,
    rescore_registry, open_policy_claim_states,
)


def _market_evidence(price_change_1d: float) -> dict:
    return {"market": {"performance": {"1d": {"price_change_pct": price_change_1d}}, "volatility": 1.0}}


def _news(corroboration: str = "neutral") -> dict:
    return {"news": {"headlines": [], "corroboration": corroboration, "summary": "s", "cache_hit": False}}


def _reply_evidence() -> dict:
    return {"market": {"performance": {"1d": {"price_change_pct": 1.0}}, "volatility": 1.0}, "news": _news()}


def _sector_evidence() -> dict:
    return {
        "sector": "oil-gas",
        "members": ["PGAS", "MEDC"],
        "by_member": {
            "PGAS": _reply_evidence(),
            "MEDC": _reply_evidence(),
        },
        "fetched_at": "2026-01-01",
    }


def _claim_state(claim_id: str, status: str = ClaimStatus.COMPLETED.value,
                 score=None, policy=True, sector="oil-gas") -> dict:
    claim = Claim(
        ticker="PGAS",
        category=ClaimCategory.MARKET,
        assertion="harga bbm naik",
        direction=ClaimDirection.ABOVE,
        confidence=0.7,
        is_policy=policy,
        sector=sector,
        sector_members=["PGAS", "MEDC"] if policy else None,
    )
    return {
        "claim_id": claim_id,
        "narrative": "harga bbm naik",
        "status": status,
        "claim": claim.model_dump(mode="json"),
        "score": score or {},
    }


class TestOpenPolicyClaimStates:
    def test_filters_open_and_sector(self):
        claims = [
            _claim_state("open1", status=ClaimStatus.SCORED.value),
            _claim_state("done1", status=ClaimStatus.COMPLETED.value),
            _claim_state("failed1", status=ClaimStatus.FAILED.value),
            _claim_state("other-sector", status=ClaimStatus.SCORED.value, sector="coal"),
            _claim_state("nonpolicy", status=ClaimStatus.SCORED.value, policy=False),
        ]
        got = open_policy_claim_states("oil-gas", claims)
        ids = {c["claim_id"] for c in got}
        assert ids == {"open1"}


class TestRescoreClaim:
    @pytest.mark.asyncio
    async def test_rescores_and_updates_verdict(self):
        old = {
            "reality_gap_score": 54.2,
            "verdict": "mixed",
        }
        state = _claim_state("open1", status=ClaimStatus.SCORED.value, score=old)

        sector_ev = dict(_sector_evidence())
        # A freshly landed policy-event label in the cached corpus.
        sector_ev["by_member"]["PGAS"]["news"] = {
            "headlines": [{"title": "Pemerintah umumkan subsidi bbm naik", "date": "2026-01-15"}],
            "corroboration": "neutral", "summary": "s", "cache_hit": False,
        }

        with patch("app.services.policy_rescore.cache.get_sector", new_callable=AsyncMock) as mock_get, \
             patch("app.services.policy_rescore.gather_policy_reactions", new_callable=AsyncMock) as mock_react, \
             patch("app.services.policy_rescore.claims_store.update_claim", new_callable=AsyncMock) as mock_update:
            mock_get.return_value = sector_ev
            mock_react.return_value = [
                {"ticker": "PGAS", "post_return": 8.0, "prior_return": 0.0},
                {"ticker": "MEDC", "post_return": 8.0, "prior_return": 0.0},
            ]
            result = await rescore_claim(state)

        assert result is not None
        assert result is not None
        assert result["old_verdict"] == "mixed"
        assert result["new_verdict"] == "supported"
        assert result["verdict_changed"] is True
        # Reaction gathering is explicitly cache-only (credit discipline).
        mock_react.assert_called_once()
        assert mock_react.call_args.kwargs["cached_only"] is True
        mock_update.assert_called_once()
        updates = mock_update.call_args.args[1]
        assert updates["score"]["verdict"] == "supported"
        assert updates["rescore"]["trigger"] == "policy_event_label"

    @pytest.mark.asyncio
    async def test_no_cached_sector_evidence_skips(self):
        state = _claim_state("open1", status=ClaimStatus.SCORED.value)
        with patch("app.services.policy_rescore.cache.get_sector", new_callable=AsyncMock) as mock_get, \
             patch("app.services.policy_rescore.claims_store.update_claim", new_callable=AsyncMock) as mock_update:
            mock_get.return_value = None
            result = await rescore_claim(state)
        assert result is not None
        assert result["skipped"] == "no_cached_sector_evidence"
        mock_update.assert_not_called()


class TestRescoreSector:
    @pytest.mark.asyncio
    async def test_rescores_only_open_claims(self):
        claims = [
            _claim_state("open", status=ClaimStatus.SCORED.value),
            _claim_state("done", status=ClaimStatus.COMPLETED.value),
        ]
        with patch("app.services.policy_rescore.claims_store.list_all_claims", new_callable=AsyncMock) as mock_list, \
             patch("app.services.policy_rescore.rescore_claim", new_callable=AsyncMock) as mock_rescore:
            mock_list.return_value = claims
            mock_rescore.return_value = {"claim_id": "open", "verdict_changed": True}
            results = await rescore_sector("oil-gas")
        assert [r["claim_id"] for r in results] == ["open"]


class TestScheduleSectorRescore:
    @pytest.mark.asyncio
    async def test_schedule_runs_background_rescore(self):
        with patch("app.services.policy_rescore.rescore_sector", new_callable=AsyncMock) as mock_run:
            assert schedule_sector_rescore("oil-gas") is True
            await asyncio.sleep(0.05)
        mock_run.assert_awaited_once_with("oil-gas")
        assert rescore_registry._in_flight == set()

    @pytest.mark.asyncio
    async def test_duplicate_schedule_while_in_flight_rejected(self):
        with patch("app.services.policy_rescore.rescore_sector", new_callable=AsyncMock) as mock_run:
            assert schedule_sector_rescore("oil-gas-y") is True
            assert schedule_sector_rescore("oil-gas-y") is False
            await asyncio.sleep(0.05)
        mock_run.assert_awaited_once_with("oil-gas-y")
        assert rescore_registry._in_flight == set()

    def test_empty_sector_no_schedule(self):
        assert schedule_sector_rescore("") is False


class TestPipelineTrigger:
    @pytest.mark.asyncio
    async def test_policy_event_landing_schedules_rescore(self):
        from app.services.pipeline import run_pipeline
        from app.core import llm_client

        mock_store = MagicMock()
        mock_store.create_claim = AsyncMock(return_value="test-claim")
        mock_store.update_claim = AsyncMock()
        mock_store.find_active_by_narrative = AsyncMock(return_value=None)
        mock_store.get_claim = AsyncMock(return_value=None)

        llm_response = '{"ticker": "UNKNOWN", "category": "market", "assertion": "batu bara naik", "direction": "above", "confidence": 0.8}'
        sector_evidence = {
            "sector": "coal",
            "members": ["ADRO"],
            "by_member": {"ADRO": {"news": {"headlines": [
                {"title": "Pemerintah tetapkan hba baru", "date": "2026-03-01"},
            ]}}},
            "fetched_at": "2026-03-01",
        }
        with patch.object(llm_client, "stream_chat", new_callable=AsyncMock) as mock_llm, \
             patch("app.services.pipeline.claims_store", mock_store), \
             patch("app.services.pipeline.sectors_client.validate_ticker_exists", new_callable=AsyncMock) as exists, \
             patch("app.services.pipeline.get_sector_evidence", new_callable=AsyncMock) as mock_gse, \
             patch("app.services.pipeline.schedule_sector_rescore", new_callable=MagicMock) as mock_schedule:
            mock_llm.return_value = llm_response
            exists.return_value = True
            mock_gse.return_value = sector_evidence
            mock_schedule.return_value = True

            events = []
            async for ev in run_pipeline("Harga batu bara naik"):
                events.append(ev)

        mock_schedule.assert_called_once_with("coal")