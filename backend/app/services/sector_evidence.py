"""T3: Sector-scoped Evidence Graph population and reuse.

A policy claim resolves to a sector plus a list of member tickers (T2). The
Evidence Graph stores an aggregated, sector-keyed entry so that evidence for a
policy claim is gathered ONCE and reused across every later claim on the same
sector — no new Sectors API calls for repeat policy claims.

Routing is graph-first, preserving the credit-budget discipline:
  1. Check the sector-keyed cache (`evidence:sector:{sector}`).
  2. On a hit, return the cached per-member evidence and count a cache hit.
  3. On a miss, gather evidence per member ticker (through the existing
     per-ticker agents/cache so member tickers also stay fresh), then merge the
     result into the sector key.

`sample_claim_for_member` builds a Claim-shaped object for a member using the
policy claim's category/direction, letting us reuse `get_evidence_for_claim`
verbatim without an LLM.
"""

from datetime import datetime

from app.core.evidence_cache import cache
from app.core.usage_tracker import record_sectors_cache_hit
from app.models.schemas import Claim, ClaimCategory, ClaimDirection
from app.services.evidence_agents import get_evidence_for_claim


def sample_claim_for_member(ticker: str, category: ClaimCategory, direction: ClaimDirection = ClaimDirection.NEUTRAL) -> Claim:
    return Claim(
        ticker=ticker,
        category=category,
        assertion="policy narrative sector analysis",
        assertion_en="Policy narrative sector analysis",
        direction=direction,
        confidence=0.6,
        ticker_valid=True,
    )


async def gather_member_evidence(member: str, category: ClaimCategory) -> dict:
    """Fetch evidence for one member ticker via the normal agent dispatch."""
    return await get_evidence_for_claim(sample_claim_for_member(member, category))


async def get_sector_evidence(sector: str, members: list[str], category: ClaimCategory) -> dict:
    """Return sector-scoped evidence for a policy claim, graph-first.

    On a cache hit returns the cached per-member aggregate. On a miss fetches
    each member (cache-aware), stores the aggregate under the sector key, and
    returns it. `members` may be empty -> returns an empty aggregate (callers
    decide whether that is sufficient evidence; utilities resolve to empty).
    """
    cached = await cache.get_sector(sector)
    if cached and "members" in cached:
        record_sectors_cache_hit()
        return cached

    by_member: dict[str, dict] = {}
    for member in members:
        try:
            by_member[member] = await gather_member_evidence(member, category)
        except Exception:  # noqa: BLE001 — one member failing should not fail the sector
            by_member[member] = {"error": "member evidence fetch failed"}

    aggregate = {
        "sector": sector,
        "members": members,
        "by_member": {k: _serializable(v) for k, v in by_member.items()},
        "fetched_at": datetime.now().isoformat(),
    }
    await cache.set_sector(sector, aggregate)
    return aggregate


def _serializable(value) -> object:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {k: _serializable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serializable(v) for v in value]
    return value
