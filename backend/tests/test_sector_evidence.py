import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.sector_evidence import (
    get_sector_evidence,
    sample_claim_for_member,
    gather_member_evidence,
)
from app.models.schemas import ClaimCategory


@pytest.fixture(autouse=True)
def _noop_cache_hit_counter():
    with patch("app.services.sector_evidence.record_sectors_cache_hit"):
        yield


class TestSampleClaimForMember:
    def test_builds_claim_shaped_object(self):
        c = sample_claim_for_member("ADRO", ClaimCategory.MARKET)
        assert c.ticker == "ADRO"
        assert c.category == ClaimCategory.MARKET
        assert c.ticker_valid is True


class TestGetSectorEvidence:
    @pytest.mark.asyncio
    async def test_populates_sector_keyed_entry_on_miss(self):
        with patch("app.services.sector_evidence.cache") as mock_cache, \
             patch("app.services.sector_evidence.gather_member_evidence") as mock_gather, \
             patch("app.services.sector_evidence.record_sectors_cache_hit") as mock_hit:
            mock_cache.get_sector = AsyncMock(return_value=None)
            mock_cache.set_sector = AsyncMock()
            mock_gather.return_value = {"market": {"performance": {"1d": {}}}}

            result = await get_sector_evidence("coal", ["ADRO", "ITMG"], ClaimCategory.MARKET)

            assert result["sector"] == "coal"
            assert result["members"] == ["ADRO", "ITMG"]
            assert "by_member" in result
            assert "ADRO" in result["by_member"]
            assert "fetched_at" in result
            mock_cache.set_sector.assert_awaited_once()
            mock_hit.assert_not_called()

    @pytest.mark.asyncio
    async def test_reuses_sector_entry_on_hit_no_new_fetch(self):
        existing = {
            "sector": "oil-gas",
            "members": ["PGAS", "MEDC"],
            "by_member": {"PGAS": {"news": {}}, "MEDC": {"news": {}}},
            "fetched_at": "2026-01-01T00:00:00",
        }
        with patch("app.services.sector_evidence.cache") as mock_cache, \
             patch("app.services.sector_evidence.gather_member_evidence") as mock_gather, \
             patch("app.services.sector_evidence.record_sectors_cache_hit") as mock_hit:
            mock_cache.get_sector = AsyncMock(return_value=existing)

            second = await get_sector_evidence("oil-gas", ["PGAS", "MEDC"], ClaimCategory.MARKET)

            assert second is existing
            mock_gather.assert_not_awaited()
            mock_hit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_hit_counts_sectors_cache_hit(self):
        existing = {"sector": "coal", "members": ["ADRO"], "by_member": {}, "fetched_at": "2026-01-01T00:00:00"}
        with patch("app.services.sector_evidence.cache") as mock_cache, \
             patch("app.services.sector_evidence.record_sectors_cache_hit") as mock_hit:
            mock_cache.get_sector = AsyncMock(return_value=existing)
            await get_sector_evidence("coal", ["ADRO"], ClaimCategory.MARKET)
            mock_hit.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_members_returns_empty_aggregate(self):
        with patch("app.services.sector_evidence.cache") as mock_cache, \
             patch("app.services.sector_evidence.gather_member_evidence") as mock_gather:
            mock_cache.get_sector = AsyncMock(return_value=None)
            mock_cache.set_sector = AsyncMock()
            result = await get_sector_evidence("utilities", [], ClaimCategory.MARKET)
            assert result["members"] == []
            assert result["by_member"] == {}
            mock_gather.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_member_failure_does_not_kill_sector(self):
        with patch("app.services.sector_evidence.cache") as mock_cache, \
             patch("app.services.sector_evidence.gather_member_evidence") as mock_gather:
            mock_cache.get_sector = AsyncMock(return_value=None)
            mock_cache.set_sector = AsyncMock()
            async def flaky(_t):
                raise RuntimeError("boom")
            mock_gather.side_effect = flaky

            result = await get_sector_evidence("coal", ["ADRO"], ClaimCategory.MARKET)
            assert "error" in result["by_member"]["ADRO"]

    @pytest.mark.asyncio
    async def test_serializes_pydantic_members(self):
        from app.models.schemas import MarketEvidence
        async def agent(_t, _c):
            return {"market": MarketEvidence(
                claim_ticker="ADRO", category="market", performance={"1d": {"price_change_pct": 1.0}},
                volatility=1.0, evidence_freshness="2026-01-01", cache_hit=False,
            )}
        with patch("app.services.sector_evidence.cache") as mock_cache, \
             patch("app.services.sector_evidence.gather_member_evidence", new=agent):
            mock_cache.get_sector = AsyncMock(return_value=None)
            mock_cache.set_sector = AsyncMock()
            result = await get_sector_evidence("coal", ["ADRO"], ClaimCategory.MARKET)
            serialized = result["by_member"]["ADRO"]
            assert not hasattr(serialized["market"], "model_dump")
            assert isinstance(serialized["market"], dict)


