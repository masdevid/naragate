"""T5: Sector price reaction to a labeled policy event.

Computes a strict timing-disciplined price reaction for each sector member:

- `post_return`: the move over `window_days` trading days strictly AFTER the
  policy date (policy date always precedes the measured move).
- `prior_return`: the move over the same window strictly BEFORE the policy
  date (used to detect run-up drift — "the same names must not move the prior
  period").

The judge consumes these to score the `policy_narrative_gap` dimension; any
member that already drifted in the prior period is excluded there, and if no
clean reaction remains the dimension scores neutral — never a fake signal.
"""

from app.core.evidence_cache import cache
from app.services.policy_signal import (
    POLICY_WINDOW_DAYS, daily_close_series, fetch_daily_transaction
)


def policy_reaction_for_series(series: list[tuple[str, float]], policy_date: str, window_days: int) -> dict | None:
    """Signed reaction around a policy date for an ascending (date, close) series.

    Uses the last trading day on or before `policy_date` as the anchor so the
    measured move is strictly after the announcement. Returns None when the
    window exceeds the available data.
    """
    dates = [d for d, _ in series]
    closes = [c for _, c in series]
    anchor = -1
    for i, d in enumerate(dates):
        if d <= policy_date:
            anchor = i
    if anchor < 0 or anchor - window_days < 0 or anchor + window_days >= len(series):
        return None
    prior = closes[anchor - window_days]
    post_base = closes[anchor]
    post = closes[anchor + window_days]
    if not prior or not post_base or not post:
        return None
    return {
        "post_return": round((post - post_base) / post_base * 100.0, 4),
        "prior_return": round((post_base - prior) / prior * 100.0, 4),
    }


async def gather_policy_reactions(members: list[str], policy_dates: list[str], window_days: int = POLICY_WINDOW_DAYS, cached_only: bool = False) -> list[dict]:
    """Cache-first per-member reaction to the most recent labeled policy event.

    With `cached_only`, only already-graph-cached daily transactions are read —
    no Sectors calls at all (used by the background re-score to preserve credit
    discipline). One member failing never fails the sector; it is skipped.
    """
    if not members or not policy_dates:
        return []
    policy_date = max(policy_dates)
    reactions = []
    for member in members:
        transaction = None
        try:
            if cached_only:
                cached = await cache.get(member)
                transaction = (cached or {}).get("daily_transaction")
                if transaction is None:
                    continue
            else:
                transaction, _hit = await fetch_daily_transaction(member)
            reaction = policy_reaction_for_series(daily_close_series(transaction or []), policy_date, window_days)
            if reaction:
                reaction["ticker"] = member
                reaction["policy_date"] = policy_date
                reactions.append(reaction)
        except Exception:  # noqa: BLE001 — keep gathering the rest of the sector
            continue
    return reactions