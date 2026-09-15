import pytest
import re
from unittest.mock import AsyncMock, patch
from app.services.claim_parser import parse_llm_response, extract_claim
from app.models.schemas import ClaimCategory, ClaimDirection


class TestParseLlmResponse:
    """Tests for parsing LLM JSON responses into claim data."""

    def test_parses_valid_json(self):
        raw = '{"ticker": "BBCA", "category": "fundamental", "assertion": "profits declined", "direction": "below", "confidence": 0.9}'
        result = parse_llm_response(raw)
        assert result["ticker"] == "BBCA"
        assert result["category"] == "fundamental"
        assert result["direction"] == "below"
        assert result["confidence"] == 0.9

    def test_strips_markdown_code_block(self):
        raw = '```json\n{"ticker": "BBRI", "category": "valuation", "assertion": "PE is high", "direction": "above", "confidence": 0.8}\n```'
        result = parse_llm_response(raw)
        assert result["ticker"] == "BBRI"
        assert result["category"] == "valuation"

    def test_returns_fallback_on_invalid_json(self):
        raw = "This is not JSON at all"
        result = parse_llm_response(raw)
        assert result["ticker"] == "UNKNOWN"
        assert result["category"] == "valuation"
        assert result["confidence"] == 0.1
        assert "This is not JSON" in result["assertion"]

    def test_handles_empty_string(self):
        raw = ""
        result = parse_llm_response(raw)
        assert result["ticker"] == "UNKNOWN"
        assert result["confidence"] == 0.1

    def test_handles_whitespace_around_json(self):
        raw = '  \n  {"ticker": "TLKM", "category": "market", "assertion": "price surge", "direction": "above", "confidence": 0.7}  \n  '
        result = parse_llm_response(raw)
        assert result["ticker"] == "TLKM"
        assert result["category"] == "market"


