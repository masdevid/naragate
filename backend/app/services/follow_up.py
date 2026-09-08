import json

from app.core import llm_client
from app.services.claims_store import claims_store

FOLLOW_UP_PROMPT = """You are Naragate's follow-up assistant. A user just ran a Reality Gap analysis on a market narrative.
Generate 3-5 short follow-up question templates that this specific user would most likely want to ask,
based on the analysis below. The templates are shown as clickable chips in the results page.

Rules:
- Questions must be answerable from the evidence (or from a re-read of the analysis). No data the system cannot provide.
- Anchor each question in a concrete detail of THIS analysis: the score, the verdict, a weak evidence dimension,
  a skeptic note, or the claim itself. Generic questions ("How does this stock perform?") are forbidden.
- Cover diverse angles: at least one about the score/verdict, at least one about the evidence, and one about
  what would change the verdict.
- Match the user's preference profile when given: re-use their preferred question styles and topics.

Claim: {assertion} ({ticker})
Direction: {direction}
Category: {category}
Narrative: {narrative}
Evidence: {evidence}
Score: {score}/100 ({verdict})
Skeptic notes: {skeptic}

User preference profile (recently clicked templates and preferred topics; may be empty):
{preferences}

Return ONLY a JSON object with this exact shape:
{{
  "suggestions": [
    {{"id": "s1", "text": "<question in Indonesian>", "text_en": "<same question in English>"}},
    {{"id": "s2", "text": "<question in Indonesian>", "text_en": "<same question in English>"}}
  ]
}}

Return 3 to 5 suggestions. Return ONLY valid JSON, no other text."""

DEFAULT_SUGGESTIONS = [
    {"id": "d1", "text": "Kenapa skornya setinggi ini?", "text_en": "Why is the score this high?"},
    {"id": "d2", "text": "Apa yang bisa mengubah verdict ini?", "text_en": "What would change this verdict?"},
    {"id": "d3", "text": "Apakah sahamnya wajar?", "text_en": "Is the stock fairly valued?"},
]

MAX_SUGGESTIONS = 5


def _format_preferences(recent: list[dict]) -> str:
    """Format click history into a prompt-ready preference profile."""
    if not recent:
        return "(no history yet — propose diverse questions)"

    lines = ["Recently clicked templates (most recent first):"]
    for i, row in enumerate(recent[:10], 1):
        lines.append(
            f'{i}. "{row["suggestion_text"]}" '
            f'(ticker: {row["ticker"]}, category: {row["category"]}, verdict: {row["verdict"]})'
        )

    for field, label in (
        ("category", "categories"),
        ("verdict", "verdicts"),
        ("ticker", "tickers"),
    ):
        counts = _topic_counts(recent, field)
        if counts:
            summary = ", ".join(f"{value} ({clicks}x)" for value, clicks in counts)
            lines.append(f"Preferred {label}: {summary}")

    return "\n".join(lines)


def _topic_counts(rows: list[dict], field: str) -> list[tuple]:
    counts: dict = {}
    for row in rows:
        value = row.get(field) or "unknown"
        counts[value] = counts.get(value, 0) + 1
    return sorted(counts.items(), key=lambda kv: -kv[1])[:3]


def _build_prompt(claim_state: dict, preferences: str) -> str:
    claim = claim_state.get("claim") or {}
    evidence = claim_state.get("evidence") or {}
    score = claim_state.get("score") or {}
    skeptic = claim_state.get("skeptic") or {}

    evidence_str = json.dumps(evidence, default=str, indent=2)[:2000]
    skeptic_str = json.dumps(skeptic, default=str, indent=2)[:800]

    return FOLLOW_UP_PROMPT.format(
        assertion=claim.get("assertion", ""),
        ticker=claim.get("ticker", ""),
        direction=claim.get("direction", ""),
        category=claim.get("category", ""),
        narrative=claim_state.get("narrative", ""),
        evidence=evidence_str,
        score=score.get("reality_gap_score", "?"),
        verdict=score.get("verdict", "?"),
        skeptic=skeptic_str,
        preferences=preferences,
    )


def _sanitize(raw_suggestions: list) -> list[dict]:
    clean = []
    for i, item in enumerate(raw_suggestions[:MAX_SUGGESTIONS]):
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        text_en = str(item.get("text_en") or "").strip()
        if not text and not text_en:
            continue
        clean.append({
            "id": str(item.get("id") or f"s{i + 1}"),
            "text": text or text_en,
            "text_en": text_en or text,
        })
    return clean


async def generate_suggestions(claim_state: dict) -> list[dict]:
    """Generate contextual follow-up templates for a completed analysis.

    Feeds the user's click history into the prompt so the templates adapt to
    their preference. Falls back to static templates when the LLM fails.
    """
    recent = await claims_store.recent_followup_feedback(limit=20)
    prompt = _build_prompt(claim_state, _format_preferences(recent))

    try:
        raw = await llm_client.stream_chat(
            "follow_up",
            [{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        result = llm_client.extract_json(raw) or {}
        suggestions = _sanitize(result.get("suggestions") or [])
        if len(suggestions) >= 1:
            return suggestions
    except Exception:
        pass
    return DEFAULT_SUGGESTIONS


async def get_suggestions(claim_id: str, claim_state: dict) -> dict:
    """Return cached templates for a claim, generating and caching on first call."""
    cached = claim_state.get("followup_suggestions")
    if cached:
        return {"claim_id": claim_id, "suggestions": cached, "cached": True}

    suggestions = await generate_suggestions(claim_state)
    await claims_store.update_claim(claim_id, {"followup_suggestions": suggestions})
    return {"claim_id": claim_id, "suggestions": suggestions, "cached": False}


async def record_feedback(claim_id: str, claim_state: dict, suggestion: dict) -> bool:
    """Record a clicked template so future recommendations adapt to it."""
    claim = claim_state.get("claim") or {}
    score = claim_state.get("score") or {}
    text = suggestion.get("text") or ""
    if not text:
        return False
    await claims_store.record_followup_feedback(
        claim_id=claim_id,
        ticker=claim.get("ticker", ""),
        category=claim.get("category", ""),
        verdict=score.get("verdict", ""),
        score=float(score.get("reality_gap_score", 0.0) or 0.0),
        suggestion_id=suggestion.get("id", ""),
        suggestion_text=text,
    )
    return True
