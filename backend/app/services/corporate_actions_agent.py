from datetime import datetime

from app.models.schemas import Claim, CorporateActionEvidence
from app.core.sectors_client import sectors_client
from app.core.evidence_cache import cache

EVENT_TYPE_LABELS = {
    "dividend": "dividend",
    "stock_split": "stock split",
    "rights_issue": "rights issue",
    "bonus": "bonus shares",
    "buyback": "buyback",
    "acquisition": "acquisition",
    "merger": "merger",
}


class CorporateActionsAgent:
    async def analyze(self, claim: Claim) -> CorporateActionEvidence:
        ticker = claim.ticker

        cached = await cache.get(ticker)
        if cached and "corporate_actions" in cached:
            actions_data = cached["corporate_actions"]
            cache_hit = True
        else:
            try:
                actions_data = await sectors_client.get_corporate_actions(ticker)
            except Exception:
                actions_data = {}
            existing = cached or {}
            existing["corporate_actions"] = actions_data
            await cache.set(ticker, existing)
            cache_hit = False

        actions = []
        if isinstance(actions_data, dict):
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
            for key, label in EVENT_TYPE_LABELS.items():
                if key in action_type:
                    relevant_events.append(label)
                    break

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