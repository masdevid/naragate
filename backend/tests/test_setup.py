import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

from app.config.settings import Settings, settings
from app.core.sectors_config import sectors_api_key
from app.core.sectors_client import sectors_client
from app.core.llm_client import stream_chat
from app.main import app, check_sectors


class FakePath:
    def __init__(self, *args):
        pass

    def exists(self):
        return False


class FakeStreamResponse:
    def __init__(self, lines):
        self._lines = lines

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    def raise_for_status(self):
        pass

    async def aiter_lines(self):
        for line in self._lines:
            yield line


class FakeHTTPXClient:
    captured_headers = None

    def __init__(self, *args, **kwargs):
        FakeHTTPXClient.captured_headers = kwargs.get("headers")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    def stream(self, method, url, json=None):
        return FakeStreamResponse(["data: [DONE]"])


class FakeStatusClient:
    def __init__(self, status_code):
        self._status = status_code

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, url, headers=None):
        return SimpleNamespace(status_code=self._status, text="{}")


class TestSettingsResolution:
    def test_settings_resolves_empty_when_no_key(self):
        old = os.environ.get("SECTORS_API_KEY")
        os.environ["SECTORS_API_KEY"] = ""
        try:
            with patch("app.config.settings.Path", FakePath):
                s = Settings()
                assert s.SECTORS_API_KEY == ""
        finally:
            if old is None:
                os.environ.pop("SECTORS_API_KEY", None)
            else:
                os.environ["SECTORS_API_KEY"] = old

    def test_sectors_api_key_prefers_runtime(self):
        with patch("app.core.sectors_config._load_runtime", return_value={"sectors_api_key": "ui_key"}):
            assert sectors_api_key() == "ui_key"

    def test_sectors_api_key_falls_back_to_startup(self):
        with patch("app.core.sectors_config._load_runtime", return_value={}):
            assert sectors_api_key() == settings.SECTORS_API_KEY


class TestSectorsKeyAllowlist:
    """Shared key owned by the first binding IP; owner + allowlist may use it."""

    @staticmethod
    def _runtime(**overrides):
        data = {
            "sectors_api_key": "shared_key",
            "sectors_key_owner_ip": "1.2.3.4",
            "sectors_authorized_ips": ["1.2.3.4", "5.6.7.8"],
        }
        data.update(overrides)
        return data

    def teardown_method(self):
        from app.core.client_ip import set_client_ip
        set_client_ip("")

    def test_owner_ip_gets_key(self):
        from app.core.client_ip import set_client_ip
        set_client_ip("1.2.3.4")
        with patch("app.core.sectors_config._load_runtime", return_value=self._runtime()):
            assert sectors_api_key() == "shared_key"

    def test_authorized_ip_gets_key(self):
        from app.core.client_ip import set_client_ip
        set_client_ip("5.6.7.8")
        with patch("app.core.sectors_config._load_runtime", return_value=self._runtime()):
            assert sectors_api_key() == "shared_key"

    def test_unauthorized_ip_gets_no_key(self):
        from app.core.client_ip import set_client_ip
        set_client_ip("9.9.9.9")
        with patch("app.core.sectors_config._load_runtime", return_value=self._runtime()):
            assert sectors_api_key() == ""

    def test_dev_ip_bypasses_allowlist(self):
        from app.core.client_ip import set_client_ip
        set_client_ip("127.0.0.1")
        with patch("app.core.sectors_config._load_runtime", return_value={"sectors_api_key": "k"}):
            assert sectors_api_key() == "k"

    def test_enforcement_off_shares_legacy_key(self):
        from app.core.client_ip import set_client_ip
        set_client_ip("9.9.9.9")
        with patch("app.core.sectors_config._load_runtime",
                   return_value={"sectors_api_key": "k", "sectors_enforce_per_ip": False}):
            assert sectors_api_key() == "k"


class TestSectorsKeyMigration:
    def test_migrates_legacy_registry_to_allowlist(self):
        from app.core.sectors_config import _migrate_runtime
        data = _migrate_runtime({
            "sectors_keys_by_ip": {"203.0.113.10": "k", "110.139.62.115": "k"},
            "sectors_key_bound_to": "110.139.62.115",
        })
        assert data["sectors_key_owner_ip"] == "110.139.62.115"
        assert set(data["sectors_authorized_ips"]) == {"203.0.113.10", "110.139.62.115"}
        assert data["sectors_api_key"] == "k"
        assert "sectors_keys_by_ip" not in data

    def test_migration_owner_kept_in_allowlist(self):
        from app.core.sectors_config import _migrate_runtime
        data = _migrate_runtime({"sectors_key_owner_ip": "1.2.3.4", "sectors_api_key": "k"})
        assert data["sectors_authorized_ips"] == ["1.2.3.4"]


class TestSectorsClientKey:
    @pytest.mark.asyncio
    async def test_sends_resolved_key_per_request(self):
        with patch("app.core.sectors_client.sectors_api_key", return_value="resolved_key"), \
             patch.object(sectors_client, "client") as mock_client:
            mock_client.get = AsyncMock(return_value=MagicMock(
                raise_for_status=MagicMock(), json=MagicMock(return_value={})))
            await sectors_client._get("/v2/test")
            _, kwargs = mock_client.get.call_args
            assert kwargs["headers"] == {"Authorization": "resolved_key"}


class TestLLMClientAuth:
    @pytest.mark.asyncio
    async def test_sends_auth_header_when_key_set(self):
        with patch("app.core.llm_client.httpx.AsyncClient", FakeHTTPXClient), \
             patch("app.core.llm_client.llm_api_key", return_value="sk-test"):
            await stream_chat("claim_parser", [{"role": "user", "content": "hi"}])
        assert FakeHTTPXClient.captured_headers == {"Authorization": "Bearer sk-test"}

    @pytest.mark.asyncio
    async def test_omits_auth_header_when_key_empty(self):
        with patch("app.core.llm_client.httpx.AsyncClient", FakeHTTPXClient), \
             patch("app.core.llm_client.llm_api_key", return_value=""):
            await stream_chat("claim_parser", [{"role": "user", "content": "hi"}])
        assert FakeHTTPXClient.captured_headers == {}


