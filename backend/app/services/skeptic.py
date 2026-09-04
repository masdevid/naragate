import json
import httpx

from app.config.settings import settings
from app.models.schemas import Claim, SkepticOutput
from app.core.usage_tracker import record_llm_call

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
- counter_arguments: array of objects with "point" (string), "evidence_ref" (string), "strength" (0-100)
- ambiguity_points: array of strings
- missing_evidence: array of strings
- skepticism_score: 0-100

Return ONLY valid JSON, no other text."""


async def run_skeptic(claim: Claim, evidence: dict) -> SkepticOutput:
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
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/chat/completions",
                json={
                    "model": settings.skeptic_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
            data = response.json()
            raw = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            if input_tokens or output_tokens:
                record_llm_call(settings.skeptic_model, input_tokens, output_tokens)

            cleaned = raw.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1])

            result = json.loads(cleaned)
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
        missing_evidence=result.get("missing_evidence", []),
        skepticism_score=float(result.get("skepticism_score", 50.0)),
    )
