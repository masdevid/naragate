"""T4: Policy-event labeling wrapper over the news corpus.

Reads the news corpus that T3 already gathered into the Evidence Graph (per
sector, per member) and emits a thin structured policy-event layer for each
headline that matches anchored Indonesian policy vocabulary (Q20). No new
scraper, no new data source, no Sectors call — the corpus always comes from
`evidence:sector:{sector}`.

Each labeled event is `{date, actor, keyword}` plus the matching headline.
A subsidy narrative with supportive news yields events; unrelated or empty
news yields an empty list — never an exception.
"""

from typing import Optional

# Topic keywords relevant per sector. "*" is the fallback for any sector.
POLICY_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "oil-gas": ["subsidi bbm", "harga bbm", "subsidi", "bbm", "tarif", "minyak", "energi"],
    "coal": ["hba", "dmo", "batu bara", "coal"],
    "utilities": ["tarif listrik", "listrik", "pln"],
    "*": ["subsidi", "harga", "tarif"],
}

# Recognized policy actors, longest phrase first so "kementerian energi"
# wins over "kementerian" and "pemerintah" stays generic.
ACTOR_TERMS: list[tuple[str, str]] = [
    ("kementerian energi", "kementerian esdm"),
    ("esdm", "kementerian esdm"),
    ("bph migas", "bph migas"),
    ("pertamina", "pertamina"),
    ("pemerintah", "pemerintah"),
    ("presiden", "presiden"),
    ("menko", "menko"),
    ("dpr", "dpr"),
]


def label_policy_events(headlines: Optional[list[dict]] = None, sector: Optional[str] = None) -> list[dict]:
    """Label each matching headline into {date, actor, keyword, headline}.

    Returns an empty list when there is nothing to label. Deterministic.
    """
    keywords = POLICY_TOPIC_KEYWORDS.get(sector or "*") or POLICY_TOPIC_KEYWORDS["*"]
    # Longest keyword first so multi-word phrases win over sub-phrases.
    ordered = sorted(keywords, key=len, reverse=True)

    events = []
    for h in headlines or []:
        title = str(h.get("title") or "").lower()
        keyword = next((k for k in ordered if k in title), None)
        if not keyword:
            continue
        actor = None
        for phrase, actor_name in ACTOR_TERMS:
            if phrase in title:
                actor = actor_name
                break
        events.append({
            "date": h.get("date") or "",
            "actor": actor,
            "keyword": keyword,
            "headline": h.get("title") or "",
        })
    return events


def headlines_from_sector_evidence(sector_evidence: Optional[dict]) -> list[dict]:
    """Flatten member news headlines out of the T3 sector aggregate.

    Accepts either serialized dicts (from the graph) or Pydantic models.
    Never raises on partial/missing data.
    """
    headlines: list[dict] = []
    if not sector_evidence:
        return headlines
    by_member = sector_evidence.get("by_member") or {}
    for member, evidence in by_member.items():
        news = evidence.get("news") if isinstance(evidence, dict) else {}
        if isinstance(news, dict) and isinstance(news.get("headlines"), list):
            for h in news["headlines"]:
                if isinstance(h, dict):
                    headlines.append(h)
    return headlines


def extract_policy_events_from_sector(sector_evidence: Optional[dict] = None, sector: Optional[str] = None) -> list[dict]:
    """Label policy events from a T3 sector aggregate (corpus already in-graph)."""
    return label_policy_events(headlines_from_sector_evidence(sector_evidence), sector)