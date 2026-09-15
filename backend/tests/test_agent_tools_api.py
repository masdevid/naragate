"""API tests for the low-level agent tools (parity with skills/*/tools.yaml).

These wrap Sectors/cache/LLM primitives. Sectors and cache are mocked so tests
never touch the real API, and we assert the Sectors primitives are called
exactly once per request (credit accounting stays predictable).
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_company_report_uppercases_ticker_and_splits_sections():
    fake = SimpleNamespace(get_company_report=AsyncMock(return_value={"symbol": "BBCA"}))

    with patch("app.api.v1.endpoints.agent_tools.sectors_client", fake):
        async with _client() as client:
            resp = await client.get(
                "/api/v1/tools/sectors/company-report",
                params={"ticker": "bbca", "sections": "valuation,overview"},
            )

    assert resp.status_code == 200
    fake.get_company_report.assert_awaited_once_with("BBCA", ["valuation", "overview"])


@pytest.mark.asyncio
async def test_filings_tool_passes_filing_type():
    fake = SimpleNamespace(get_filings=AsyncMock(return_value={"results": []}))

    with patch("app.api.v1.endpoints.agent_tools.sectors_client", fake):
        async with _client() as client:
            resp = await client.get(
                "/api/v1/tools/sectors/filings",
                params={"ticker": "bbri", "filing_type": "buy"},
            )

    assert resp.status_code == 200
    fake.get_filings.assert_awaited_once_with("BBRI", filing_type="buy")


@pytest.mark.asyncio
async def test_news_tool_passes_limit():
    fake = SimpleNamespace(get_news=AsyncMock(return_value={"results": []}))

    with patch("app.api.v1.endpoints.agent_tools.sectors_client", fake):
        async with _client() as client:
            resp = await client.get("/api/v1/tools/sectors/news", params={"ticker": "tlkm", "limit": 5})

    assert resp.status_code == 200
    fake.get_news.assert_awaited_once_with("TLKM", limit=5)


@pytest.mark.asyncio
async def test_evidence_cache_endpoints_never_touch_sectors():
    fake_cache = SimpleNamespace(
        get=AsyncMock(return_value={"valuation": {"metrics": {"pe": 25}}}),
        merge=AsyncMock(),
        invalidate=AsyncMock(),
    )
    fake_sectors = SimpleNamespace(
        get_company_report=AsyncMock(side_effect=AssertionError("sectors must not be called")),
    )

    with patch("app.api.v1.endpoints.agent_tools.cache", fake_cache), \
         patch("app.api.v1.endpoints.agent_tools.sectors_client", fake_sectors):
        async with _client() as client:
            got = await client.get("/api/v1/tools/evidence-cache", params={"ticker": "bbca"})
            merged = await client.post(
                "/api/v1/tools/evidence-cache",
                json={"ticker": "bbca", "key": "valuation", "value": {"metrics": {"pe": 25}}},
            )

    assert got.json()["data"]["valuation"]["metrics"]["pe"] == 25
    assert merged.json()["merged"] is True
    fake_cache.merge.assert_awaited_once()


@pytest.mark.asyncio
async def test_llm_complete_returns_content():
    with patch("app.api.v1.endpoints.agent_tools.complete", AsyncMock(return_value='{"ok": true}')):
        async with _client() as client:
            resp = await client.post(
                "/api/v1/tools/llm-complete",
                json={"prompt": "classify", "response_format": {"type": "json_object"}},
            )

    assert resp.status_code == 200
    assert resp.json()["content"] == '{"ok": true}'


@pytest.mark.asyncio
async def test_llm_complete_rejects_empty_prompt():
    async with _client() as client:
        resp = await client.post("/api/v1/tools/llm-complete", json={"prompt": "   "})

    assert resp.status_code == 422
