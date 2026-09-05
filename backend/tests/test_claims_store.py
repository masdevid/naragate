import pytest
import pytest_asyncio
from app.services.claims_store import ClaimsStore
from app.models.schemas import Claim, ClaimCategory, ClaimDirection, ClaimStatus


@pytest_asyncio.fixture
async def store():
    """ClaimsStore backed by an in-memory SQLite database."""
    s = ClaimsStore()
    s.db_path = ":memory:"
    await s.connect()
    yield s
    await s.disconnect()


class TestClaimsStore:
    """Tests for SQLite-backed claims store."""

    @pytest.mark.asyncio
    async def test_create_claim_returns_claim_id(self, store):
        claim_id = await store.create_claim("BBCA labanya jeblok")
        assert claim_id is not None
        assert len(claim_id) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_create_claim_stores_narrative(self, store):
        claim_id = await store.create_claim("BBCA labanya jeblok")
        state = await store.get_claim(claim_id)
        assert state["narrative"] == "BBCA labanya jeblok"

    @pytest.mark.asyncio
    async def test_create_claim_sets_pending_status(self, store):
        claim_id = await store.create_claim("BBCA test")
        state = await store.get_claim(claim_id)
        assert state["status"] == ClaimStatus.PENDING.value

    @pytest.mark.asyncio
    async def test_create_claim_with_parsed_claim(self, store):
        claim = Claim(
            ticker="BBCA",
            category=ClaimCategory.FUNDAMENTAL,
            assertion="profits declined",
            direction=ClaimDirection.BELOW,
            confidence=0.9,
        )
        claim_id = await store.create_claim("BBCA labanya jeblok", claim=claim)

        state = await store.get_claim(claim_id)
        assert state["status"] == ClaimStatus.PARSED.value
        assert state["claim"]["ticker"] == "BBCA"

    @pytest.mark.asyncio
    async def test_get_claim_returns_none_for_missing(self, store):
        result = await store.get_claim("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_claim_returns_state(self, store):
        claim_id = await store.create_claim("BBCA test")
        result = await store.get_claim(claim_id)
        assert result["claim_id"] == claim_id
        assert result["status"] == ClaimStatus.PENDING.value

    @pytest.mark.asyncio
    async def test_update_claim_merges_updates(self, store):
        claim_id = await store.create_claim("BBCA test")
        updated = await store.update_claim(claim_id, {"status": "parsed"})
        assert updated["status"] == "parsed"
        assert "updated_at" in updated

    @pytest.mark.asyncio
    async def test_update_claim_returns_none_for_missing(self, store):
        result = await store.update_claim("nonexistent", {"status": "parsed"})
        assert result is None

    @pytest.mark.asyncio
    async def test_set_claim_status(self, store):
        claim_id = await store.create_claim("BBCA test")
        await store.set_claim_status(claim_id, ClaimStatus.EVIDENCE_RETRIEVED)
        state = await store.get_claim(claim_id)
        assert state["status"] == ClaimStatus.EVIDENCE_RETRIEVED.value

    @pytest.mark.asyncio
    async def test_set_claim_data(self, store):
        claim_id = await store.create_claim("BBCA test")
        evidence = {"metrics": {"pe": 25.5}}
        await store.set_claim_data(claim_id, "evidence", evidence)
        state = await store.get_claim(claim_id)
        assert state["evidence"] == evidence

    @pytest.mark.asyncio
    async def test_list_claims_returns_sorted_by_created_at(self, store):
        await store.create_claim("narrative 1")
        await store.create_claim("narrative 2")
        await store.create_claim("narrative 3")

        claims = await store.list_claims()
        assert len(claims) == 3
        assert claims[0]["created_at"] >= claims[1]["created_at"]
        assert claims[1]["created_at"] >= claims[2]["created_at"]

    @pytest.mark.asyncio
    async def test_list_claims_respects_limit(self, store):
        for i in range(5):
            await store.create_claim(f"narrative {i}")

        claims = await store.list_claims(limit=2)
        assert len(claims) == 2

    @pytest.mark.asyncio
    async def test_claims_summary_aggregates_completed(self, store):
        c1 = await store.create_claim("BBCA mahal")
        await store.update_claim(c1, {
            "status": ClaimStatus.COMPLETED.value,
            "claim": {"ticker": "BBCA"},
            "score": {"reality_gap_score": 45.0, "verdict": "mixed"},
        })

        c2 = await store.create_claim("BBCA murah")
        await store.update_claim(c2, {
            "status": ClaimStatus.COMPLETED.value,
            "claim": {"ticker": "BBCA"},
            "score": {"reality_gap_score": 75.0, "verdict": "supported"},
        })

        c3 = await store.create_claim("TLKM gagal")
        await store.update_claim(c3, {"status": ClaimStatus.FAILED.value})

        summary = await store.claims_summary()
        assert summary["total_analyses"] == 2
        assert summary["average_score"] == 60.0
        assert summary["verdict_distribution"] == {"mixed": 1, "supported": 1}
        assert len(summary["by_ticker"]["BBCA"]) == 2
        assert summary["by_ticker"]["BBCA"][0]["score"] == 45.0
        assert summary["by_ticker"]["BBCA"][1]["score"] == 75.0

    @pytest.mark.asyncio
    async def test_find_active_by_narrative(self, store):
        active_id = await store.create_claim("BBCA mahal")
        await store.create_claim("TLKM gagal")
        await store.update_claim(active_id, {"status": ClaimStatus.PARSED.value})

        found = await store.find_active_by_narrative("BBCA mahal")
        assert found is not None
        assert found["claim_id"] == active_id

    @pytest.mark.asyncio
    async def test_find_active_by_narrative_skips_completed(self, store):
        done_id = await store.create_claim("BBCA mahal")
        await store.update_claim(done_id, {"status": ClaimStatus.COMPLETED.value})

        found = await store.find_active_by_narrative("BBCA mahal")
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_claim(self, store):
        claim_id = await store.create_claim("BBCA test")
        assert await store.delete_claim(claim_id) is True
        assert await store.get_claim(claim_id) is None
        assert await store.delete_claim(claim_id) is False

    @pytest.mark.asyncio
    async def test_delete_claims(self, store):
        ids = [await store.create_claim(f"narrative {i}") for i in range(3)]
        deleted = await store.delete_claims(ids[:2])
        assert deleted == 2
        assert await store.get_claim(ids[0]) is None
        assert await store.get_claim(ids[2]) is not None