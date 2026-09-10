"""T2: Deterministic sector resolver for ticker-less policy narratives.

An anchored keyword map translates Indonesian policy vocabulary into a sector
slug and a list of member tickers. The function `resolve_sector_from_narrative`
is pure, deterministic, and requires no LLM — the same text always yields the
same resolution. Policy narratives that mention a known keyword are admitted
to the pipeline; their members are the evidence scope for T3+.

The anchored map is ordered longest-keyword-first so that multi-word policy
phrases win over single words (e.g., "subsidi bbm" beats "bbm"). Only exact
substring matches in a lowercased narrative are considered.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SectorResolution:
    sector: str
    members: list[str]
    keyword_matched: str
    source: str = "anchored"


# Anchored keyword map: (keyword, sector_slug, member_tickers)
# Longest keyword first so first-match-wins favors specificity.
_POLICY_SECTOR_MAP: list[tuple[str, str, list[str]]] = [
    ("subsidi bbm", "oil-gas", ["PGAS", "MEDC"]),
    ("tarif listrik", "utilities", []),
    ("harga bbm", "oil-gas", ["PGAS", "MEDC"]),
    ("batu bara", "coal", ["ADRO", "ITMG", "PTBA"]),
    ("hba", "coal", ["ADRO", "ITMG", "PTBA"]),
    ("bbm", "oil-gas", ["PGAS", "MEDC"]),
    ("pertamina", "oil-gas", ["PGAS", "MEDC"]),
    ("minyak", "oil-gas", ["MEDC"]),
    ("energi", "oil-gas", ["PGAS", "MEDC"]),
    ("coal", "coal", ["ADRO", "ITMG", "PTBA"]),
    ("listrik", "utilities", []),
]

ALL_POLICY_KEYWORDS: frozenset[str] = frozenset(kw for kw, *_ in _POLICY_SECTOR_MAP)


def resolve_sector_from_narrative(text: str) -> Optional[SectorResolution]:
    """Return the best-matching SectorResolution for a policy narrative, or None.

    Deterministic: same text always yields the same output. Longest-keyword-first
    ordering guarantees multi-word policy phrases (e.g., "subsidi bbm") win over
    their sub-phrases.
    """
    lower = text.lower()
    for keyword, sector, members in _POLICY_SECTOR_MAP:
        if keyword in lower:
            return SectorResolution(sector=sector, members=list(members), keyword_matched=keyword)
    return None
