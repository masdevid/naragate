import re
from typing import Optional

from app.models.schemas import Claim, ClaimCategory, ClaimDirection
from app.core import llm_client

CURATED_TICKERS = {"BBCA", "BBRI", "BMRI", "TLKM", "UNVR"}

TERM_MAP = {
    "mahal": "valuation premium",
    "murah": "valuation discount",
    "jeblok": "deterioration",
    "anjlok": "negative price change",
    "meroket": "strong growth",
    "meledak": "strong growth",
    "labanya jeblok": "earnings deterioration",
    "untung besar": "strong profitability",
    "rugi": "loss",
    "bangkrut": "bankruptcy",
    "naik": "increase",
    "turun": "decrease",
    "stagnan": "stable",
}

EXTRACTION_PROMPT = """You are a financial claim extractor for Indonesian market narratives.

Extract a structured financial claim from the narrative. Return ONLY a JSON object with these fields:
- ticker: Indonesian stock ticker (4 letters, e.g., BBCA, BBRI, BMRI, TLKM, UNVR)
- category: one of "valuation", "fundamental", "market", "peer_comparison"
- assertion: the core financial claim in Indonesian (Bahasa Indonesia)
- assertion_en: the same claim translated to English
- direction: one of "above", "below", "between", "neutral"
- time_window: optional time period (e.g., "1D", "7D", "30D", "quarterly")
- magnitude: optional numeric qualifier
- confidence: 0-1 confidence in extraction

Indonesian term mappings:
- "mahal" = valuation premium
- "murah" = valuation discount
- "jeblok" = deterioration
- "anjlok" = negative price change
- "meroket" / "meledak" = strong growth
- "labanya jeblok" = earnings deterioration
- "untung besar" = strong profitability

Provide both assertion and assertion_en.
Return ONLY valid JSON, no other text."""


def parse_llm_response(raw: str) -> dict:
    data = llm_client.extract_json(raw)
    if data is None:
        return {
            "ticker": "UNKNOWN",
            "category": "valuation",
            "assertion": raw[:200],
            "direction": "neutral",
            "confidence": 0.1,
        }
    return data


def _parse_magnitude(value) -> Optional[float]:
    """Coerce an LLM magnitude into a float, tolerating strings like '3x', '3x lipat', 'double'."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip().lower().replace(",", ".")
        m = re.search(r"(\d+(?:\.\d+)?)", s)
        if m:
            return float(m.group(1))
        if "double" in s or "dua kali" in s:
            return 2.0
        if "triple" in s or "tiga kali" in s:
            return 3.0
    return None


def _parse_confidence(value) -> float:
    try:
        return min(max(float(value), 0.0), 1.0)
    except (TypeError, ValueError):
        return 0.5


async def extract_claim(
    narrative: str,
    on_token=None,
) -> Claim:
    raw = await llm_client.stream_chat(
        "claim_parser",
        [
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": narrative},
        ],
        response_format={"type": "json_object"},
        on_token=on_token,
    )
    data = parse_llm_response(raw)

    ticker = data.get("ticker", "UNKNOWN").upper().replace(".JK", "")
    ticker_valid = ticker in CURATED_TICKERS

    category_str = data.get("category", "valuation").lower()
    try:
        category = ClaimCategory(category_str)
    except ValueError:
        category = ClaimCategory.VALUATION

    direction_str = data.get("direction", "neutral").lower()
    try:
        direction = ClaimDirection(direction_str)
    except ValueError:
        direction = ClaimDirection.NEUTRAL

    assertion = data.get("assertion") or narrative

    return Claim(
        ticker=ticker,
        category=category,
        assertion=assertion,
        assertion_en=data.get("assertion_en") or assertion,
        direction=direction,
        time_window=data.get("time_window"),
        magnitude=_parse_magnitude(data.get("magnitude")),
        confidence=_parse_confidence(data.get("confidence", 0.5)),
        ticker_valid=ticker_valid,
        narrative_source=narrative,
    )