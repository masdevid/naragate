import pytest
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
