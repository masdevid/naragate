"""Tests for the Sectors account-usage service.

No real network: an httpx.MockTransport stands in for api.sectors.app, and the
in-process cache is reset per test. We assert request counts so polling stays
cheap and credit-safe.
"""

import base64
import json
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from httpx import ASGITransport

from app.core import sectors_account
from app.main import app


def _jwt(claims: dict) -> str:
    def part(d: dict) -> str:
        raw = json.dumps(d).encode()
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")
    return f"{part({'alg': 'HS256', 'typ': 'JWT'})}.{part(claims)}.sig"


def _future(seconds: int = 3600) -> int:
    return int(time.time()) + seconds


USAGE_BODY = {
    "current": {
        "success": {"2026-09-14 09:47:24 +0000": 10, "2026-09-15 09:47:24 +0000": 5},
        "error": {"2026-09-14 09:47:24 +0000": 2},
    },
    "previous": {"success": {}, "error": {}},
    "credits": 600,
    "credits_expire_at": "2027-03-04T00:00:00Z",
    "promo_credits": 442,
    "promo_credits_expire_at": "2026-09-30T16:59:59Z",
    "promo_label": "Sectors Hackathon 2026",
}

PROFILE_BODY = {
    "id": 6915,
    "email": "devid.wahid@gmail.com",
    "subscription_tier": "FREE",
    "credits": 600,
    "credits_expire_at": "2027-03-04T00:00:00+00:00",
    "promo_credits": 442,
    "promo_credits_expire_at": "2026-09-30T16:59:59+00:00",
    "promo_label": "Sectors Hackathon 2026",
}


@pytest.fixture(autouse=True)
def _reset():
    sectors_account.reset_cache()
    yield
    sectors_account.reset_cache()


def _settings(**kw) -> SimpleNamespace:
    base = dict(
        SECTORS_OAUTH_ACCESS_TOKEN="",
        SECTORS_OAUTH_CLIENT_ID="",
        SECTORS_OAUTH_CLIENT_SECRET="",
        SECTORS_OAUTH_REFRESH_TOKEN="",
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _client(handler, calls: list) -> httpx.AsyncClient:
    def wrapped(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url.path))
        return handler(request)
    return httpx.AsyncClient(transport=httpx.MockTransport(wrapped))


@pytest.mark.asyncio
async def test_no_token_is_not_configured(monkeypatch):
    monkeypatch.setattr(sectors_account, "settings", _settings())
    snapshot = await sectors_account.fetch_account_snapshot()
    assert snapshot["configured"] is False
    assert snapshot["ok"] is False


@pytest.mark.asyncio
async def test_fetches_profile_and_usage_with_bearer(monkeypatch):
    token = _jwt({"user_id": 6915, "exp": _future()})
    monkeypatch.setattr(sectors_account, "settings", _settings(SECTORS_OAUTH_ACCESS_TOKEN=token))
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == f"Bearer {token}"
        if request.url.path == "/auth/users/6915/":
            return httpx.Response(200, json=PROFILE_BODY)
        if request.url.path == "/api/usage/":
            return httpx.Response(200, json=USAGE_BODY)
        return httpx.Response(404, json={})

    snapshot = await sectors_account.fetch_account_snapshot(_client(handler, calls))

    assert snapshot["ok"] is True
    assert snapshot["email"] == "devid.wahid@gmail.com"
    assert snapshot["credits"] == 600
    assert snapshot["promo_credits"] == 442
    assert snapshot["promo_label"] == "Sectors Hackathon 2026"
    assert snapshot["period"]["success"] == 15  # 10 + 5
    assert snapshot["period"]["error"] == 2
    assert calls == ["/auth/users/6915/", "/api/usage/"]


@pytest.mark.asyncio
async def test_snapshot_is_cached(monkeypatch):
    token = _jwt({"user_id": 6915, "exp": _future()})
    monkeypatch.setattr(sectors_account, "settings", _settings(SECTORS_OAUTH_ACCESS_TOKEN=token))
    calls: list[str] = []
    handler = lambda r: httpx.Response(200, json=PROFILE_BODY if "users" in r.url.path else USAGE_BODY)

    await sectors_account.fetch_account_snapshot(_client(handler, calls))
    await sectors_account.fetch_account_snapshot(_client(handler, calls))  # served from cache

    assert len(calls) == 2  # profile + usage, once


@pytest.mark.asyncio
async def test_usage_error_degrades(monkeypatch):
    token = _jwt({"user_id": 6915, "exp": _future()})
    monkeypatch.setattr(sectors_account, "settings", _settings(SECTORS_OAUTH_ACCESS_TOKEN=token))
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/users/6915/":
            return httpx.Response(200, json=PROFILE_BODY)
        return httpx.Response(403, json={"detail": "no"})

    snapshot = await sectors_account.fetch_account_snapshot(_client(handler, calls))

    assert snapshot["ok"] is False
    assert "403" in snapshot["error"]


@pytest.mark.asyncio
async def test_expired_token_without_refresh_is_unavailable(monkeypatch):
    token = _jwt({"user_id": 6915, "exp": _future(-3600)})
    monkeypatch.setattr(sectors_account, "settings", _settings(SECTORS_OAUTH_ACCESS_TOKEN=token))
    calls: list[str] = []

    snapshot = await sectors_account.fetch_account_snapshot(_client(lambda r: httpx.Response(200), calls))

    assert snapshot["configured"] is True
    assert snapshot["ok"] is False
    assert calls == []  # no request without a valid token


@pytest.mark.asyncio
async def test_usage_endpoint_fetches_and_records_account(monkeypatch):
    snapshot = {"configured": True, "ok": True, "credits": 600, "period": {"success": 1, "error": 0}}
    fake_fetch = AsyncMock(return_value=snapshot)
    recorded: dict = {}
    monkeypatch.setattr("app.api.v1.endpoints.usage.fetch_account_snapshot", fake_fetch)
    monkeypatch.setattr("app.api.v1.endpoints.usage.record_account_snapshot", lambda s: recorded.update(s))

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/usage")

    assert resp.status_code == 200
    fake_fetch.assert_awaited_once()
    assert recorded["credits"] == 600
    assert "sectors_account" in resp.json()


@pytest.mark.asyncio
async def test_refresh_token_exchanges_when_access_expired(monkeypatch):
    monkeypatch.setattr(sectors_account, "settings", _settings(
        SECTORS_OAUTH_ACCESS_TOKEN=_jwt({"user_id": 6915, "exp": _future(-10)}),
        SECTORS_OAUTH_CLIENT_ID="client-abc",
        SECTORS_OAUTH_REFRESH_TOKEN="refresh-xyz",
    ))
    calls: list[str] = []
    new_token = _jwt({"user_id": 6915, "exp": _future()})

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth/token/":
            return httpx.Response(200, json={"access_token": new_token})
        if request.url.path == "/auth/users/6915/":
            return httpx.Response(200, json=PROFILE_BODY)
        if request.url.path == "/api/usage/":
            return httpx.Response(200, json=USAGE_BODY)
        return httpx.Response(404, json={})

    snapshot = await sectors_account.fetch_account_snapshot(_client(handler, calls))

    assert snapshot["ok"] is True
    assert calls[0] == "/oauth/token/"
    assert "/api/usage/" in calls
