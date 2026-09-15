"""Tests for the Naragate MCP server surface.

These run without a live backend (the REST client is faked) and without any
Sectors access. They assert the tool surface, the compact-report shaping, and
that the MCP layer can never spend Sectors credits directly.
"""

from pathlib import Path

import pytest

from naragate_mcp import server
from naragate_mcp.client import NaragateError

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


@pytest.fixture(autouse=True)
def _fake_client(monkeypatch):
    monkeypatch.setattr(server, "NaragateClient", FakeClient)


async def test_tool_surface_is_registered():
    tools = {t.name for t in await server.mcp.list_tools()}
    assert {
        "analyze_narrative", "analyze_template", "list_templates", "get_claim",
        "get_reality_gap", "list_history", "get_trend_summary", "get_policy_precheck", "get_usage",
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
