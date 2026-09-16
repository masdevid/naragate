"""Tests for per-user API tokens (bearer auth for non-web surfaces).

The same email must drive key ownership whether it arrives via the web session
cookie or via an `Authorization: Bearer <token>` header, so MCP runs use the
user's own Sectors key, cache and credit ledger.
"""

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


def _bearer_client(token: str):
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    )


def _fake_login(monkeypatch):
    async def fake(email, password):
        if password != "pw":
            return None
        return {
            "access": "access-token",
            "refresh": "refresh-token",
            "profile": {"email": email, "subscription_tier": "FREE", "credits": 600, "promo_credits": 442},
        }
    monkeypatch.setattr("app.api.v1.endpoints.auth.login_with_password", fake)


async def _login_and_mint(client: AsyncClient, email: str, name: str = "laptop") -> dict:
    await client.post("/api/v1/auth/login", json={"email": email, "password": "pw"})
    r = await client.post("/api/v1/auth/tokens", json={"name": name})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.asyncio
async def test_mint_list_revoke_token(settings_file, monkeypatch):
    _fake_login(monkeypatch)
    async with _client() as client:
        created = await _login_and_mint(client, "a@example.com")

        assert created["token"].startswith("nrg_")
        assert created["id"]
        assert created["email"] == "a@example.com"
        assert created["name"] == "laptop"

        listed = (await client.get("/api/v1/auth/tokens")).json()["tokens"]
        assert len(listed) == 1
        assert listed[0]["id"] == created["id"]
        assert "token" not in listed[0]  # secret never leaves the server again

        revoked = await client.delete(f"/api/v1/auth/tokens/{created['id']}")
        assert revoked.status_code == 200
        assert (await client.get("/api/v1/auth/tokens")).json()["tokens"] == []


@pytest.mark.asyncio
async def test_bearer_token_resolves_email_and_binds_sectors_key(settings_file, monkeypatch):
    _fake_login(monkeypatch)
    async with _client() as session:
        created = await _login_and_mint(session, "a@example.com")
        token = created["token"]

    # A cookie-less client (the MCP case) is the same user via the bearer token.
    async with _bearer_client(token) as client:
        me = (await client.get("/api/v1/auth/me")).json()
        assert me["authenticated"] is True
        assert me["email"] == "a@example.com"

        put = await client.put("/api/v1/settings", json={"sectors_api_key": "key_bearer_123456"})
        assert put.status_code == 200, put.text

        got = (await client.get("/api/v1/settings")).json()
        assert got["sectors_api_key"].endswith("3456")

    data = json.loads(settings_file.read_text())
    assert data["sectors_keys_by_email"]["a@example.com"] == "key_bearer_123456"


@pytest.mark.asyncio
async def test_unknown_bearer_token_is_anonymous(settings_file, monkeypatch):
    _fake_login(monkeypatch)
    async with _bearer_client("nrg_not_a_real_token") as client:
        me = (await client.get("/api/v1/auth/me")).json()
        assert me["authenticated"] is False


@pytest.mark.asyncio
async def test_tokens_require_identity(settings_file):
    async with _client() as client:
        assert (await client.get("/api/v1/auth/tokens")).status_code == 401
        assert (await client.post("/api/v1/auth/tokens", json={})).status_code == 401


@pytest.mark.asyncio
async def test_revoke_is_scoped_to_owner(settings_file, monkeypatch):
    _fake_login(monkeypatch)
    async with _client() as a, _client() as b:
        token_a = await _login_and_mint(a, "a@example.com")
        token_b = await _login_and_mint(b, "b@example.com")

        # B cannot revoke A's token, even with the correct id.
        assert (await b.delete(f"/api/v1/auth/tokens/{token_a['id']}")).status_code == 404
        assert len((await a.get("/api/v1/auth/tokens")).json()["tokens"]) == 1

        assert (await b.delete(f"/api/v1/auth/tokens/{token_b['id']}")).status_code == 200
