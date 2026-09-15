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

import json
from datetime import datetime, timezone
from typing import Any

from mcp.server.fastmcp import FastMCP

from naragate_mcp.client import NaragateClient, NaragateError

mcp = FastMCP("naragate")

_EVIDENCE_KEYS = ("valuation", "fundamental", "market", "news", "corporate_actions", "filings")


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
    state = NaragateClient().analyze(narrative)
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
    templates = NaragateClient().list_templates().get("templates", [])
    match = next((t for t in templates if t.get("id") == template_id), None)
    if match is None:
        return {"error": f"unknown template_id '{template_id}'", "available": [t["id"] for t in templates]}
    return analyze_narrative(match["narrative"])


@mcp.tool()
def list_templates() -> dict[str, Any]:
    """List the 12 curated demo narratives (the dashboard tiles) so non-web users get the same entry points."""
    return NaragateClient().list_templates()


@mcp.tool()
def get_claim(claim_id: str) -> dict[str, Any]:
    """Fetch the full stored record for a claim (claim, evidence, skeptic, score, policy)."""
    return NaragateClient().get_claim(claim_id)


@mcp.tool()
def get_reality_gap(claim_id: str) -> dict[str, Any]:
    """Fetch a compact Reality Gap report for a stored claim by id."""
    return _compact(NaragateClient().get_claim(claim_id))


@mcp.tool()
def list_history(limit: int = 20) -> dict[str, Any]:
    """List recent analyses, most recent first (the web UI's History page)."""
    claims = NaragateClient().list_history(limit=limit)
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
    return NaragateClient().get_summary()


@mcp.tool()
def get_policy_precheck(sector: str | None = None) -> dict[str, Any]:
    """Policy-to-price pre-check (T1). Scoped to the claim's sector to avoid cross-sector leakage.

    Args:
        sector: optional sector slug, e.g. `oil-gas`, `coal`, `nickel`.
    """
    return NaragateClient().get_precheck(sector=sector)


@mcp.tool()
def get_usage() -> dict[str, Any]:
    """Sectors API and LLM credit usage: totals, cache hits, remaining budget, daily breakdown."""
    return NaragateClient().get_usage()


# ---------------------------------------------- low-level tools (tools.yaml parity) --
# These mirror skills/*/tools.yaml exactly, for harnesses that want to compose
# per-agent. Credit discipline: check `evidence_cache_get` first, then call the
# `sectors_*` tool on a miss and `evidence_cache_merge` the result.


@mcp.tool()
def sectors_company_report(ticker: str, sections: list[str] | None = None) -> dict[str, Any]:
    """Sectors v2 company report (sections: valuation, overview, financials)."""
    return NaragateClient().sectors_company_report(ticker, sections)


@mcp.tool()
def sectors_subsector_report(sub_sector: str, sections: list[str] | None = None) -> dict[str, Any]:
    """Sectors v2 subsector report (sections: statistics, valuation, ...)."""
    return NaragateClient().sectors_subsector_report(sub_sector, sections)


@mcp.tool()
def sectors_quarterly_financials(ticker: str, n_quarters: int = 8) -> list[dict[str, Any]]:
    """Sectors v2 quarterly financials (revenue, earnings, margins) for a ticker."""
    return NaragateClient().sectors_quarterly_financials(ticker, n_quarters)


@mcp.tool()
def sectors_daily_transaction(ticker: str, start: str | None = None, end: str | None = None) -> list[dict[str, Any]]:
    """Sectors v2 daily transaction data (price, volume, close). Sectors caps a call at 90 days."""
    return NaragateClient().sectors_daily_transaction(ticker, start, end)


@mcp.tool()
def sectors_news(ticker: str, limit: int = 20) -> dict[str, Any]:
    """Sectors v2 recent news headlines for a ticker."""
    return NaragateClient().sectors_news(ticker, limit)


@mcp.tool()
def sectors_corporate_actions(ticker: str) -> dict[str, Any]:
    """Sectors v2 corporate actions (dividends, splits, warrants) for a ticker."""
    return NaragateClient().sectors_corporate_actions(ticker)


@mcp.tool()
def sectors_filings(ticker: str, filing_type: str | None = None) -> dict[str, Any]:
    """Sectors v2 insider-trade filings for a ticker (filing_type: buy, sell, others)."""
    return NaragateClient().sectors_filings(ticker, filing_type)


@mcp.tool()
def evidence_cache_get(ticker: str) -> dict[str, Any]:
    """Read the full Evidence Graph for a ticker from the cache (null on miss)."""
    return NaragateClient().evidence_cache_get(ticker)


@mcp.tool()
def evidence_cache_merge(ticker: str, key: str, value: Any, ttl: int | None = None) -> dict[str, Any]:
    """Atomically merge one section into the cached Evidence Graph for a ticker."""
    return NaragateClient().evidence_cache_merge(ticker, key, value, ttl)


@mcp.tool()
def llm_complete(prompt: str, system: str | None = None,
                 response_format: dict | None = None, role: str = "default") -> dict[str, Any]:
    """Run a one-shot completion on Naragate's configured LLM and return the raw text."""
    return NaragateClient().llm_complete(prompt, system, response_format, role)


# ----------------------------------------------------------------- resources --

@mcp.resource("naragate://templates")
def templates_resource() -> str:
    """The 12 curated demo templates as JSON."""
    return json.dumps(NaragateClient().list_templates(), ensure_ascii=False, indent=2)


@mcp.resource("naragate://usage")
def usage_resource() -> str:
    """Current Sectors/LLM credit usage as JSON."""
    return json.dumps(NaragateClient().get_usage(), ensure_ascii=False, indent=2)


@mcp.resource("naragate://history")
def history_resource() -> str:
    """Recent analyses as JSON."""
    return json.dumps(NaragateClient().list_history(limit=20), ensure_ascii=False, indent=2)


@mcp.resource("naragate://claim/{claim_id}")
def claim_resource(claim_id: str) -> str:
    """A stored claim's compact Reality Gap report as JSON."""
    try:
        return json.dumps(_compact(NaragateClient().get_claim(claim_id)), ensure_ascii=False, indent=2)
    except NaragateError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


def main() -> None:
    """Entry point for the `naragate-mcp` console script (stdio transport)."""
    mcp.run()


if __name__ == "__main__":
    main()
