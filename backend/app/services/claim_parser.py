import re
from typing import Optional

from app.models.schemas import Claim, ClaimCategory, ClaimDirection
from app.core import llm_client
from app.services.sector_resolver import resolve_sector_from_narrative

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
- category: one of "valuation", "fundamental", "market", "peer_comparison", "insider_trading"
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
- "insider jual saham" = insider selling
- "direktur beli" = director buying
- "komisaris menjual" = commissioner selling
- "pejabat memborong saham" = official accumulating shares

Category guidance:
- "valuation" = claims about PE, PB, PS, premium/discount vs peers
- "fundamental" = claims about revenue, earnings, margins, growth
- "market" = claims about price movement, volume, momentum
- "peer_comparison" = claims comparing two stocks
- "insider_trading" = claims about insider buying/selling, director transactions, commissioner activity

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

    needs_clarification = bool(data.get("needs_clarification"))
    reason = data.get("reason")
    reason_id = data.get("reason_id")
    missing = data.get("missing")

    raw_ticker = data.get("ticker", "UNKNOWN")
    ticker = str(raw_ticker).upper().replace(".JK", "") if raw_ticker else ""
    ticker_valid = ticker in CURATED_TICKERS

    if ticker_valid or re.match(r"^[A-Z]{4}$", ticker):
        sector_resolved = None
    else:
        sector_resolved = resolve_sector_from_narrative(narrative)

    if needs_clarification or not re.match(r"^[A-Z]{4}$", ticker) or ticker == "UNKNOWN":
        if not sector_resolved:
            needs_clarification = True
            if not reason_id:
                reason_id = "Nilai narasi ini menyebutkan perusahaan atau kode saham tertentu (mis. BBCA, BBRI, TLKM) agar dapat dianalisis."
            if not reason:
                reason = "No valid 4-letter ticker identified in the narrative"
            if not missing:
                missing = ["ticker"]

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
        needs_clarification=needs_clarification,
        missing=missing,
        reason=reason,
        reason_id=reason_id,
        is_policy=sector_resolved is not None,
        sector=sector_resolved.sector if sector_resolved else None,
        sector_members=sector_resolved.members if sector_resolved else None,
    )