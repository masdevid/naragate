"""T7: Background re-score trigger on policy-event landing.

When a policy-event label lands for a sector (emitted by the pipeline's
`policy_event_labeled` event), any OPEN claim resolved to that sector is
re-scored in the background — no manual re-run — turning the amplifier into a
live policy-risk monitor.

Credit discipline: the re-score is read-only against the Evidence Graph. It
uses `evidence:sector:{sector}` (pure cache read), re-labels policy events
from the in-graph corpus, and gathers price reactions from already-cached
daily transactions (`cached_only=True`). A sector with no cached graph entry is
skipped rather than fetched wholesale — no bulk Sectors calls.
"""

import asyncio
from datetime import datetime
from typing import Optional

from app.core.evidence_cache import cache
from app.models.schemas import Claim, ClaimStatus, SkepticOutput
from app.services.claims_store import claims_store, NON_TERMINAL_STATUSES
from app.services.judge import evidence_judge, score_generator
from app.services.policy_event_agent import extract_policy_events_from_sector
from app.services.policy_reaction import gather_policy_reactions

_GRAPH_KEYS = ("valuation", "fundamental", "market", "news", "corporate_actions", "filings")


def _flatten_member_evidence(sector_evidence: Optional[dict]) -> dict:
    """Promote the first available member's standard evidence keys to top level.

    The sector aggregate stores per-member evidence under `by_member`; the
    judge reads top-level `market`/`news`/`fundamental`/... keys, so we flatten
    best-effort (first member wins) so scoring sees the full evidence picture.
    """
    top: dict = {}
    by_member = (sector_evidence or {}).get("by_member") or {}
    for member, ev in by_member.items():
        if not isinstance(ev, dict):
            continue
        for key in _GRAPH_KEYS:
            if key not in top and ev.get(key):
                top[key] = ev[key]
    return top


class RescoreRegistry:
    """Guards against duplicate concurrent re-scores of the same sector."""

    def __init__(self):
        self._in_flight: set[str] = set()

    def try_schedule(self, sector: str) -> bool:
        if sector in self._in_flight:
            return False
        self._in_flight.add(sector)
        return True

    def done(self, sector: str) -> None:
        self._in_flight.discard(sector)


rescore_registry = RescoreRegistry()


def open_policy_claim_states(sector: str, claims: list[dict]) -> list[dict]:
    """Claims resolved to `sector` that are still open (non-terminal)."""
    return [
        c for c in claims
        if c.get("status") in NON_TERMINAL_STATUSES
        and (c.get("claim") or {}).get("sector") == sector
        and (c.get("claim") or {}).get("is_policy") is True
    ]


async def rescore_claim(claim_state: dict) -> Optional[dict]:
    """Re-score one claim from graph-cached data only. Returns a result dict."""
    claim_id = claim_state.get("claim_id")
    claim_data = claim_state.get("claim")
    if not claim_id or not claim_data:
        return None
    claim = Claim(**claim_data)
    sector = claim.sector
    if not sector:
        return {"claim_id": claim_id, "verdict_changed": False, "skipped": "no_sector"}
    members = claim.sector_members or []

    sector_evidence = await cache.get_sector(sector)
    if not sector_evidence or "members" not in sector_evidence:
        # Credit discipline: no cached graph entry -> skip, never fetch wholesale.
        return {"claim_id": claim_id, "verdict_changed": False, "skipped": "no_cached_sector_evidence"}

    policy_events = extract_policy_events_from_sector(sector_evidence, sector)
    reactions = await gather_policy_reactions(
        members,
        [e["date"] for e in policy_events if e.get("date")],
        cached_only=True,
    )

    evidence = _flatten_member_evidence(sector_evidence)
    evidence["policy"] = {"policy_events": policy_events, "reactions": reactions}

    skeptic = None
    if claim_state.get("skeptic"):
        try:
            skeptic = SkepticOutput(**claim_state["skeptic"])
        except Exception:  # noqa: BLE001 — a malformed skeptic must not block re-scoring
            skeptic = None

    assessment = evidence_judge.assess(claim, evidence, skeptic)
    skeptic_score = skeptic.skepticism_score if skeptic else 50.0
    score = score_generator.compute(assessment, skeptic_score)

    old_verdict = (claim_state.get("score") or {}).get("verdict")
    new_verdict = score.verdict.value
    rescore_at = datetime.now().isoformat()
    history = list(claim_state.get("rescore_history") or [])
    if old_verdict != new_verdict:
        history.append({"at": rescore_at, "from": old_verdict, "to": new_verdict})

    await claims_store.update_claim(claim_id, {
        "assessment": assessment.model_dump(mode="json"),
        "score": score.model_dump(mode="json"),
        "rescore": {
            "at": rescore_at,
            "trigger": "policy_event_label",
            "policy_events": len(policy_events),
            "verdict_changed": old_verdict != new_verdict,
        },
        "rescore_history": history,
    })

    return {
        "claim_id": claim_id,
        "old_verdict": old_verdict,
        "new_verdict": new_verdict,
        "verdict_changed": old_verdict != new_verdict,
    }


async def rescore_sector(sector: str) -> list[dict]:
    """Re-score every open claim resolved to `sector` from cached graph data."""
    claims = await claims_store.list_all_claims()
    results = []
    for state in open_policy_claim_states(sector, claims):
        result = await rescore_claim(state)
        if result:
            results.append(result)
    return results


def schedule_sector_rescore(sector: str) -> bool:
    """Queue a background re-score of `sector`'s open claims (deduped)."""
    if not sector or not rescore_registry.try_schedule(sector):
        return False

    async def _run() -> None:
        try:
            await rescore_sector(sector)
        finally:
            rescore_registry.done(sector)

    asyncio.create_task(_run())
    return True