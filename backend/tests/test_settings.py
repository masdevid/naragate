import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def settings_file(tmp_path, monkeypatch):
    from app.api.v1.endpoints import settings as settings_mod
    from app.core import sectors_config as sc
    target = tmp_path / "runtime_settings.json"
    monkeypatch.setattr(settings_mod, "SETTINGS_FILE", target)
    monkeypatch.setattr(sc, "SETTINGS_FILE", target)
    return target


def _client(headers=None):
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers=headers or {},
    )


def _write(settings_file, data):
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    settings_file.write_text(__import__("json").dumps(data))


class TestSectorsKeyByEmail:
    """The Sectors API key is bound to the session email, not an IP."""

    def _as(self, monkeypatch, email):
        monkeypatch.setattr(
            "app.api.v1.endpoints.settings.email_from_request", lambda request: email
        )

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_set_key(self, settings_file, monkeypatch):
        self._as(monkeypatch, "")
        async with _client() as client:
            r = await client.put("/api/v1/settings", json={"sectors_api_key": "key_a"})
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_authenticated_binds_key_to_email(self, settings_file, monkeypatch):
        self._as(monkeypatch, "a@example.com")
        async with _client() as client:
            r = await client.put("/api/v1/settings", json={"sectors_api_key": "key_a"})
        assert r.status_code == 200
        data = __import__("json").loads(settings_file.read_text())
        assert data["sectors_keys_by_email"]["a@example.com"] == "key_a"
        assert data["sectors_key_owner_email"] == "a@example.com"

    @pytest.mark.asyncio
    async def test_each_email_gets_its_own_key(self, settings_file, monkeypatch):
        self._as(monkeypatch, "a@example.com")
        async with _client() as client:
            await client.put("/api/v1/settings", json={"sectors_api_key": "key_a"})
        self._as(monkeypatch, "b@example.com")
        async with _client() as client:
            await client.put("/api/v1/settings", json={"sectors_api_key": "key_b"})
        data = __import__("json").loads(settings_file.read_text())
        assert data["sectors_keys_by_email"] == {"a@example.com": "key_a", "b@example.com": "key_b"}

    @pytest.mark.asyncio
    async def test_get_exposes_bound_email_and_masks_key(self, settings_file, monkeypatch):
        self._as(monkeypatch, "a@example.com")
        _write(settings_file, {
            "sectors_keys_by_email": {"a@example.com": "key_abcdef123456"},
            "sectors_key_owner_email": "a@example.com",
            "session_secret": "should-not-leak",
        })
        async with _client() as client:
            r = await client.get("/api/v1/settings")
        assert r.status_code == 200
        body = r.json()
        assert body["authenticated"] is True
        assert body["email"] == "a@example.com"
        assert body["sectors_key_owner_email"] == "a@example.com"
        assert "..." in body["sectors_api_key"]
        assert "sectors_keys_by_email" not in body
        assert "session_secret" not in body

    @pytest.mark.asyncio
    async def test_unauthenticated_get_has_no_key(self, settings_file, monkeypatch):
        self._as(monkeypatch, "")
        _write(settings_file, {"sectors_keys_by_email": {"a@example.com": "key_a"}})
        async with _client() as client:
            r = await client.get("/api/v1/settings")
        body = r.json()
        assert body["authenticated"] is False
        assert body["sectors_api_key"] == ""


class TestAgentModelSettings:
    @pytest.mark.asyncio
    async def test_news_and_chat_models_persist(self, settings_file):
        async with _client({"X-Real-IP": "1.2.3.4"}) as client:
            r = await client.put("/api/v1/settings", json={
                "news_model": "news-m", "chat_model": "chat-m",
            })
        assert r.status_code == 200
        data = __import__("json").loads(settings_file.read_text())
        assert data["news_model"] == "news-m"
        assert data["chat_model"] == "chat-m"