class TestPipelineSectorBranch:
    @pytest.mark.asyncio
    async def test_sector_evidence_ready_event_emitted(self):
        from app.services.pipeline import run_pipeline
        from app.core import llm_client
        from unittest.mock import MagicMock
        from app.core.evidence_cache import cache
        from app.services.sector_evidence import get_sector_evidence

        mock_store = MagicMock()
        mock_store.create_claim = AsyncMock(return_value="test-claim")
        mock_store.update_claim = AsyncMock()
        mock_store.find_active_by_narrative = AsyncMock(return_value=None)
        mock_store.get_claim = AsyncMock(return_value=None)

        llm_response = '{"ticker": "UNKNOWN", "category": "market", "assertion": "batu bara naik", "direction": "above", "confidence": 0.8}'
        with patch.object(llm_client, "stream_chat", new_callable=AsyncMock) as mock_llm, \
             patch("app.services.pipeline.claims_store", mock_store), \
             patch("app.services.pipeline.sectors_client.validate_ticker_exists", new_callable=AsyncMock) as exists, \
             patch("app.services.pipeline.get_sector_evidence", new_callable=AsyncMock) as mock_gse:
            mock_llm.return_value = llm_response
            exists.return_value = True
            mock_gse.return_value = {"sector": "coal", "members": ["ADRO", "ITMG", "PTBA"], "by_member": {}, "fetched_at": "2026-01-01"}

            events = []
            async for ev in run_pipeline("Harga batu bara naik"):
                events.append(ev)

        types = [e.event_type for e in events]
        assert "policy_sector_resolved" in types
        assert "sector_evidence_ready" in types


class TestSectorKeyedCacheSemantics:
    """Sector-keyed cache methods must match ticker-keyed semantics."""

    def _make_cache_with_redis(self):
        from app.core.evidence_cache import EvidenceGraphCache
        inst = EvidenceGraphCache()
        inst._redis = MagicMock()
        return inst

    @pytest.mark.asyncio
    async def test_get_sector_parses_json_from_redis_key(self):
        inst = self._make_cache_with_redis()
        payload = '{"sector": "coal", "members": ["ADRO"]}'
        inst._redis.get = AsyncMock(return_value=payload)
        result = await inst.get_sector("coal")
        assert result == {"sector": "coal", "members": ["ADRO"]}
        inst._redis.get.assert_awaited_once_with("evidence:sector:coal")

    @pytest.mark.asyncio
    async def test_get_sector_none_returns_none(self):
        inst = self._make_cache_with_redis()
        inst._redis.get = AsyncMock(return_value=None)
        assert await inst.get_sector("coal") is None

    @pytest.mark.asyncio
    async def test_set_sector_uses_sector_key_with_ttl(self):
        inst = self._make_cache_with_redis()
        inst._redis.setex = AsyncMock()
        await inst.set_sector("coal", {"members": ["ADRO"]}, ttl=999)
        key, ttl, payload = inst._redis.setex.await_args.args
        assert key == "evidence:sector:coal"
        assert ttl == 999
        assert '"ADRO"' in payload

    @pytest.mark.asyncio
    async def test_merge_sector_preserves_other_keys(self):
        inst = self._make_cache_with_redis()
        inst._redis.get = AsyncMock(return_value='{"members": ["ADRO"], "news": {"h": 1}}')
        inst._redis.setex = AsyncMock()
        await inst.merge_sector("coal", "news", {"h": 2})
        _, _, payload = inst._redis.setex.await_args.args
        import json
        merged = json.loads(payload)
        assert merged["members"] == ["ADRO"]
        assert merged["news"] == {"h": 2}

    @pytest.mark.asyncio
    async def test_merge_sector_creates_when_missing(self):
        inst = self._make_cache_with_redis()
        inst._redis.get = AsyncMock(return_value=None)
        inst._redis.setex = AsyncMock()
        await inst.merge_sector("coal", "news", {"h": 1})
        _, _, payload = inst._redis.setex.await_args.args
        import json
        merged = json.loads(payload)
        assert merged == {"news": {"h": 1}}

    @pytest.mark.asyncio
    async def test_invalidate_sector_deletes_key(self):
        inst = self._make_cache_with_redis()
        inst._redis.delete = AsyncMock()
        await inst.invalidate_sector("coal")
        inst._redis.delete.assert_awaited_once_with("evidence:sector:coal")

    @pytest.mark.asyncio
    async def test_is_sector_stale_returns_true_when_missing(self):
        inst = self._make_cache_with_redis()
        inst._redis.get = AsyncMock(return_value=None)
        assert await inst.is_sector_stale("coal", "daily_transaction") is True

    @pytest.mark.asyncio
    async def test_is_sector_stale_respects_daily_ttl(self, monkeypatch):
        import json as _json
        from datetime import datetime, timedelta
        from app.core import evidence_cache as ec_mod
        now = datetime.now()
        monkeypatch.setattr(ec_mod.settings, "EVIDENCE_CACHE_TTL_DAILY", 3600)
        inst = self._make_cache_with_redis()
        inst._redis.get = AsyncMock(return_value=_json.dumps({
            "daily_transaction": [],
            "fetched_at": (now - timedelta(seconds=1800)).isoformat(),
        }))
        assert await inst.is_sector_stale("coal", "daily_transaction") is False
        inst._redis.get = AsyncMock(return_value=_json.dumps({
            "daily_transaction": [],
            "fetched_at": (now - timedelta(seconds=5400)).isoformat(),
        }))
        assert await inst.is_sector_stale("coal", "daily_transaction") is True
