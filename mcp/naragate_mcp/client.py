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
