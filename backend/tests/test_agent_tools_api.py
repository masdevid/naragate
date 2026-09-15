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
async def test_foreign_flow_tool_uppercases_ticker_and_passes_window():
    fake = SimpleNamespace(get_foreign_flow=AsyncMock(return_value=[]))

    with patch("app.api.v1.endpoints.agent_tools.sectors_client", fake):
        async with _client() as client:
            resp = await client.get(
                "/api/v1/tools/sectors/foreign-flow",
                params={"ticker": "bbca", "start": "2026-01-01", "end": "2026-03-01"},
            )

    assert resp.status_code == 200
    fake.get_foreign_flow.assert_awaited_once_with("BBCA", start="2026-01-01", end="2026-03-01")


@pytest.mark.asyncio
async def test_broker_summary_tool_uppercases_ticker():
    fake = SimpleNamespace(get_broker_summary=AsyncMock(return_value={"results": []}))

    with patch("app.api.v1.endpoints.agent_tools.sectors_client", fake):
        async with _client() as client:
            resp = await client.get("/api/v1/tools/sectors/broker-summary", params={"ticker": "tlkm"})

    assert resp.status_code == 200
    fake.get_broker_summary.assert_awaited_once_with("TLKM", start=None, end=None)


@pytest.mark.asyncio
async def test_top_changes_tool_passes_classification_and_period():
    fake = SimpleNamespace(get_top_changes=AsyncMock(return_value={}))

    with patch("app.api.v1.endpoints.agent_tools.sectors_client", fake):
        async with _client() as client:
            resp = await client.get(
                "/api/v1/tools/sectors/top-changes",
                params={"classifications": "top_gainers,top_losers", "periods": "1d", "n_stock": 10},
            )

    assert resp.status_code == 200
    fake.get_top_changes.assert_awaited_once_with("top_gainers,top_losers", "1d", 10)


@pytest.mark.asyncio
async def test_segments_tool_uppercases_ticker_and_passes_year():
    fake = SimpleNamespace(get_segments=AsyncMock(return_value={}))

    with patch("app.api.v1.endpoints.agent_tools.sectors_client", fake):
        async with _client() as client:
            resp = await client.get(
                "/api/v1/tools/sectors/segments",
                params={"ticker": "bbca", "financial_year": 2024},
            )

    assert resp.status_code == 200
    fake.get_segments.assert_awaited_once_with("BBCA", 2024)


@pytest.mark.asyncio
async def test_index_daily_tool_passes_index_and_window():
    fake = SimpleNamespace(get_index_daily=AsyncMock(return_value=[]))

    with patch("app.api.v1.endpoints.agent_tools.sectors_client", fake):
        async with _client() as client:
            resp = await client.get(
                "/api/v1/tools/sectors/index-daily",
                params={"index_code": "ihsg", "start": "2026-01-01", "end": "2026-03-01"},
            )

    assert resp.status_code == 200
    fake.get_index_daily.assert_awaited_once_with("ihsg", start="2026-01-01", end="2026-03-01")


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
