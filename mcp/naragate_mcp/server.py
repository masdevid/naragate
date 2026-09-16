"""Naragate MCP server.

Exposes the Naragate reality-gap engine over the Model Context Protocol so the
same skills package works on any MCP-capable harness (Claude Code, Claude
Desktop, Cursor, Windsurf, Zed, VS Code, opencode, Codex, ...).

Design: this server is a thin, credit-safe client over the Naragate backend's
REST API. It never talks to Sectors directly — all evidence gathering, caching
and credit accounting happen in the backend pipeline, so a non-web run costs
exactly the same as a web-UI run (0 additional Sectors calls on a warm cache).
"""

from __future__ import annotations

import argparse
import atexit
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from naragate_mcp.client import NaragateClient, NaragateError
from naragate_mcp.local_engine import LocalEngine

mcp = FastMCP("naragate")

_EVIDENCE_KEYS = ("valuation", "fundamental", "market", "news", "corporate_actions", "filings")

# When embedded (`--local`), the engine runs in-process on `_BASE_URL`; otherwise
# clients fall back to NARAGATE_BACKEND_URL (remote engine).
_BASE_URL: Optional[str] = None
_engine: Optional[LocalEngine] = None


def _client() -> NaragateClient:
    """A client bound to the embedded engine when active, else the remote URL."""
    return NaragateClient(base_url=_BASE_URL) if _BASE_URL else NaragateClient()


def _embedded_requested(argv: Optional[list[str]] = None) -> bool:
    argv = list(sys.argv[1:] if argv is None else argv)
    if any(arg in ("--local", "--embedded") for arg in argv):
        return True
    return os.environ.get("NARAGATE_ENGINE", "").strip().lower() in {
        "local", "embedded", "inproc", "in-process",
    }


def _start_embedded() -> str:
    """Start the in-process engine once and return its base URL."""
    global _BASE_URL, _engine
    if _engine is None:
        _engine = LocalEngine().start()
        _BASE_URL = _engine.base_url
        atexit.register(_engine.stop)
    return _BASE_URL or _engine.base_url


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compact(state: dict[str, Any]) -> dict[str, Any]:
    """Shape a finished claim into a compact, agent-friendly report."""
    claim = state.get("claim") or {}
    score = state.get("score") or {}
    skeptic = state.get("skeptic") or {}
    evidence = state.get("evidence") or {}
    policy = evidence.get("policy") or {}

    return {
        "claim_id": state.get("claim_id"),
        "narrative": state.get("narrative"),
        "status": state.get("status"),
        "clarification": state.get("clarification"),
        "ticker": claim.get("ticker"),
        "category": claim.get("category"),
        "direction": claim.get("direction"),
        "assertion": claim.get("assertion"),
        "is_policy": claim.get("is_policy"),
        "sector": claim.get("sector"),
        "sector_members": claim.get("sector_members"),
        "reality_gap_score": score.get("reality_gap_score"),
        "verdict": score.get("verdict"),
        "explanation": score.get("explanation"),
        "dimensions": score.get("dimensions"),
        "evidence_sections": [k for k in _EVIDENCE_KEYS if evidence.get(k)],
        "policy_events": (policy.get("policy_events") or []) if claim.get("is_policy") else [],
        "skeptic": {
            "score": skeptic.get("skepticism_score"),
            "counter_arguments": len(skeptic.get("counter_arguments") or []),
            "ambiguity_points": len(skeptic.get("ambiguity_points") or []),
            "missing_evidence": len(skeptic.get("missing_evidence") or []),
        },
        "url": f"https://naragate.ilkomers.com/results/{state.get('claim_id')}",
    }


# --------------------------------------------------------------------- tools --

@mcp.tool()
def analyze_narrative(narrative: str) -> dict[str, Any]:
    """Verify an Indonesian market narrative end-to-end and return the Reality Gap report.

    Runs the full Naragate pipeline (claim parsing, evidence, skeptic, judge,
    score) against real Sectors v2 data. Returns the score (0-100), verdict,
    direction, evidence sections, policy signal and skeptic summary.

    Args:
        narrative: the Indonesian market claim to verify, e.g.
            "PE BBCA mahal di 25x, jauh di atas rata-rata sektor 18x."
    """
    state = _client().analyze(narrative)
    if state.get("status") == "needs_clarification":
        return {
            "claim_id": state.get("claim_id"),
            "narrative": state.get("narrative"),
            "status": "needs_clarification",
            "clarification": state.get("message"),
            "hint": "Name a specific 4-letter IDX ticker so the claim can be verified.",
        }
    return _compact(state)


@mcp.tool()
def analyze_template(template_id: str) -> dict[str, Any]:
    """Verify one of the 12 curated demo templates by id (same tiles as the web dashboard).

    Use `list_templates` to discover ids. Example ids: `valuation`, `market`,
    `policy_bbm`, `policy_hba`, `policy_nickel`, `contradiction`, `no_ticker`.
    """
    templates = _client().list_templates().get("templates", [])
    match = next((t for t in templates if t.get("id") == template_id), None)
    if match is None:
        return {"error": f"unknown template_id '{template_id}'", "available": [t["id"] for t in templates]}
    return analyze_narrative(match["narrative"])


