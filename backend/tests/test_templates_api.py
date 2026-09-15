"""Tests for the curated templates endpoint (shared by web and non-web clients)."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.templates import TEMPLATES

EXPECTED_IDS = {
    "valuation", "fundamental", "market", "news",
    "policy_bbm", "policy_hba", "policy_nickel",
    "no_ticker", "contradiction", "future_price", "below_cpo", "below_auto",
}


@pytest.mark.asyncio
async def test_templates_endpoint_returns_the_twelve_curated_narratives():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/templates")

    assert resp.status_code == 200
    templates = resp.json()["templates"]
    assert len(templates) == 12
    assert {t["id"] for t in templates} == EXPECTED_IDS
    for t in templates:
        assert t["narrative"] and t["narrative_en"]
        assert t["label"] and t["label_en"] and t["category"]


def test_templates_module_has_no_duplicate_ids():
    ids = [t["id"] for t in TEMPLATES]
    assert len(ids) == len(set(ids))
