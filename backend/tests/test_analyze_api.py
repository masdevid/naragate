"""Tests for the synchronous /api/v1/analyze endpoint.

This is the shared entry point non-web clients (the MCP server) use, so it must
mirror the streaming pipeline's outcomes exactly: completed, clarification, and
error — all without spending Sectors credits in tests.
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.pipeline import make_event

COMPLETED_STATE = {
    "claim_id": "c1",
    "narrative": "PE BBCA mahal di 25x",
    "status": "completed",
    "claim": {"ticker": "BBCA", "category": "valuation", "is_policy": False},
    "evidence": {"valuation": {}},
    "score": {"reality_gap_score": 72, "verdict": "supported"},
    "skeptic": {"skepticism_score": 45},
}


async def _post(payload):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/api/v1/analyze", json=payload)


@pytest.mark.asyncio
async def test_empty_narrative_is_rejected():
    with patch("app.api.v1.endpoints.analyze.missing_setup_items", return_value=[]):
        resp = await _post({"narrative": "   "})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_setup_incomplete_returns_409():
    with patch("app.api.v1.endpoints.analyze.missing_setup_items", return_value=["sectors_api_key"]):
        resp = await _post({"narrative": "PE BBCA mahal"})
    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "setup_incomplete"


@pytest.mark.asyncio
async def test_completed_run_returns_the_claim_state():
    async def fake_pipeline(narrative):
        yield make_event("pipeline_started", "c1", {"narrative": narrative})
        yield make_event("pipeline_complete", "c1", {"score": 72, "verdict": "supported"})

    with patch("app.api.v1.endpoints.analyze.missing_setup_items", return_value=[]), \
         patch("app.api.v1.endpoints.analyze.run_pipeline", fake_pipeline), \
         patch("app.api.v1.endpoints.analyze.claims_store.get_claim",
               AsyncMock(return_value=dict(COMPLETED_STATE))):
        resp = await _post({"narrative": "PE BBCA mahal di 25x"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "completed"
    assert body["score"]["reality_gap_score"] == 72
    assert body["clarification"] is None


@pytest.mark.asyncio
async def test_clarification_returns_needs_clarification():
    async def fake_pipeline(narrative):
        yield make_event("pipeline_started", "c2", {"narrative": narrative})
        yield make_event("clarification_required", "c2", {
            "message": "Mohon berikan kode saham untuk dianalisis.",
        })

    with patch("app.api.v1.endpoints.analyze.missing_setup_items", return_value=[]), \
         patch("app.api.v1.endpoints.analyze.run_pipeline", fake_pipeline), \
         patch("app.api.v1.endpoints.analyze.claims_store.get_claim", AsyncMock(return_value=None)):
        resp = await _post({"narrative": "Saham perbankan sedang mahal."})

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "needs_clarification"
    assert "kode saham" in body["message"]


@pytest.mark.asyncio
async def test_pipeline_error_without_claim_returns_502():
    async def fake_pipeline(narrative):
        yield make_event("pipeline_started", "c3", {"narrative": narrative})
        yield make_event("pipeline_error", "c3", {"error": "boom"})

    with patch("app.api.v1.endpoints.analyze.missing_setup_items", return_value=[]), \
         patch("app.api.v1.endpoints.analyze.run_pipeline", fake_pipeline), \
         patch("app.api.v1.endpoints.analyze.claims_store.get_claim", AsyncMock(return_value=None)):
        resp = await _post({"narrative": "anything"})

    assert resp.status_code == 502
    assert resp.json()["detail"]["code"] == "pipeline_error"