class TestExtractClaim:
    """Tests for extracting claims from narratives using LLM."""

    @pytest.mark.asyncio
    async def test_extracts_claim_from_valid_llm_response(self):
        llm_response = '{"ticker": "BBCA", "category": "fundamental", "assertion": "profits declined", "direction": "below", "confidence": 0.9}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("BBCA labanya jeblok")
            assert claim.ticker == "BBCA"
            assert claim.category == ClaimCategory.FUNDAMENTAL
            assert claim.direction == ClaimDirection.BELOW
            assert claim.confidence == 0.9
            assert claim.ticker_valid is True

    @pytest.mark.asyncio
    async def test_validates_curated_tickers(self):
        llm_response = '{"ticker": "BBCA", "category": "valuation", "assertion": "expensive", "direction": "above", "confidence": 0.8}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("BBCA mahal")
            assert claim.ticker_valid is True

    @pytest.mark.asyncio
    async def test_marks_unknown_ticker_as_invalid(self):
        llm_response = '{"ticker": "XYZZ", "category": "valuation", "assertion": "cheap", "direction": "below", "confidence": 0.7}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("XYZZ murah")
            assert claim.ticker == "XYZZ"
            assert claim.ticker_valid is False

    @pytest.mark.asyncio
    async def test_clamps_confidence_to_valid_range(self):
        llm_response = '{"ticker": "BBCA", "category": "market", "assertion": "price up", "direction": "above", "confidence": 1.5}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("BBCA naik")
            assert claim.confidence == 1.0  # Clamped to max

    @pytest.mark.asyncio
    async def test_handles_negative_confidence(self):
        llm_response = '{"ticker": "BBCA", "category": "market", "assertion": "price down", "direction": "below", "confidence": -0.5}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("BBCA turun")
            assert claim.confidence == 0.0  # Clamped to min

    @pytest.mark.asyncio
    async def test_falls_back_on_invalid_category(self):
        llm_response = '{"ticker": "BBCA", "category": "invalid_category", "assertion": "test", "direction": "neutral", "confidence": 0.5}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("BBCA test")
            assert claim.category == ClaimCategory.VALUATION  # Fallback

    @pytest.mark.asyncio
    async def test_strips_jk_suffix_from_ticker(self):
        llm_response = '{"ticker": "BBCA.JK", "category": "fundamental", "assertion": "test", "direction": "neutral", "confidence": 0.5}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("BBCA test")
            assert claim.ticker == "BBCA"

    @pytest.mark.asyncio
    async def test_preserves_narrative_source(self):
        llm_response = '{"ticker": "BBCA", "category": "market", "assertion": "price up", "direction": "above", "confidence": 0.6}'
        narrative = "BBCA meroket hari ini"
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim(narrative)
            assert claim.narrative_source == narrative

    @pytest.mark.asyncio
    async def test_maps_bilingual_assertion(self):
        llm_response = '{"ticker": "BBCA", "category": "fundamental", "assertion": "laba menurun", "assertion_en": "profits declined", "direction": "below", "confidence": 0.8}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("BBCA labanya jeblok")
            assert claim.assertion == "laba menurun"
            assert claim.assertion_en == "profits declined"

    @pytest.mark.asyncio
    async def test_falls_back_assertion_en_to_assertion(self):
        llm_response = '{"ticker": "BBCA", "category": "fundamental", "assertion": "laba menurun", "direction": "below", "confidence": 0.8}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("BBCA labanya jeblok")
            assert claim.assertion_en == "laba menurun"

    @pytest.mark.asyncio
    async def test_parses_string_magnitude(self):
        llm_response = '{"ticker": "BBCA", "category": "fundamental", "assertion": "naik 3x lipat", "direction": "above", "magnitude": "3x", "confidence": 0.8}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("BBCA naik 3x lipat")
            assert claim.magnitude == 3.0

    @pytest.mark.asyncio
    async def test_parses_verbose_magnitude_string(self):
        llm_response = '{"ticker": "BBCA", "category": "fundamental", "assertion": "naik lebih dari 3x lipat", "direction": "above", "magnitude": "lebih dari 3x lipat", "confidence": 0.8}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("Kami mengestimasikan laba bersih BBCA naik lebih dari 3x lipat pada FY24.")
            assert claim.magnitude == 3.0

    @pytest.mark.asyncio
    async def test_drops_unparseable_magnitude(self):
        llm_response = '{"ticker": "BBCA", "category": "fundamental", "assertion": "naik", "direction": "above", "magnitude": "banyak banget", "confidence": 0.8}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("BBCA naik banyak banget")
            assert claim.magnitude is None

    @pytest.mark.asyncio
    async def test_handles_non_numeric_confidence(self):
        llm_response = '{"ticker": "BBCA", "category": "fundamental", "assertion": "naik", "direction": "above", "confidence": "high"}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("BBCA naik")
            assert claim.confidence == 0.5  # Fallback default

    @pytest.mark.asyncio
    async def test_classifies_insider_trading_en(self):
        llm_response = '{"ticker": "BBCA", "category": "insider_trading", "assertion": "insiders are dumping shares", "assertion_en": "insiders are dumping shares", "direction": "below", "confidence": 0.8}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("BBCA insiders are dumping shares")
            assert claim.category == ClaimCategory.INSIDER_TRADING
            assert claim.ticker == "BBCA"
            assert claim.ticker_valid is True

    @pytest.mark.asyncio
    async def test_classifies_insider_trading_id(self):
        llm_response = '{"ticker": "BMRI", "category": "insider_trading", "assertion": "direktur baru beli saham", "assertion_en": "director just bought shares", "direction": "above", "confidence": 0.8}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("Direktur BMRI baru beli 50rb lembar")
            assert claim.category == ClaimCategory.INSIDER_TRADING
            assert claim.ticker == "BMRI"

    @pytest.mark.asyncio
    async def test_insider_trading_regression_other_categories(self):
        llm_response = '{"ticker": "BBCA", "category": "valuation", "assertion": "PE mahal", "assertion_en": "PE is expensive", "direction": "above", "confidence": 0.8}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("PE BBCA mahal")
            assert claim.category == ClaimCategory.VALUATION

    @pytest.mark.asyncio
    async def test_marks_missing_ticker_as_clarification(self):
        llm_response = '{"ticker": null, "needs_clarification": true, "missing": ["ticker"], "reason_id": "Nilai kode saham?"}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("Saham perbankan lagi mahal nih")
            assert claim.needs_clarification is True
            assert claim.missing == ["ticker"]
            assert claim.ticker == ""
            assert claim.ticker_valid is False

    @pytest.mark.asyncio
    async def test_marks_unknown_ticker_as_clarification(self):
        llm_response = '{"ticker": "UNKNOWN", "category": "valuation", "assertion": "mahal", "direction": "above"}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("Saham mahal")
            assert claim.needs_clarification is True
            assert claim.ticker == "UNKNOWN"
            assert claim.ticker_valid is False

    @pytest.mark.asyncio
    async def test_invalid_format_ticker_triggers_clarification(self):
        llm_response = '{"ticker": "PT_MAJUBERSAMA", "category": "valuation", "assertion": "mahal", "direction": "above"}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("Perusahaan maju bersama mahal")
            assert claim.needs_clarification is True
            assert claim.ticker_valid is False

    @pytest.mark.asyncio
    async def test_non_curated_but_valid_format_not_clarification(self):
        # A valid 4-letter ticker outside the curated list must NOT trigger clarification
        # (existence is checked separately against the full company universe)
        llm_response = '{"ticker": "ACES", "category": "valuation", "assertion": "mahal", "direction": "above"}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("Ace Hardware mahal")
            assert claim.needs_clarification is False
            assert claim.ticker_valid is False  # not in curated list, but format is OK

    @pytest.mark.asyncio
    async def test_valid_ticker_not_clarification(self):
        llm_response = '{"ticker": "BBCA", "category": "fundamental", "assertion": "laba jeblok", "direction": "below", "confidence": 0.8}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("BBCA labanya jeblok")
            assert claim.needs_clarification is False


