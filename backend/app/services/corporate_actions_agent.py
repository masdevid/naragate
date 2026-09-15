from datetime import datetime

from app.models.schemas import Claim, CorporateActionEvidence
from app.core.sectors_client import sectors_client
from app.core.evidence_cache import cache
from app.core.usage_tracker import record_sectors_cache_hit

EVENT_TYPE_LABELS = {
    "dividend": "dividend",
    "stock_split": "stock split",
    "rights_issue": "rights issue",
    "bonus": "bonus shares",
    "buyback": "buyback",
    "acquisition": "acquisition",
    "merger": "merger",
    "right_issue": "rights issue",
    "upcoming_dividend": "dividend",
    "warrant": "warrant",
    "agm": "annual general meeting",
}


def _describe_action(category: str, entry: dict) -> str:
    """Build a short human-readable description from a Sectors corporate-action row."""
    if category in ("dividend", "upcoming_dividend"):
        parts = []
        amount = entry.get("dividend_amount")
        if amount is not None:
            parts.append(f"IDR {amount}")
        yield_pct = entry.get("dividend_yield")
        if yield_pct is not None:
            try:
                parts.append(f"yield {float(yield_pct) * 100:.2f}%")
            except (TypeError, ValueError):
                pass
        return "Dividend " + ("· ".join(parts) if parts else "")
    if category == "stock_split" and entry.get("split_ratio") is not None:
        return f"Stock split {entry.get('split_ratio')}"
    if category == "bonus":
        ratio = entry.get("ratio") or entry.get("bonus_ratio")
        return f"Bonus shares {ratio}" if ratio else "Bonus shares"
    if category == "right_issue":
        return "Rights issue"
    if category == "warrant":
        return "Warrant"
    if category == "agm":
        return "Annual general meeting"
    return category.replace("_", " ").title()


class CorporateActionsAgent:
    async def analyze(self, claim: Claim) -> CorporateActionEvidence:
        ticker = claim.ticker

        cached = await cache.get(ticker)
        if cached and "corporate_actions" in cached:
            actions_data = cached["corporate_actions"]
            cache_hit = True
            record_sectors_cache_hit()
        else:
            try:
                actions_data = await sectors_client.get_corporate_actions(ticker)
            except Exception:
                actions_data = {}
            await cache.merge(ticker, "corporate_actions", actions_data)
            cache_hit = False

        actions = []
        if isinstance(actions_data, dict):
            nested = actions_data.get("corporate_actions")
            if isinstance(nested, dict):
                # Real Sectors response: {"corporate_actions": {dividend: [...],
                # stock_split: [...], bonus: [...], right_issue: [...], agm: ...}}
                for category, entries in nested.items():
                    label = EVENT_TYPE_LABELS.get(category, category.replace("_", " "))
                    if not isinstance(entries, list):
                        continue
                    for entry in entries[:10]:
                        if isinstance(entry, dict):
                            actions.append({
                                "type": label,
                                "date": entry.get("ex_date") or entry.get("agm_date")
                                or entry.get("date") or entry.get("payment_date")
                                or entry.get("announcement_date") or "",
                                "description": entry.get("description")
                                or entry.get("title")
                                or _describe_action(category, entry),
                            })
            else:
                items = actions_data.get("data") or actions_data.get("actions") or actions_data.get("items") or []
                if isinstance(items, list):
                    for item in items[:10]:
                        if isinstance(item, dict):
                            actions.append({
                                "type": item.get("type") or item.get("event_type") or "",
                                "date": item.get("date") or item.get("ex_date") or item.get("announcement_date") or "",
                                "description": item.get("description") or item.get("title") or "",
                            })
        elif isinstance(actions_data, list):
            for item in actions_data[:10]:
                if isinstance(item, dict):
                    actions.append({
                        "type": item.get("type") or item.get("event_type") or "",
                        "date": item.get("date") or item.get("ex_date") or item.get("announcement_date") or "",
                        "description": item.get("description") or item.get("title") or "",
                    })

        relevant_events = []
        for action in actions:
            action_type = (action.get("type") or "").lower()
            label = EVENT_TYPE_LABELS.get(action_type, action_type)
            if label and label not in relevant_events:
                relevant_events.append(label)

        if relevant_events:
            summary = (
                f"Terdapat {len(relevant_events)} aksi korporasi relevan: "
                f"{', '.join(dict.fromkeys(relevant_events))}. "
                "Peristiwa ini dapat memengaruhi pergerakan harga dan fundamental."
            )
            summary_en = (
                f"{len(relevant_events)} relevant corporate action(s) found: "
                f"{', '.join(dict.fromkeys(relevant_events))}. "
                "These events may affect price movement and fundamentals."
            )
        else:
            summary = "Tidak ada aksi korporasi relevan yang terdeteksi."
            summary_en = "No relevant corporate actions detected."

        return CorporateActionEvidence(
            claim_ticker=ticker,
            category="corporate_actions",
            actions=actions,
            relevant_events=relevant_events,
            summary=summary,
            summary_en=summary_en,
            evidence_freshness=datetime.now().isoformat(),
            cache_hit=cache_hit,
        )


corporate_actions_agent = CorporateActionsAgent()