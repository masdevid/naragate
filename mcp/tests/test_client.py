"""Tests for the Naragate MCP REST client."""

import httpx
import pytest

from naragate_mcp.client import NaragateClient, NaragateError


def _client(handler) -> NaragateClient:
    return NaragateClient(base_url="http://backend.test", transport=httpx.MockTransport(handler))


def test_analyze_posts_narrative():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["body"] = request.content.decode()
        return httpx.Response(200, json={"claim_id": "c1", "status": "completed"})

    result = _client(handler).analyze("PE BBCA mahal")

    assert captured["method"] == "POST"
    assert captured["path"] == "/api/v1/analyze"
    assert "PE BBCA mahal" in captured["body"]
    assert result["status"] == "completed"


def test_precheck_passes_sector_param():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["query"] = request.url.params.get("sector")
        return httpx.Response(200, json={"verdict": "PASS", "sector": "coal"})

    _client(handler).get_precheck(sector="coal")
    assert seen["query"] == "coal"


def test_precheck_without_sector_has_no_query():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["has_query"] = bool(request.url.query)
        return httpx.Response(200, json={"verdict": "FAIL"})

    _client(handler).get_precheck()
    assert seen["has_query"] is False


def test_backend_error_is_wrapped_with_detail():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(409, json={"detail": {"code": "setup_incomplete", "missing": ["llm"]}})

    with pytest.raises(NaragateError) as exc:
        _client(handler).analyze("anything")

    assert exc.value.status == 409
    assert exc.value.detail["code"] == "setup_incomplete"


def test_unreachable_backend_is_wrapped():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    with pytest.raises(NaragateError) as exc:
        _client(handler).get_usage()

    assert "cannot reach Naragate backend" in str(exc.value)


def test_base_url_from_env(monkeypatch):
    monkeypatch.setenv("NARAGATE_BACKEND_URL", "http://remote.test:9000/")
    assert NaragateClient().base_url == "http://remote.test:9000"