class TestTickerRecovery:
    """Ticker detection must survive a weak/unusable LLM `ticker` field when
    the narrative itself names a symbol (curated templates always do)."""

    @pytest.mark.asyncio
    async def test_recover_useless_llm_ticker_from_narrative(self):
        # LLM grabbed "PE" (the metric) instead of the actual symbol.
        llm_response = '{"ticker": "PE", "category": "valuation", "assertion": "mahal", "direction": "above", "confidence": 0.8}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("PE BBCA mahal di 25x, jauh di atas rata-rata sektor 18x.")
            assert claim.ticker == "BBCA"
            assert claim.ticker_valid is True
            assert claim.needs_clarification is False
            assert claim.is_policy is False

    @pytest.mark.asyncio
    async def test_recover_null_llm_ticker_from_narrative(self):
        llm_response = '{"ticker": null, "needs_clarification": true, "category": "market", "assertion": "naik", "direction": "above", "confidence": 0.7}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("Harga saham BBCA akan berlipat tahun ini.")
            assert claim.ticker == "BBCA"
            assert claim.needs_clarification is False

    @pytest.mark.asyncio
    async def test_recover_lowercase_ticker_from_narrative(self):
        llm_response = '{"ticker": null, "category": "valuation", "assertion": "mahal", "direction": "above", "confidence": 0.6}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("saham bbca lagi mahal")
            assert claim.ticker == "BBCA"
            assert claim.ticker_valid is True
            assert claim.needs_clarification is False

    @pytest.mark.asyncio
    async def test_spurious_llm_clarification_flag_overridden(self):
        # Model says "needs clarification" but the narrative names a real ticker.
        llm_response = '{"ticker": "UNKNOWN", "needs_clarification": true, "category": "fundamental", "assertion": "laba naik", "direction": "above", "confidence": 0.5}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("Laba BBRI naik tapi sahamnya terus turun 20% bulan ini.")
            assert claim.ticker == "BBRI"
            assert claim.needs_clarification is False

    @pytest.mark.asyncio
    async def test_recover_template_symbols_outside_curated_list(self):
        for narrative in (
            "HBA batu bara ditetapkan naik untuk Q3 — untung ADRO ikut naik.",
            "Larangan ekspor bijih nikel diperketat — INCO untung dari hilirisasi.",
            "Harga CPO turun — laba AALI tertekan.",
            "Penjualan mobil melemah kuartal ini — pendapatan ASII akan merosot.",
        ):
            llm_response = '{"ticker": "UNKNOWN", "category": "market", "assertion": "naik", "direction": "above", "confidence": 0.5}'
            with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
                mock_ollama.return_value = llm_response
                claim = await extract_claim(narrative)
            assert claim.ticker_valid is False  # outside curated list, but format is OK
            assert re.match(r"^[A-Z]{4}$", claim.ticker), claim.ticker
            assert claim.needs_clarification is False

    @pytest.mark.asyncio
    async def test_lowercase_jk_suffix_normalized(self):
        llm_response = '{"ticker": "bbca.jk", "category": "fundamental", "assertion": "naik", "direction": "above", "confidence": 0.6}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("BBCA naik tahun ini")
            assert claim.ticker == "BBCA"

    @pytest.mark.asyncio
    async def test_policy_narrative_without_ticker_still_clarified(self):
        llm_response = '{"ticker": "UNKNOWN", "category": "market", "assertion": "subsidi BBM naik", "direction": "above", "confidence": 0.5}'
        with patch("app.core.llm_client.stream_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = llm_response
            claim = await extract_claim("Subsidi BBM dipangkas — harga BBM bersubsidi naik kuartal ini.")
            assert claim.ticker == "UNKNOWN"
            assert claim.needs_clarification is False  # policy narratives bypass ticker clarif.
            assert claim.is_policy is True
            assert claim.sector == "oil-gas"
