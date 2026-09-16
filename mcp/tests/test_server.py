"""Tests for the Naragate MCP server surface.

These run without a live backend (the REST client is faked) and without any
Sectors access. They assert the tool surface, the compact-report shaping, and
that the MCP layer can never spend Sectors credits directly.
"""

from pathlib import Path

import pytest

from naragate_mcp import server
from naragate_mcp.client import NaragateClient, NaragateError

COMPLETED = {
    "claim_id": "c1",
    "narrative": "PE BBCA mahal di 25x",
    "status": "completed",
    "claim": {
        "ticker": "BBCA", "category": "valuation", "direction": "above",
        "assertion": "Harga saham di atas nilai wajar", "is_policy": False, "sector": None,
    },
    "evidence": {"valuation": {"metrics": {"pe": 25}}, "news": {"corroboration": "supports"}},
    "score": {"reality_gap_score": 72, "verdict": "supported", "dimensions": {"valuation_gap": 30}},
    "skeptic": {"skepticism_score": 45, "counter_arguments": [{"point": "x"}], "ambiguity_points": [], "missing_evidence": []},
}


class FakeClient:
    def __init__(self, *_a, **_k):
        pass

    def analyze(self, narrative):
        return dict(COMPLETED, narrative=narrative)

    def get_claim(self, claim_id):
        return dict(COMPLETED, claim_id=claim_id)

    def list_history(self, limit=20):
        return [COMPLETED]

    def get_summary(self):
        return {"total_analyses": 1, "average_score": 72.0, "verdict_distribution": {"supported": 1}, "by_ticker": {}}

    def get_precheck(self, sector=None):
        return {"verdict": "PASS", "sector": sector, "results": [], "policy_events": []}

    def list_templates(self):
        return {"templates": [{"id": "valuation", "narrative": "PE BBCA mahal di 25x", "label": "Valuasi"}]}

    def get_usage(self):
        return {"sectors": {"total_calls": 0, "cached_calls": 10, "remaining": 1600}}

    def whoami(self):
        return {"authenticated": True, "email": "a@example.com", "key_bound": True}

    def get_setup_status(self):
        return {"complete": True, "missing": []}

    def bind_sectors_key(self, api_key):
        return {"status": "ok", "settings": {"sectors_api_key": "key_...3456"}}

    def ask_followup(self, claim_id, question):
        return {"claim_id": claim_id, "answer": f"answer to {question}", "answer_en": "answer"}

    def get_followup_suggestions(self, claim_id):
        return {"claim_id": claim_id, "suggestions": [{"id": "s1", "text": "Kenapa?", "text_en": "Why?"}]}

    def next_followup_suggestion(self, claim_id, exclude=None):
        return {"claim_id": claim_id, "suggestion": {"id": "s9", "text": "Baru?", "text_en": "New?"}}


@pytest.fixture(autouse=True)
def _fake_client(monkeypatch):
    monkeypatch.setattr(server, "NaragateClient", FakeClient)


async def test_tool_surface_is_registered():
    tools = {t.name for t in await server.mcp.list_tools()}
    assert {
        # high-level (credit-safe)
        "analyze_narrative", "analyze_template", "list_templates", "get_claim",
        "get_reality_gap", "list_history", "get_trend_summary", "get_policy_precheck", "get_usage",
        # identity / configuration
        "whoami", "get_setup_status", "bind_sectors_key",
        # follow-up Q&A (web results-page parity)
        "ask_followup", "get_followup_suggestions", "next_followup_suggestion",
        # low-level (tools.yaml parity)
        "sectors_company_report", "sectors_subsector_report", "sectors_quarterly_financials",
        "sectors_daily_transaction", "sectors_news", "sectors_corporate_actions", "sectors_filings",
        "sectors_foreign_flow", "sectors_broker_summary",
        "sectors_top_changes", "sectors_segments", "sectors_index_daily",
        "evidence_cache_get", "evidence_cache_merge", "llm_complete",
    } <= tools


def test_analyze_narrative_returns_compact_report():
    report = server.analyze_narrative("PE BBCA mahal di 25x")
    assert report["reality_gap_score"] == 72
    assert report["verdict"] == "supported"
    assert report["ticker"] == "BBCA"
    assert report["evidence_sections"] == ["valuation", "news"]
    assert report["skeptic"]["counter_arguments"] == 1
    assert report["url"].endswith("/results/c1")


def test_analyze_narrative_surfaces_clarification():
    class Clarify(FakeClient):
        def analyze(self, narrative):
            return {"claim_id": "c2", "narrative": narrative, "status": "needs_clarification", "message": "Mohon berikan kode saham"}

    server.NaragateClient = Clarify
    report = server.analyze_narrative("Saham perbankan sedang mahal.")
    assert report["status"] == "needs_clarification"
    assert "kode saham" in report["clarification"]


def test_analyze_template_unknown_id_lists_available():
    result = server.analyze_template("does-not-exist")
    assert "error" in result
    assert "valuation" in result["available"]


def test_analyze_template_runs_its_narrative():
    report = server.analyze_template("valuation")
    assert report["ticker"] == "BBCA"


def test_policy_precheck_passes_sector_through():
    assert server.get_policy_precheck("coal")["sector"] == "coal"


def test_identity_and_setup_tools():
    assert server.whoami()["email"] == "a@example.com"
    assert server.get_setup_status()["complete"] is True
    assert server.bind_sectors_key("key_abcdef123456")["status"] == "ok"


def test_followup_tools_round_trip():
    assert server.ask_followup("c1", "Kenapa?")["answer"] == "answer to Kenapa?"
    chips = server.get_followup_suggestions("c1")["suggestions"]
    assert chips[0]["id"] == "s1"
    nxt = server.next_followup_suggestion("c1", exclude=["Kenapa?"])["suggestion"]
    assert nxt["id"] == "s9"


def test_claim_resource_reports_errors_as_json():
    class Boom(FakeClient):
        def get_claim(self, claim_id):
            raise NaragateError("not found", status=404)

    server.NaragateClient = Boom
    assert '"error"' in server.claim_resource("missing")


def test_mcp_layer_never_touches_sectors_directly():
    """Credit safety: the MCP bundle must only talk to the Naragate backend."""
    source = Path(server.__file__).read_text(encoding="utf-8")
    assert "sectors.app" not in source
    assert "sectors_client" not in source


def test_embedded_mode_flag_and_env(monkeypatch):
    monkeypatch.delenv("NARAGATE_ENGINE", raising=False)
    assert server._embedded_requested(["--local"]) is True
    assert server._embedded_requested(["--embedded"]) is True
    assert server._embedded_requested([]) is False

    monkeypatch.setenv("NARAGATE_ENGINE", "embedded")
    assert server._embedded_requested([]) is True


def test_client_prefers_embedded_base_url(monkeypatch):
    # The autouse fixture fakes the client; use the real one to inspect base_url.
    monkeypatch.setattr(server, "NaragateClient", NaragateClient)

    monkeypatch.setenv("NARAGATE_BACKEND_URL", "http://remote.test:1")
    monkeypatch.setattr(server, "_BASE_URL", None)
    assert server._client().base_url == "http://remote.test:1"

    monkeypatch.setattr(server, "_BASE_URL", "http://127.0.0.1:9999")
    assert server._client().base_url == "http://127.0.0.1:9999"


def test_embedded_start_errors_helpfully_without_engine(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("app") or name == "uvicorn":
            raise ImportError("not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    from naragate_mcp.local_engine import LocalEngine

    with pytest.raises(RuntimeError, match=r"naragate-mcp\[local\]"):
        LocalEngine().start()
