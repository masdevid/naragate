import json
import httpx
from typing import Optional

from app.config.settings import settings
from app.models.schemas import Claim, ClaimCategory, ClaimDirection

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
- assertion: the core financial claim in English
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

The assertion MUST be in English even if the narrative is in Indonesian.
Return ONLY valid JSON, no other text."""


async def call_ollama(prompt: str, user_message: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.OLLAMA_BASE_URL}/chat/completions",
            json={
                "model": settings.claim_parser_model,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_message},
                ],
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


def parse_llm_response(raw: str) -> dict:
    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1])
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "ticker": "UNKNOWN",
            "category": "valuation",
            "assertion": raw[:200],
            "direction": "neutral",
            "confidence": 0.1,
        }


async def extract_claim(narrative: str) -> Claim:
    raw = await call_ollama(EXTRACTION_PROMPT, narrative)
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

    return Claim(
        ticker=ticker,
        category=category,
        assertion=data.get("assertion", narrative),
        direction=direction,
        time_window=data.get("time_window"),
        magnitude=data.get("magnitude"),
        confidence=min(max(float(data.get("confidence", 0.5)), 0.0), 1.0),
        ticker_valid=ticker_valid,
        narrative_source=narrative,
    )
