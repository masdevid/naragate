import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.claims_store import ClaimsStore
from app.models.schemas import Claim, ClaimCategory, ClaimDirection, ClaimStatus


class TestClaimsStore:
    """Tests for Redis-backed claims store."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis_mock = AsyncMock()
        redis_mock.hset = AsyncMock()
        redis_mock.hget = AsyncMock()
        redis_mock.expire = AsyncMock()
        redis_mock.scan_iter = AsyncMock()
        redis_mock.aclose = AsyncMock()
        return redis_mock

    @pytest.fixture
    def store(self, mock_redis):
        """ClaimsStore with mocked Redis."""
        s = ClaimsStore()
        s.redis = mock_redis
        return s

    @pytest.mark.asyncio
    async def test_create_claim_returns_claim_id(self, store, mock_redis):
        claim_id = await store.create_claim("BBCA labanya jeblok")
        assert claim_id is not None
        assert len(claim_id) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_create_claim_stores_narrative(self, store, mock_redis):
        await store.create_claim("BBCA labanya jeblob")
        call_args = mock_redis.hset.call_args
        assert "claim:" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_create_claim_sets_pending_status(self, store, mock_redis):
        await store.create_claim("BBCA test")
        call_args = mock_redis.hset.call_args
        import json
        state = json.loads(call_args[1]["mapping"]["state"])
        assert state["status"] == ClaimStatus.PENDING.value

    @pytest.mark.asyncio
    async def test_create_claim_with_parsed_claim(self, store, mock_redis):
        claim = Claim(
            ticker="BBCA",
            category=ClaimCategory.FUNDAMENTAL,
            assertion="profits declined",
            direction=ClaimDirection.BELOW,
            confidence=0.9,
        )
        claim_id = await store.create_claim("BBCA labanya jeblok", claim=claim)
        
        call_args = mock_redis.hset.call_args
        import json
        state = json.loads(call_args[1]["mapping"]["state"])
        assert state["status"] == ClaimStatus.PARSED.value
        assert state["claim"]["ticker"] == "BBCA"

    @pytest.mark.asyncio
    async def test_get_claim_returns_none_for_missing(self, store, mock_redis):
        mock_redis.hget.return_value = None
        result = await store.get_claim("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_claim_returns_state(self, store, mock_redis):
        import json
        state = {"claim_id": "test-123", "status": "pending"}
        mock_redis.hget.return_value = json.dumps(state)
        
        result = await store.get_claim("test-123")
        assert result["claim_id"] == "test-123"
        assert result["status"] == "pending"

    @pytest.mark.asyncio
    async def test_update_claim_merges_updates(self, store, mock_redis):
        import json
        state = {"claim_id": "test-123", "status": "pending", "created_at": "2024-01-01"}
        mock_redis.hget.return_value = json.dumps(state)
        
        await store.update_claim("test-123", {"status": "parsed"})
        
        call_args = mock_redis.hset.call_args
        updated = json.loads(call_args[1]["mapping"]["state"])
        assert updated["status"] == "parsed"
        assert "updated_at" in updated

    @pytest.mark.asyncio
    async def test_update_claim_returns_none_for_missing(self, store, mock_redis):
        mock_redis.hget.return_value = None
        result = await store.update_claim("nonexistent", {"status": "parsed"})
        assert result is None

    @pytest.mark.asyncio
    async def test_set_claim_status(self, store, mock_redis):
        import json
        state = {"claim_id": "test-123", "status": "pending"}
        mock_redis.hget.return_value = json.dumps(state)
        
        await store.set_claim_status("test-123", ClaimStatus.EVIDENCE_RETRIEVED)
        
        call_args = mock_redis.hset.call_args
        updated = json.loads(call_args[1]["mapping"]["state"])
        assert updated["status"] == ClaimStatus.EVIDENCE_RETRIEVED.value

    @pytest.mark.asyncio
    async def test_set_claim_data(self, store, mock_redis):
        import json
        state = {"claim_id": "test-123", "status": "parsed"}
        mock_redis.hget.return_value = json.dumps(state)
        
        evidence = {"metrics": {"pe": 25.5}}
        await store.set_claim_data("test-123", "evidence", evidence)
        
        call_args = mock_redis.hset.call_args
        updated = json.loads(call_args[1]["mapping"]["state"])
        assert updated["evidence"] == evidence

    @pytest.mark.asyncio
    async def test_list_claims_returns_sorted_by_created_at(self, store, mock_redis):
        import json
        
        async def mock_scan_iter(pattern, count=100):
            for key in ["claim:2", "claim:1", "claim:3"]:
                yield key
        
        mock_redis.scan_iter = mock_scan_iter
        
        states = {
            "claim:1": {"claim_id": "1", "created_at": "2024-01-01"},
            "claim:2": {"claim_id": "2", "created_at": "2024-01-03"},
            "claim:3": {"claim_id": "3", "created_at": "2024-01-02"},
        }
        
        async def mock_hget(key, field):
            return json.dumps(states.get(key))
        
        mock_redis.hget = mock_hget
        
        claims = await store.list_claims()
        assert len(claims) == 3
        assert claims[0]["created_at"] == "2024-01-03"
        assert claims[1]["created_at"] == "2024-01-02"
        assert claims[2]["created_at"] == "2024-01-01"

    @pytest.mark.asyncio
    async def test_list_claims_respects_limit(self, store, mock_redis):
        import json
        
        async def mock_scan_iter(pattern, count=100):
            for i in range(5):
                yield f"claim:{i}"
        
        mock_redis.scan_iter = mock_scan_iter
        
        async def mock_hget(key, field):
            idx = key.split(":")[1]
            return json.dumps({"claim_id": key, "created_at": f"2024-01-0{idx}"})
        
        mock_redis.hget = mock_hget
        
        claims = await store.list_claims(limit=2)
        assert len(claims) == 2

    @pytest.mark.asyncio
    async def test_claims_summary_aggregates_completed(self, store, mock_redis):
        import json

        async def mock_scan_iter(pattern, count=100):
            for key in ["claim:1", "claim:2", "claim:3"]:
                yield key

        mock_redis.scan_iter = mock_scan_iter

        states = {
            "claim:1": {
                "claim_id": "1",
                "created_at": "2024-01-01",
                "status": ClaimStatus.COMPLETED.value,
                "narrative": "BBCA mahal",
                "claim": {"ticker": "BBCA"},
                "score": {"reality_gap_score": 45.0, "verdict": "mixed"},
            },
            "claim:2": {
                "claim_id": "2",
                "created_at": "2024-01-02",
                "status": ClaimStatus.COMPLETED.value,
                "narrative": "BBCA murah",
                "claim": {"ticker": "BBCA"},
                "score": {"reality_gap_score": 75.0, "verdict": "supported"},
            },
            "claim:3": {
                "claim_id": "3",
                "created_at": "2024-01-03",
                "status": ClaimStatus.FAILED.value,
                "narrative": "TLKM gagal",
                "claim": {"ticker": "TLKM"},
            },
        }

        async def mock_hget(key, field):
            return json.dumps(states.get(key))

        mock_redis.hget = mock_hget

        summary = await store.claims_summary()
        assert summary["total_analyses"] == 2
        assert summary["average_score"] == 60.0
        assert summary["verdict_distribution"] == {"mixed": 1, "supported": 1}
        assert len(summary["by_ticker"]["BBCA"]) == 2
        assert summary["by_ticker"]["BBCA"][0]["score"] == 45.0
        assert summary["by_ticker"]["BBCA"][1]["score"] == 75.0
