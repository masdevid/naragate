"""Low-level agent tools (parity with `skills/*/tools.yaml`).

These expose the same primitives the web backend's evidence agents use, so a
harness that wants to compose per-agent (like the Pi pipeline) gets identical
building blocks over MCP/REST.

Credit discipline: the `sectors/*` tools are raw, cache-first-at-the-caller
primitives (exactly like the backend agents, which check `evidence-cache` first
and then call these). The `evidence-cache/*` and `llm-complete` tools never call
Sectors at all.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.evidence_cache import cache
from app.core.llm_client import complete
from app.core.sectors_client import sectors_client

router = APIRouter()


def _sections(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    return [s.strip() for s in raw.split(",") if s.strip()]


# ----------------------------------------------------------------- Sectors ---
# Mirror `sectors_*` in tools.yaml. These hit Sectors (credit-recording), like
# the backend evidence agents do on a cache miss.


@router.get("/sectors/company-report")
async def sectors_company_report(ticker: str, sections: str = "valuation,overview,financials"):
    return await sectors_client.get_company_report(ticker.upper(), _sections(sections) or [])


@router.get("/sectors/subsector-report")
async def sectors_subsector_report(sub_sector: str, sections: str | None = None):
    return await sectors_client.get_subsector_report(sub_sector, _sections(sections))


@router.get("/sectors/quarterly-financials")
async def sectors_quarterly_financials(ticker: str, n_quarters: int = 8):
    return await sectors_client.get_quarterly_financials(ticker.upper(), n_quarters)


@router.get("/sectors/daily-transaction")
async def sectors_daily_transaction(ticker: str, start: str | None = None, end: str | None = None):
    return await sectors_client.get_daily_transaction(ticker.upper(), start=start, end=end)


@router.get("/sectors/news")
async def sectors_news(ticker: str, limit: int = 20):
    return await sectors_client.get_news(ticker.upper(), limit=limit)


@router.get("/sectors/corporate-actions")
async def sectors_corporate_actions(ticker: str):
    return await sectors_client.get_corporate_actions(ticker.upper())


@router.get("/sectors/filings")
async def sectors_filings(ticker: str, filing_type: str | None = None):
    return await sectors_client.get_filings(ticker.upper(), filing_type=filing_type)


# ---------------------------------------------------------- Evidence cache ---


class CacheMergeInput(BaseModel):
    ticker: str
    key: str
    value: Any
    ttl: int | None = None


@router.get("/evidence-cache")
async def evidence_cache_get(ticker: str):
    data = await cache.get(ticker.upper())
    return {"ticker": ticker.upper(), "data": data}


@router.post("/evidence-cache")
async def evidence_cache_merge(payload: CacheMergeInput):
    if payload.ttl:
        await cache.merge(payload.ticker.upper(), payload.key, payload.value, ttl=payload.ttl)
    else:
        await cache.merge(payload.ticker.upper(), payload.key, payload.value)
    return {"ticker": payload.ticker.upper(), "key": payload.key, "merged": True}


@router.delete("/evidence-cache")
async def evidence_cache_invalidate(ticker: str):
    await cache.invalidate(ticker.upper())
    return {"ticker": ticker.upper(), "invalidated": True}


# -------------------------------------------------------------------- LLM ----


class LLMCompleteInput(BaseModel):
    prompt: str
    system: str | None = None
    response_format: dict | None = None
    role: str = "default"


@router.post("/llm-complete")
async def llm_complete(payload: LLMCompleteInput):
    if not payload.prompt.strip():
        raise HTTPException(status_code=422, detail="prompt cannot be empty")
    content = await complete(
        payload.prompt,
        system=payload.system,
        response_format=payload.response_format,
        role=payload.role,
    )
    return {"content": content}
