"""Thin REST client for the Naragate backend.

Every non-web surface (MCP tools, scripts) goes through the backend so that
evidence caching and credit accounting live in exactly one place. Configure the
backend with `NARAGATE_BACKEND_URL` (default `http://127.0.0.1:5678`).
"""

from __future__ import annotations

import os
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:5678"


class NaragateError(RuntimeError):
    """Raised when the Naragate backend is unreachable or returns an error."""

    def __init__(self, message: str, status: int | None = None, detail: Any = None):
        super().__init__(message)
        self.status = status
        self.detail = detail


class NaragateClient:
    def __init__(self, base_url: str | None = None, timeout: float = 600.0, transport: httpx.BaseTransport | None = None):
        self.base_url = (
            base_url or os.environ.get("NARAGATE_BACKEND_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.timeout = timeout
        self._transport = transport

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout, transport=self._transport) as client:
                resp = client.request(method, url, **kwargs)
        except httpx.HTTPError as exc:  # network / timeout
            raise NaragateError(
                f"cannot reach Naragate backend at {self.base_url}: {exc}"
            ) from exc

        if resp.status_code >= 400:
            detail: Any
            try:
                detail = resp.json().get("detail")
            except Exception:  # noqa: BLE001 — non-JSON error body
                detail = resp.text
            raise NaragateError(
                f"{method} {path} -> HTTP {resp.status_code}: {detail}",
                status=resp.status_code,
                detail=detail,
            )
        return resp.json()

    # ---- high-level, credit-safe operations (all reuse the backend pipeline) ----

    def analyze(self, narrative: str) -> dict[str, Any]:
        return self._request("POST", "/api/v1/analyze", json={"narrative": narrative})

    def get_claim(self, claim_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/claims/{claim_id}")

    def list_history(self, limit: int = 20) -> list[dict[str, Any]]:
        return self._request("GET", "/api/v1/claims/", params={"limit": limit})

    def get_summary(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/claims/summary")

    def get_precheck(self, sector: str | None = None) -> dict[str, Any]:
        params = {"sector": sector} if sector else None
        return self._request("GET", "/api/v1/precheck/", params=params)

    def list_templates(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/templates")

    def get_usage(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/usage")

    # ---- low-level agent tools (parity with skills/*/tools.yaml) ----

    def sectors_company_report(self, ticker: str, sections: list[str] | None = None) -> dict[str, Any]:
        params = {"ticker": ticker, "sections": ",".join(sections)} if sections else {"ticker": ticker}
        return self._request("GET", "/api/v1/tools/sectors/company-report", params=params)

    def sectors_subsector_report(self, sub_sector: str, sections: list[str] | None = None) -> dict[str, Any]:
        params = {"sub_sector": sub_sector}
        if sections:
            params["sections"] = ",".join(sections)
        return self._request("GET", "/api/v1/tools/sectors/subsector-report", params=params)

    def sectors_quarterly_financials(self, ticker: str, n_quarters: int = 8) -> list[dict[str, Any]]:
        return self._request("GET", "/api/v1/tools/sectors/quarterly-financials",
                             params={"ticker": ticker, "n_quarters": n_quarters})

    def sectors_daily_transaction(self, ticker: str, start: str | None = None, end: str | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"ticker": ticker}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        return self._request("GET", "/api/v1/tools/sectors/daily-transaction", params=params)

    def sectors_news(self, ticker: str, limit: int = 20) -> dict[str, Any]:
        return self._request("GET", "/api/v1/tools/sectors/news", params={"ticker": ticker, "limit": limit})

    def sectors_corporate_actions(self, ticker: str) -> dict[str, Any]:
        return self._request("GET", "/api/v1/tools/sectors/corporate-actions", params={"ticker": ticker})

    def sectors_foreign_flow(self, ticker: str, start: str | None = None, end: str | None = None) -> Any:
        params: dict[str, Any] = {"ticker": ticker}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        return self._request("GET", "/api/v1/tools/sectors/foreign-flow", params=params)

    def sectors_broker_summary(self, ticker: str, start: str | None = None, end: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"ticker": ticker}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        return self._request("GET", "/api/v1/tools/sectors/broker-summary", params=params)

    def sectors_top_changes(self, classifications: str = "top_gainers", periods: str = "1d", n_stock: int = 5) -> dict[str, Any]:
        return self._request("GET", "/api/v1/tools/sectors/top-changes", params={
            "classifications": classifications, "periods": periods, "n_stock": n_stock,
        })

    def sectors_segments(self, ticker: str, financial_year: int | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"ticker": ticker}
        if financial_year:
            params["financial_year"] = financial_year
        return self._request("GET", "/api/v1/tools/sectors/segments", params=params)

    def sectors_index_daily(self, index_code: str, start: str | None = None, end: str | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"index_code": index_code}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        return self._request("GET", "/api/v1/tools/sectors/index-daily", params=params)

    def sectors_filings(self, ticker: str, filing_type: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"ticker": ticker}
        if filing_type:
            params["filing_type"] = filing_type
        return self._request("GET", "/api/v1/tools/sectors/filings", params=params)

    def evidence_cache_get(self, ticker: str) -> dict[str, Any]:
        return self._request("GET", "/api/v1/tools/evidence-cache", params={"ticker": ticker})

    def evidence_cache_merge(self, ticker: str, key: str, value: Any, ttl: int | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {"ticker": ticker, "key": key, "value": value}
        if ttl:
            body["ttl"] = ttl
        return self._request("POST", "/api/v1/tools/evidence-cache", json=body)

    def llm_complete(self, prompt: str, system: str | None = None,
                     response_format: dict | None = None, role: str = "default") -> dict[str, Any]:
        body: dict[str, Any] = {"prompt": prompt, "role": role}
        if system:
            body["system"] = system
        if response_format:
            body["response_format"] = response_format
        return self._request("POST", "/api/v1/tools/llm-complete", json=body)
