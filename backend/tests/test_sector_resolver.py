import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.sector_resolver import resolve_sector_from_narrative, SectorResolution, ALL_POLICY_KEYWORDS
from app.services.claim_parser import extract_claim
from app.models.schemas import ClaimCategory, ClaimDirection


class TestSectorResolver:
    def test_resolves_bbm_subsidy(self):
        r = resolve_sector_from_narrative("subsidi BBM harus ditinjau ulang")
        assert r is not None
        assert r.sector == "oil-gas"
        assert r.members == ["PGAS", "MEDC"]
        assert r.keyword_matched == "subsidi bbm"
        assert r.source == "anchored"

    def test_resolves_coal_keyword(self):
        r = resolve_sector_from_narrative("Harga batu bara sedang turun tajam")
        assert r is not None
        assert r.sector == "coal"
        assert set(r.members) == {"ADRO", "ITMG", "PTBA"}

    def test_longest_keyword_wins(self):
        r = resolve_sector_from_narrative("kebijakan subsidi bbm pertamina")
        assert isinstance(r, SectorResolution)
        assert r.keyword_matched == "subsidi bbm"
        assert r.sector == "oil-gas"

    def test_single_word_bbm_resolves(self):
        r = resolve_sector_from_narrative("Kebijakan BBM terbaru")
        assert r is not None
        assert r.sector == "oil-gas"
        assert r.keyword_matched == "bbm"

    def test_returns_none_for_unrelated_text(self):
        r = resolve_sector_from_narrative("Saham BBCA naik terus minggu ini")
        assert r is None

    def test_empty_text_returns_none(self):
        r = resolve_sector_from_narrative("")
        assert r is None

    def test_case_insensitive(self):
        r = resolve_sector_from_narrative("POLA SUBSIDI BBM SANGAT KETAT")
        assert r is not None
        assert r.sector == "oil-gas"

    def test_deterministic_same_input_same_output(self):
        text = "pertamina kebijakan energi nasional"
        results = [resolve_sector_from_narrative(text) for _ in range(100)]
        assert len(results) == 100
        for r in results:
            assert isinstance(r, SectorResolution)
            assert r.sector == "oil-gas"
            assert r.keyword_matched == "pertamina"

    def test_utilities_resolves_to_empty_members(self):
        r = resolve_sector_from_narrative("tarif listrik dinaikkan")
        assert r is not None
        assert r.sector == "utilities"
        assert r.members == []

    def test_all_keywords_are_lowercase(self):
        for kw in ALL_POLICY_KEYWORDS:
            assert kw == kw.lower(), f"Keyword {kw!r} must be lowercase"


class TestExtractClaimPolicyIntegration:
    @pytest.mark.asyncio
    async def test_policy_narrative_sets_is_policy(self):
        llm_response = '{"ticker": "UNKNOWN", "category": "market", "assertion": "subsidi BBM naik", "direction": "above", "confidence": 0.8}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = llm_response
            claim = await extract_claim("Subsidi BBM dinaikkan pemerintah tahun depan")
        assert claim.is_policy is True
        assert claim.sector == "oil-gas"
        assert claim.sector_members == ["PGAS", "MEDC"]
        assert claim.needs_clarification is False
        assert claim.ticker_valid is False

    @pytest.mark.asyncio
    async def test_valid_ticker_not_affected_by_policy_resolver(self):
        llm_response = '{"ticker": "BBCA", "category": "fundamental", "assertion": "labanya turun", "direction": "below", "confidence": 0.9}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = llm_response
            claim = await extract_claim("BBCA labanya jeblok")
        assert claim.ticker == "BBCA"
        assert claim.ticker_valid is True
        assert claim.is_policy is False
        assert claim.sector is None

    @pytest.mark.asyncio
    async def test_unrelated_narrative_falls_through_to_clarification(self):
        llm_response = '{"ticker": "UNKNOWN", "category": "valuation", "assertion": "murah", "direction": "below", "confidence": 0.5}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = llm_response
            claim = await extract_claim("Nilai pasar sesuatu murah sekali")
        assert claim.needs_clarification is True
        assert claim.is_policy is False

    @pytest.mark.asyncio
    async def test_llm_clarification_flag_still_wins(self):
        llm_response = '{"ticker": "UNKNOWN", "needs_clarification": true, "category": "market", "assertion": "batu bara", "direction": "neutral", "confidence": 0.3}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = llm_response
            claim = await extract_claim("Narasi ambigu tanpa konteks")
        assert claim.needs_clarification is True

    @pytest.mark.asyncio
    async def test_existing_claim_fields_preserved(self):
        llm_response = '{"ticker": "BBCA", "category": "fundamental", "assertion": "profit up", "direction": "above", "confidence": 0.85}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = llm_response
            claim = await extract_claim("BBCA labanya naik")
        assert claim.ticker == "BBCA"
        assert claim.ticker_valid is True
        assert claim.is_policy is False
        assert claim.sector is None
        assert claim.sector_members is None


class TestPipelinePolicyGuardrail:
    @pytest.fixture(autouse=True)
    def _mock_pipeline_deps(self):
        from unittest.mock import MagicMock, AsyncMock as _AM
        mock_store = MagicMock()
        mock_store.create_claim = _AM(return_value="test-claim")
        mock_store.update_claim = _AM()
        mock_store.find_active_by_narrative = _AM(return_value=None)
        mock_store.get_claim = _AM(return_value=None)
        with patch("app.services.pipeline.claims_store", mock_store), \
             patch("app.services.pipeline.sectors_client.validate_ticker_exists", new_callable=AsyncMock) as exists:
            exists.return_value = True
            yield mock_store

    @pytest.mark.asyncio
    async def test_policy_claim_skips_clarification_and_ticker_exists(self):
        """Policy claim should NOT hit clarification_required or ticker-not-found."""
        from app.services.pipeline import run_pipeline
        from app.core import llm_client
        llm_response = '{"ticker": "UNKNOWN", "category": "market", "assertion": "BBM naik", "direction": "above", "confidence": 0.8}'
        with patch.object(llm_client, "stream_chat", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = llm_response
            events = []
            async for ev in run_pipeline("Subsidi BBM dinaikkan pemerintah"):
                events.append(ev)

        event_types = [e.event_type for e in events]
        assert "clarification_required" not in event_types
        assert "policy_sector_resolved" in event_types

    @pytest.mark.asyncio
    async def test_ticker_narrative_still_validates_ticker(self):
        """Ticker-bearing claim should go through the normal ticker gate."""
        from app.services.pipeline import run_pipeline
        from app.core import llm_client
        llm_response = '{"ticker": "BBCA", "category": "valuation", "assertion": "mahal", "direction": "above", "confidence": 0.8}'
        with patch.object(llm_client, "stream_chat", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = llm_response
            events = []
            async for ev in run_pipeline("BBCA mahal sekali"):
                events.append(ev)
        event_types = [e.event_type for e in events]
        assert "clarification_required" not in event_types
        assert "claim_parsed" in event_types
