import json

from app.models.schemas import Claim, SkepticOutput
from app.core import llm_client

SKEPTIC_PROMPT = """You are a skeptical financial analyst. Given the following evidence for a claim,
find arguments that would DISPROVE or WEAKEN the claim.

Claim: {assertion} ({ticker})
Category: {category}
Evidence: {evidence}

Identify:
1. What evidence contradicts the claim?
2. What evidence is ambiguous or could be interpreted differently?
3. What missing evidence would change the verdict?
4. Overall skepticism score: 0-100 (higher = stronger counter-argument)

Return ONLY a JSON object with these fields:
- counter_arguments: array of objects with "point" (in Indonesian), "point_en" (in English), "evidence_ref" (string), "strength" (0-100)
- ambiguity_points: array of strings in Indonesian
- ambiguity_points_en: array of strings in English (same points)
- missing_evidence: array of strings in Indonesian
- missing_evidence_en: array of strings in English (same items)
- skepticism_score: 0-100

Provide both the Indonesian and English versions of every text field.
Return ONLY valid JSON, no other text."""


async def run_skeptic(
    claim: Claim,
    evidence: dict,
    on_token=None,
) -> SkepticOutput:
    evidence_str = json.dumps(
        {k: v.model_dump(mode="json") if hasattr(v, "model_dump") else v for k, v in evidence.items()},
        default=str,
        indent=2,
    )

    prompt = SKEPTIC_PROMPT.format(
        assertion=claim.assertion,
        ticker=claim.ticker,
        category=claim.category.value,
        evidence=evidence_str[:2000],
    )

    try:
        raw = await llm_client.stream_chat(
            "skeptic",
            [{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            on_token=on_token,
        )

        result = llm_client.extract_json(raw) or {}
    except Exception:
        result = {
            "counter_arguments": [],
            "ambiguity_points": ["Skeptic analysis failed"],
            "missing_evidence": ["Unable to run skeptic analysis"],
            "skepticism_score": 50.0,
        }

    return SkepticOutput(
        claim_ticker=claim.ticker,
        counter_arguments=result.get("counter_arguments", []),
        ambiguity_points=result.get("ambiguity_points", []),
        ambiguity_points_en=result.get("ambiguity_points_en"),
        missing_evidence=result.get("missing_evidence", []),
        missing_evidence_en=result.get("missing_evidence_en"),
        skepticism_score=float(result.get("skepticism_score", 50.0)),
    )