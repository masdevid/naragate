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


def test_bearer_token_header_is_sent(monkeypatch):
    monkeypatch.setenv("NARAGATE_TOKEN", "nrg_secret")
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"authenticated": True})

    _client(handler).whoami()
    assert seen["auth"] == "Bearer nrg_secret"


def test_no_bearer_header_without_token(monkeypatch):
    monkeypatch.delenv("NARAGATE_TOKEN", raising=False)
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={})

    _client(handler).get_setup_status()
    assert seen["auth"] is None


def test_identity_and_followup_endpoints():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen[request.url.path] = {"method": request.method, "body": request.content.decode()}
        return httpx.Response(200, json={})

    client = _client(handler)
    client.whoami()
    client.get_setup_status()
    client.bind_sectors_key("key_abcdef123456")
    client.ask_followup("c1", "Kenapa skornya tinggi?")
    client.get_followup_suggestions("c1")
    client.next_followup_suggestion("c1", exclude=["Kenapa?"])

    assert seen["/api/v1/auth/me"]["method"] == "GET"
    assert seen["/api/v1/settings/status"]["method"] == "GET"
    assert seen["/api/v1/settings"]["method"] == "PUT"
    assert "key_abcdef123456" in seen["/api/v1/settings"]["body"]
    assert "Kenapa skornya tinggi?" in seen["/api/v1/claims/c1/chat"]["body"]
    assert seen["/api/v1/claims/c1/suggestions"]["method"] == "GET"
    assert "Kenapa?" in seen["/api/v1/claims/c1/suggestions/next"]["body"]


def test_low_level_sectors_tools_hit_tool_endpoints():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen[request.url.path] = dict(request.url.params)
        return httpx.Response(200, json={})

    client = _client(handler)
    client.sectors_company_report("bbca", ["valuation", "overview"])
    client.sectors_quarterly_financials("tlkm", 4)
    client.sectors_daily_transaction("unvr", "2026-01-01", "2026-03-01")
    client.sectors_filings("bbri", "buy")
    client.sectors_foreign_flow("bbca", "2026-01-01", "2026-03-01")
    client.sectors_broker_summary("tlkm")
    client.sectors_top_changes("top_gainers,top_losers", "1d", 10)
    client.sectors_segments("bbca", 2024)
    client.sectors_index_daily("ihsg", "2026-01-01", "2026-03-01")
    client.evidence_cache_merge("bbca", "valuation", {"metrics": {"pe": 25}})
    client.llm_complete("classify", role="news")

    assert seen["/api/v1/tools/sectors/company-report"] == {"ticker": "bbca", "sections": "valuation,overview"}
    assert seen["/api/v1/tools/sectors/quarterly-financials"] == {"ticker": "tlkm", "n_quarters": "4"}
    assert seen["/api/v1/tools/sectors/daily-transaction"]["start"] == "2026-01-01"
    assert seen["/api/v1/tools/sectors/filings"] == {"ticker": "bbri", "filing_type": "buy"}
    assert seen["/api/v1/tools/sectors/foreign-flow"] == {"ticker": "bbca", "start": "2026-01-01", "end": "2026-03-01"}
    assert seen["/api/v1/tools/sectors/broker-summary"] == {"ticker": "tlkm"}
    assert seen["/api/v1/tools/sectors/top-changes"] == {
        "classifications": "top_gainers,top_losers", "periods": "1d", "n_stock": "10",
    }
    assert seen["/api/v1/tools/sectors/segments"] == {"ticker": "bbca", "financial_year": "2024"}
    assert seen["/api/v1/tools/sectors/index-daily"] == {
        "index_code": "ihsg", "start": "2026-01-01", "end": "2026-03-01",
    }
    assert "/api/v1/tools/evidence-cache" in seen
    assert "/api/v1/tools/llm-complete" in seen
