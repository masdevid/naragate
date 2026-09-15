"""Tests for email login + session-based Sectors key ownership."""

import json

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def settings_file(tmp_path, monkeypatch):
    from app.api.v1.endpoints import settings as settings_mod
    from app.core import sectors_config as sc
    target = tmp_path / "runtime_settings.json"
    monkeypatch.setattr(settings_mod, "SETTINGS_FILE", target)
    monkeypatch.setattr(sc, "SETTINGS_FILE", target)
    return target


def _client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _fake_login(monkeypatch, *, ok=True):
    async def fake(email, password):
        if not ok or password != "pw":
            return None
        return {
            "access": "access-token",
            "refresh": "refresh-token",
            "profile": {"email": email, "subscription_tier": "FREE", "credits": 600, "promo_credits": 442},
        }
    monkeypatch.setattr("app.api.v1.endpoints.auth.login_with_password", fake)


@pytest.mark.asyncio
async def test_login_sets_session_and_reports_account(settings_file, monkeypatch):
    _fake_login(monkeypatch)
    async with _client() as client:
        r = await client.post("/api/v1/auth/login", json={"email": "A@Example.com", "password": "pw"})
        assert r.status_code == 200
        body = r.json()
        assert body["authenticated"] is True
        assert body["email"] == "a@example.com"
        assert body["subscription_tier"] == "FREE"

        me = await client.get("/api/v1/auth/me")
        assert me.json()["email"] == "a@example.com"

        logged_out = await client.post("/api/v1/auth/logout")
        assert logged_out.json()["authenticated"] is False
        assert (await client.get("/api/v1/auth/me")).json()["authenticated"] is False


@pytest.mark.asyncio
async def test_login_rejects_bad_credentials(settings_file, monkeypatch):
    _fake_login(monkeypatch)
    async with _client() as client:
        r = await client.post("/api/v1/auth/login", json={"email": "x@y.com", "password": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_session_email_binds_sectors_key(settings_file, monkeypatch):
    _fake_login(monkeypatch)
    async with _client() as client:
        await client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": "pw"})
        put = await client.put("/api/v1/settings", json={"sectors_api_key": "key_abcdef123456"})
        assert put.status_code == 200

        data = json.loads(settings_file.read_text())
        assert data["sectors_keys_by_email"]["a@example.com"] == "key_abcdef123456"
        assert data["sectors_key_owner_email"] == "a@example.com"

        got = await client.get("/api/v1/settings")
        assert got.json()["sectors_api_key"].endswith("3456")


@pytest.mark.asyncio
async def test_login_binds_optional_api_key(settings_file, monkeypatch):
    _fake_login(monkeypatch)
    async with _client() as client:
        r = await client.post("/api/v1/auth/login", json={
            "email": "a@example.com", "password": "pw", "api_key": "key_from_login",
        })
    assert r.status_code == 200
    data = json.loads(settings_file.read_text())
    assert data["sectors_keys_by_email"]["a@example.com"] == "key_from_login"


@pytest.mark.asyncio
async def test_login_without_api_key_leaves_it_unbound(settings_file, monkeypatch):
    _fake_login(monkeypatch)
    async with _client() as client:
        await client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": "pw"})
    data = json.loads(settings_file.read_text())
    assert "a@example.com" not in (data.get("sectors_keys_by_email") or {})


@pytest.mark.asyncio
async def test_login_persists_tokens_for_account_usage(settings_file, monkeypatch):
    _fake_login(monkeypatch)
    async with _client() as client:
        await client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": "pw"})
    data = json.loads(settings_file.read_text())
    assert data["sectors_oauth_email"] == "a@example.com"
    assert data["sectors_oauth_access_token"] == "access-token"
    assert data["sectors_oauth_refresh_token"] == "refresh-token"