@mcp.tool()
def list_templates() -> dict[str, Any]:
    """List the 12 curated demo narratives (the dashboard tiles) so non-web users get the same entry points."""
    return _client().list_templates()


@mcp.tool()
def get_claim(claim_id: str) -> dict[str, Any]:
    """Fetch the full stored record for a claim (claim, evidence, skeptic, score, policy)."""
    return _client().get_claim(claim_id)


@mcp.tool()
def get_reality_gap(claim_id: str) -> dict[str, Any]:
    """Fetch a compact Reality Gap report for a stored claim by id."""
    return _compact(_client().get_claim(claim_id))


@mcp.tool()
def ask_followup(claim_id: str, question: str) -> dict[str, Any]:
    """Ask a follow-up question about a completed analysis.

    Answers are grounded strictly in the stored analysis evidence — the same
    grounded chat the web results page offers.
    """
    return _client().ask_followup(claim_id, question)


@mcp.tool()
def get_followup_suggestions(claim_id: str) -> dict[str, Any]:
    """Get 3-5 contextual follow-up question templates for a completed analysis.

    The same suggestion chips the web results page renders, for non-web
    surfaces that want to offer pickable next questions.
    """
    return _client().get_followup_suggestions(claim_id)


@mcp.tool()
def next_followup_suggestion(claim_id: str, exclude: list[str] | None = None) -> dict[str, Any]:
    """Generate one fresh follow-up template, avoiding the texts in `exclude`.

    Mirrors the web UI's dismiss -> answer -> generate-one-replacement flow.
    """
    return _client().next_followup_suggestion(claim_id, exclude)


@mcp.tool()
def list_history(limit: int = 20) -> dict[str, Any]:
    """List recent analyses, most recent first (the web UI's History page)."""
    claims = _client().list_history(limit=limit)
    rows = [
        {
            "claim_id": c.get("claim_id"),
            "narrative": c.get("narrative"),
            "status": c.get("status"),
            "ticker": (c.get("claim") or {}).get("ticker"),
            "created_at": c.get("created_at"),
            "reality_gap_score": (c.get("score") or {}).get("reality_gap_score"),
            "verdict": (c.get("score") or {}).get("verdict"),
        }
        for c in claims
    ]
    return {"count": len(rows), "claims": rows}


@mcp.tool()
def get_trend_summary() -> dict[str, Any]:
    """Aggregate trends across completed analyses: totals, average score, verdict distribution, per-ticker history."""
    return _client().get_summary()


@mcp.tool()
def get_policy_precheck(sector: str | None = None) -> dict[str, Any]:
    """Policy-to-price pre-check (T1). Scoped to the claim's sector to avoid cross-sector leakage.

    Args:
        sector: optional sector slug, e.g. `oil-gas`, `coal`, `nickel`.
    """
    return _client().get_precheck(sector=sector)


@mcp.tool()
def get_usage() -> dict[str, Any]:
    """Sectors API and LLM credit usage: totals, cache hits, remaining budget, daily breakdown."""
    return _client().get_usage()


@mcp.tool()
def whoami() -> dict[str, Any]:
    """Report which Naragate user this MCP session acts as.

    With `NARAGATE_TOKEN` set, this resolves to the token's email and reports
    whether a Sectors key is bound — so MCP runs use that user's own key, cache
    and credit ledger. Without a token it reports an anonymous/deployment session.
    """
    return _client().whoami()


@mcp.tool()
def get_setup_status() -> dict[str, Any]:
    """Report whether the backend is ready to analyze.

    Returns the missing configuration items (e.g. `sectors_api_key`, `llm_model`)
    so an agent can tell the user exactly what to configure.
    """
    return _client().get_setup_status()


@mcp.tool()
def bind_sectors_key(api_key: str) -> dict[str, Any]:
    """Bind a Sectors v2 API key to this session's user.

    Requires `NARAGATE_TOKEN` (minted in the web UI Settings page) — the key is
    stored server-side against that user's email and never returned by the API.
    """
    return _client().bind_sectors_key(api_key)


# ---------------------------------------------- low-level tools (tools.yaml parity) --
# These mirror skills/*/tools.yaml exactly, for harnesses that want to compose
# per-agent. Credit discipline: check `evidence_cache_get` first, then call the
# `sectors_*` tool on a miss and `evidence_cache_merge` the result.


@mcp.tool()
def sectors_company_report(ticker: str, sections: list[str] | None = None) -> dict[str, Any]:
    """Sectors v2 company report (sections: valuation, overview, financials)."""
    return _client().sectors_company_report(ticker, sections)


@mcp.tool()
def sectors_subsector_report(sub_sector: str, sections: list[str] | None = None) -> dict[str, Any]:
    """Sectors v2 subsector report (sections: statistics, valuation, ...)."""
    return _client().sectors_subsector_report(sub_sector, sections)


