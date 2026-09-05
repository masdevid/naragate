import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core import llm_client


class FakeStreamResponse:
    """Minimal stand-in for httpx streaming response."""

    def __init__(self, lines):
        self._lines = lines

    def raise_for_status(self):
        return None

    async def aiter_lines(self):
        for line in self._lines:
            yield line


def make_sse_chunks(*pieces, usage=None):
    lines = []
    for piece in pieces:
        content = json.dumps(piece)
        lines.append(
            f'data: {{"choices": [{{"delta": {{"content": {content}}}, "finish_reason": null}}]}}\n'
        )
    if usage:
        lines.append(f'data: {{"usage": {usage}}}\n')
    lines.append("data: [DONE]\n")
    return lines


def make_mock_client(lines):
    fake_response = FakeStreamResponse(lines)
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.stream.return_value.__aenter__ = AsyncMock(return_value=fake_response)
    mock_client.stream.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_client


class TestExtractJson:
    def test_parses_clean_json(self):
        assert llm_client.extract_json('{"a": 1}') == {"a": 1}

    def test_parses_json_with_leading_text(self):
        raw = 'Here is the result: {"ticker": "BBCA", "category": "valuation"}'
        result = llm_client.extract_json(raw)
        assert result is not None
        assert result["ticker"] == "BBCA"

    def test_parses_code_fenced_json(self):
        raw = '```json\n{"ok": true}\n```'
        assert llm_client.extract_json(raw) == {"ok": True}

    def test_returns_none_for_non_json(self):
        assert llm_client.extract_json("no json here") is None


class TestStreamChatRouting:
    @pytest.mark.asyncio
    async def test_routes_through_pi_agent_when_configured(self):
        lines = make_sse_chunks('{"ticker": "BBCA"}', usage='{"prompt_tokens": 10, "completion_tokens": 5}')
        mock_client = make_mock_client(lines)

        with patch("app.config.settings.settings.PI_AGENT_URL", "http://pi-agent:3000"), \
             patch("httpx.AsyncClient", return_value=mock_client):
            result = await llm_client.stream_chat(
                "claim_parser",
                [{"role": "user", "content": "BBCA mahal banget"}],
            )

        assert result == '{"ticker": "BBCA"}'
        call = mock_client.stream.call_args
        url = call.args[1]
        assert url == "http://pi-agent:3000/v1/agents/claim_parser/complete"
        assert call.kwargs["json"] == {
            "prompt": "BBCA mahal banget",
            "model": llm_client.llm_model("claim_parser"),
        }

    @pytest.mark.asyncio
    async def test_uses_direct_endpoint_when_pi_agent_not_configured(self):
        lines = make_sse_chunks('{"ok": true}')
        mock_client = make_mock_client(lines)

        with patch("app.config.settings.settings.PI_AGENT_URL", ""), \
             patch("httpx.AsyncClient", return_value=mock_client):
            result = await llm_client.stream_chat(
                "claim_parser",
                [{"role": "user", "content": "test"}],
            )

        assert result == '{"ok": true}'
        call = mock_client.stream.call_args
        assert call.args[1].endswith("/chat/completions")
        assert "messages" in call.kwargs["json"]

    @pytest.mark.asyncio
    async def test_streams_tokens_to_callback(self):
        lines = make_sse_chunks('{"a":', " 1}")
        mock_client = make_mock_client(lines)

        tokens = []

        async def on_token(piece):
            tokens.append(piece)

        with patch("app.config.settings.settings.PI_AGENT_URL", "http://pi-agent:3000"), \
             patch("httpx.AsyncClient", return_value=mock_client):
            await llm_client.stream_chat(
                "skeptic",
                [{"role": "user", "content": "analyze"}],
                on_token=on_token,
            )

        assert tokens == ['{"a":', " 1}"]