class TestPerAgentModelResolution:
    def test_role_override_from_runtime(self):
        from app.core.llm_config import llm_model
        runtime = {
            "llm_model": "global-m",
            "news_model": "news-m",
            "chat_model": "chat-m",
        }
        with patch("app.core.llm_config._load_runtime", return_value=runtime):
            assert llm_model("news") == "news-m"
            assert llm_model("chat") == "chat-m"
            assert llm_model("claim_parser") == "global-m"

    def test_role_falls_back_to_global(self):
        from app.core.llm_config import llm_model
        with patch("app.core.llm_config._load_runtime",
                   return_value={"llm_model": "global-m"}):
            assert llm_model("news") == "global-m"
            assert llm_model("chat") == "global-m"


class TestSetupGuard:
    @pytest.mark.asyncio
    async def test_stream_evaluate_returns_409_when_setup_incomplete(self):
        with patch("app.api.v1.endpoints.stream.missing_setup_items",
                   return_value=["sectors_api_key", "llm_model"]):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post("/api/v1/stream/evaluate", json={"narrative": "BBCA mahal"})

        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["code"] == "setup_incomplete"
        assert "sectors_api_key" in data["detail"]["missing"]
        assert "llm_model" in data["detail"]["missing"]

    @pytest.mark.asyncio
    async def test_evaluate_bulk_returns_409_when_setup_incomplete(self):
        with patch("app.api.v1.endpoints.stream.missing_setup_items",
                   return_value=["sectors_api_key"]):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/stream/evaluate-bulk",
                    json={"narratives": ["BBCA mahal", "TLKM murah"]},
                )

        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "setup_incomplete"

    @pytest.mark.asyncio
    async def test_evaluate_bulk_returns_422_when_no_narratives(self):
        with patch("app.api.v1.endpoints.stream.missing_setup_items", return_value=[]):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/stream/evaluate-bulk",
                    json={"narratives": ["   ", ""]},
                )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_evaluate_bulk_streams_progress_events(self):
        from app.services.pipeline import PipelineEvent

        async def fake_run_pipeline(narrative):
            yield PipelineEvent(
                event_type="pipeline_started",
                claim_id="c-1",
                data={"narrative": narrative},
                timestamp="2024-01-01T00:00:00",
            )
            yield PipelineEvent(
                event_type="pipeline_complete",
                claim_id="c-1",
                data={"verdict": "mixed", "score": 55.0},
                timestamp="2024-01-01T00:00:01",
            )

        with patch("app.api.v1.endpoints.stream.missing_setup_items", return_value=[]), \
             patch("app.api.v1.endpoints.stream.run_pipeline", side_effect=fake_run_pipeline):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                async with client.stream(
                    "POST",
                    "/api/v1/stream/evaluate-bulk",
                    json={"narratives": ["BBCA mahal", "TLKM murah"]},
                ) as response:
                    assert response.status_code == 200
                    body = await response.aread()

        text = body.decode()
        assert "bulk_started" in text
        assert '"total": 2' in text
        assert "bulk_item_started" in text
        assert "pipeline_started" in text
        assert "pipeline_complete" in text
        assert "bulk_item_completed" in text
        assert '"status": "completed"' in text
        assert "bulk_complete" in text
        assert '"processed": 2' in text


class TestValidateSectorsEndpoint:
    @pytest.mark.asyncio
    async def test_validate_sectors_ok(self):
        with patch("app.api.v1.endpoints.settings.httpx.AsyncClient", return_value=FakeStatusClient(200)):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post("/api/v1/settings/validate-sectors", json={"api_key": "k"})

        assert response.status_code == 200
        assert response.json()["ok"] is True

    @pytest.mark.asyncio
    async def test_validate_sectors_rejects_bad_key(self):
        with patch("app.api.v1.endpoints.settings.httpx.AsyncClient", return_value=FakeStatusClient(401)):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post("/api/v1/settings/validate-sectors", json={"api_key": "bad"})

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert data["error"]


class TestSettingsStatusEndpoint:
    @pytest.mark.asyncio
    async def test_status_complete(self):
        with patch("app.api.v1.endpoints.settings.missing_setup_items", return_value=[]):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/settings/status")

        assert response.status_code == 200
        assert response.json() == {"complete": True, "missing": []}

    @pytest.mark.asyncio
    async def test_status_incomplete(self):
        with patch("app.api.v1.endpoints.settings.missing_setup_items",
                   return_value=["sectors_api_key"]):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/settings/status")

        assert response.status_code == 200
        assert response.json() == {"complete": False, "missing": ["sectors_api_key"]}


class TestHealthWithRuntimeKeys:
    @pytest.mark.asyncio
    async def test_check_sectors_reports_error_without_key(self):
        with patch("app.main.sectors_api_key", return_value=""):
            result = await check_sectors()
        assert result["status"] == "error"
        assert "No API key configured" in result["error"]

    @pytest.mark.asyncio
    async def test_health_degraded_when_sectors_key_missing(self):
        with patch("app.main.check_ollama", new_callable=AsyncMock) as mock_ollama, \
             patch("app.main.check_sectors", new_callable=AsyncMock) as mock_sectors:
            mock_ollama.return_value = {"status": "ok", "models": []}
            mock_sectors.return_value = {"status": "error", "error": "No API key configured"}

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/health")

        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["sectors_api"]["status"] == "error"