@mcp.tool()
def sectors_quarterly_financials(ticker: str, n_quarters: int = 8) -> list[dict[str, Any]]:
    """Sectors v2 quarterly financials (revenue, earnings, margins) for a ticker."""
    return _client().sectors_quarterly_financials(ticker, n_quarters)


@mcp.tool()
def sectors_daily_transaction(ticker: str, start: str | None = None, end: str | None = None) -> list[dict[str, Any]]:
    """Sectors v2 daily transaction data (price, volume, close). Sectors caps a call at 90 days."""
    return _client().sectors_daily_transaction(ticker, start, end)


@mcp.tool()
def sectors_news(ticker: str, limit: int = 20) -> dict[str, Any]:
    """Sectors v2 recent news headlines for a ticker."""
    return _client().sectors_news(ticker, limit)


@mcp.tool()
def sectors_corporate_actions(ticker: str) -> dict[str, Any]:
    """Sectors v2 corporate actions (dividends, splits, warrants) for a ticker."""
    return _client().sectors_corporate_actions(ticker)


@mcp.tool()
def sectors_foreign_flow(ticker: str, start: str | None = None, end: str | None = None) -> Any:
    """Sectors v2 foreign investor flow for a ticker (net inflow/outflow)."""
    return _client().sectors_foreign_flow(ticker, start, end)


@mcp.tool()
def sectors_broker_summary(ticker: str, start: str | None = None, end: str | None = None) -> dict[str, Any]:
    """Sectors v2 broker accumulation/distribution summary for a ticker."""
    return _client().sectors_broker_summary(ticker, start, end)


@mcp.tool()
def sectors_top_changes(classifications: str = "top_gainers", periods: str = "1d", n_stock: int = 5) -> dict[str, Any]:
    """Sectors v2 top gainers/losers across the IDX universe (market-wide)."""
    return _client().sectors_top_changes(classifications, periods, n_stock)


@mcp.tool()
def sectors_segments(ticker: str, financial_year: int | None = None) -> dict[str, Any]:
    """Sectors v2 revenue-segment breakdown for a company."""
    return _client().sectors_segments(ticker, financial_year)


@mcp.tool()
def sectors_index_daily(index_code: str, start: str | None = None, end: str | None = None) -> list[dict[str, Any]]:
    """Sectors v2 daily closing prices for an IDX index (e.g. ihsg)."""
    return _client().sectors_index_daily(index_code, start, end)


@mcp.tool()
def sectors_filings(ticker: str, filing_type: str | None = None) -> dict[str, Any]:
    """Sectors v2 insider-trade filings for a ticker (filing_type: buy, sell, others)."""
    return _client().sectors_filings(ticker, filing_type)


@mcp.tool()
def evidence_cache_get(ticker: str) -> dict[str, Any]:
    """Read the full Evidence Graph for a ticker from the cache (null on miss)."""
    return _client().evidence_cache_get(ticker)


@mcp.tool()
def evidence_cache_merge(ticker: str, key: str, value: Any, ttl: int | None = None) -> dict[str, Any]:
    """Atomically merge one section into the cached Evidence Graph for a ticker."""
    return _client().evidence_cache_merge(ticker, key, value, ttl)


@mcp.tool()
def llm_complete(prompt: str, system: str | None = None,
                 response_format: dict | None = None, role: str = "default") -> dict[str, Any]:
    """Run a one-shot completion on Naragate's configured LLM and return the raw text."""
    return _client().llm_complete(prompt, system, response_format, role)


# ----------------------------------------------------------------- resources --

@mcp.resource("naragate://templates")
def templates_resource() -> str:
    """The 12 curated demo templates as JSON."""
    return json.dumps(_client().list_templates(), ensure_ascii=False, indent=2)


@mcp.resource("naragate://usage")
def usage_resource() -> str:
    """Current Sectors/LLM credit usage as JSON."""
    return json.dumps(_client().get_usage(), ensure_ascii=False, indent=2)


@mcp.resource("naragate://history")
def history_resource() -> str:
    """Recent analyses as JSON."""
    return json.dumps(_client().list_history(limit=20), ensure_ascii=False, indent=2)


@mcp.resource("naragate://claim/{claim_id}")
def claim_resource(claim_id: str) -> str:
    """A stored claim's compact Reality Gap report as JSON."""
    try:
        return json.dumps(_compact(_client().get_claim(claim_id)), ensure_ascii=False, indent=2)
    except NaragateError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


def main() -> None:
    """Entry point for the `naragate-mcp` console script (stdio transport).

    `--local` (or `NARAGATE_ENGINE=embedded`) runs the engine in-process so the
    server needs no external backend; otherwise it calls `NARAGATE_BACKEND_URL`.
    """
    parser = argparse.ArgumentParser(prog="naragate-mcp", description=__doc__)
    parser.add_argument(
        "--local", "--embedded", dest="local", action="store_true",
        help="run the Naragate engine in-process (needs the [local] extra)",
    )
    parser.add_argument("--version", action="version", version="naragate-mcp")
    args = parser.parse_args()

    if args.local or _embedded_requested([]):
        _start_embedded()
    mcp.run()


if __name__ == "__main__":
    main()
