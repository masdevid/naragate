"""API tests for the pre-check endpoint (T1).

The endpoint must never spend Sectors credits on a default GET: a warm cache
serves the report with zero API calls, and a cold cache must answer 503 rather
than fetching wholesale.
"""

import random
from datetime import date, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.services.policy_signal import DAILY_WINDOW_DAYS


def _synthetic_tx(n=260, seed=0, vol=0.01) -> list[dict]:
    rng = random.Random(seed)
    base = date.today() - timedelta(days=DAILY_WINDOW_DAYS)
    price = 1000.0
    out = []
    for i in range(n):
        price = max(10.0, price * (1 + rng.gauss(0, vol)))
        out.append({"date": (base + timedelta(days=i)).isoformat(), "close": round(price, 2), "volume": 1_000_000})
    return out


def _warm_env():
    return {t: {"daily_transaction": _synthetic_tx(seed=i)} for i, t in enumerate(("ADRO", "ITMG", "MEDC", "PGAS", "PTBA"))}


@pytest.mark.asyncio
async def test_warm_run_serves_report_with_zero_api_calls():
    env = _warm_env()
    calls = {"n": 0}

    async def no_fetch(*_a, **_k):
        calls["n"] += 1
        return []

    with patch("app.services.policy_signal.cache.get", AsyncMock(side_effect=lambda t: env.get(t))), \
         patch("app.services.policy_signal.sectors_client.get_daily_transaction", no_fetch):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/precheck/")

    assert resp.status_code == 200
    data = resp.json()
    assert data["verdict"] in ("PASS", "CONDITIONAL", "FAIL")
    assert isinstance(data["beacon_list"], list)
    assert data["window_days"] > 0
    assert len(data["results"]) == 5
    for r in data["results"]:
        assert {
            "ticker", "name", "subsector", "daily_vol", "policy_ratio",
            "on_window_returns", "off_window_returns", "price_regime",
            "policy_signal", "classification", "cache_hit",
        } <= set(r)
        assert r["cache_hit"] is True
    assert len(data["policy_events"]) == 5
    assert all(e["verified"] for e in data["policy_events"])
    assert calls["n"] == 0


@pytest.mark.asyncio
async def test_cold_cache_returns_503_and_never_calls_the_api():
    calls = {"n": 0}

    async def no_fetch(*_a, **_k):
        calls["n"] += 1
        return []

    async def chunk_miss(_ticker, _epoch):
        return None

    with patch("app.services.policy_signal.cache.get", AsyncMock(return_value=None)), \
         patch("app.services.policy_signal.cache.get_daily_chunk", chunk_miss), \
         patch("app.services.policy_signal.sectors_client.get_daily_transaction", no_fetch):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/precheck/")

    assert resp.status_code == 503
    assert resp.json()["detail"]["code"] == "precheck_cache_cold"
    assert calls["n"] == 0


@pytest.mark.asyncio
async def test_refresh_fetches_missing_epochs_and_recovers():
    calls = {"n": 0}
    merges = {"n": 0}
    chunk_writes = {"n": 0}

    async def fake_fetch(_ticker, start=None, end=None):
        calls["n"] += 1
        s = date.fromisoformat(start)
        e = date.fromisoformat(end)
        return [
            {"date": (s + timedelta(days=i)).isoformat(), "close": 1000.0 + i, "volume": 1}
            for i in range((e - s).days + 1)
        ]

    async def chunk_miss(_ticker, _epoch):
        return None

    async def fake_chunk_set(_ticker, _epoch, _rows, ttl=None):
        chunk_writes["n"] += 1

    async def fake_merge(_ticker, _key, _value, ttl=None):
        merges["n"] += 1

    with patch("app.services.policy_signal.cache.get", AsyncMock(return_value=None)), \
         patch("app.services.policy_signal.cache.get_daily_chunk", chunk_miss), \
         patch("app.services.policy_signal.cache.set_daily_chunk", fake_chunk_set), \
         patch("app.services.policy_signal.cache.merge", fake_merge), \
         patch("app.services.policy_signal.sectors_client.get_daily_transaction", fake_fetch):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/precheck/?refresh=true")

    assert resp.status_code == 200
    # 5 candidates × 5 aligned 90-day epochs covering the 12-month window.
    assert calls["n"] == 25
    assert chunk_writes["n"] == 25
    assert merges["n"] == 5
    assert len(resp.json()["results"]) == 5
