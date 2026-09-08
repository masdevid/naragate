import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def settings_file(tmp_path, monkeypatch):
    from app.api.v1.endpoints import settings as settings_mod
    target = tmp_path / "runtime_settings.json"
    monkeypatch.setattr(settings_mod, "SETTINGS_FILE", target)
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


class TestSectorsAuthorizedIps:
    @pytest.mark.asyncio
    async def test_first_binder_becomes_owner(self, settings_file):
        async with _client({"X-Real-IP": "1.2.3.4"}) as client:
            r = await client.put("/api/v1/settings", json={"sectors_api_key": "shared_key"})
        assert r.status_code == 200
        data = __import__("json").loads(settings_file.read_text())
        assert data["sectors_key_owner_ip"] == "1.2.3.4"
        assert data["sectors_authorized_ips"] == ["1.2.3.4"]
        assert data["sectors_api_key"] == "shared_key"

    @pytest.mark.asyncio
    async def test_non_owner_cannot_replace_key(self, settings_file):
        _write(settings_file, {
            "sectors_api_key": "shared_key",
            "sectors_key_owner_ip": "1.2.3.4",
            "sectors_authorized_ips": ["1.2.3.4", "5.6.7.8"],
        })
        async with _client({"X-Real-IP": "5.6.7.8"}) as client:
            r = await client.put("/api/v1/settings", json={"sectors_api_key": "other_key"})
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_owner_adds_ip(self, settings_file):
        _write(settings_file, {
            "sectors_api_key": "shared_key",
            "sectors_key_owner_ip": "1.2.3.4",
            "sectors_authorized_ips": ["1.2.3.4"],
        })
        async with _client({"X-Real-IP": "1.2.3.4"}) as client:
            r = await client.post("/api/v1/settings/sectors-ips", json={"ip": "5.6.7.8", "action": "add"})
        assert r.status_code == 200
        body = r.json()
        assert set(body["sectors_authorized_ips"]) == {"1.2.3.4", "5.6.7.8"}

    @pytest.mark.asyncio
    async def test_non_owner_cannot_add_ip(self, settings_file):
        _write(settings_file, {
            "sectors_api_key": "shared_key",
            "sectors_key_owner_ip": "1.2.3.4",
            "sectors_authorized_ips": ["1.2.3.4", "5.6.7.8"],
        })
        async with _client({"X-Real-IP": "5.6.7.8"}) as client:
            r = await client.post("/api/v1/settings/sectors-ips", json={"ip": "9.9.9.9", "action": "add"})
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_owner_removes_ip_but_not_self(self, settings_file):
        _write(settings_file, {
            "sectors_api_key": "shared_key",
            "sectors_key_owner_ip": "1.2.3.4",
            "sectors_authorized_ips": ["1.2.3.4", "5.6.7.8"],
        })
        async with _client({"X-Real-IP": "1.2.3.4"}) as client:
            r = await client.post("/api/v1/settings/sectors-ips", json={"ip": "5.6.7.8", "action": "remove"})
            assert r.status_code == 200
            assert r.json()["sectors_authorized_ips"] == ["1.2.3.4"]
            r2 = await client.post("/api/v1/settings/sectors-ips", json={"ip": "1.2.3.4", "action": "remove"})
        assert r2.status_code == 400

    @pytest.mark.asyncio
    async def test_get_settings_exposes_allowlist(self, settings_file):
        _write(settings_file, {
            "sectors_api_key": "shared_key",
            "sectors_key_owner_ip": "1.2.3.4",
            "sectors_authorized_ips": ["1.2.3.4", "5.6.7.8"],
        })
        async with _client({"X-Real-IP": "1.2.3.4"}) as client:
            r = await client.get("/api/v1/settings")
        assert r.status_code == 200
        body = r.json()
        assert body["sectors_key_owner_ip"] == "1.2.3.4"
        assert set(body["sectors_authorized_ips"]) == {"1.2.3.4", "5.6.7.8"}
        assert body["sectors_key_is_owner"] is True
        assert body["sectors_key_bound_to"] == "1.2.3.4"

    @pytest.mark.asyncio
    async def test_dev_ip_is_owner_for_management(self, settings_file):
        _write(settings_file, {
            "sectors_api_key": "shared_key",
            "sectors_key_owner_ip": "1.2.3.4",
            "sectors_authorized_ips": ["1.2.3.4"],
        })
        async with _client({"X-Real-IP": "127.0.0.1"}) as client:
            r = await client.post("/api/v1/settings/sectors-ips", json={"ip": "5.6.7.8", "action": "add"})
        assert r.status_code == 200


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