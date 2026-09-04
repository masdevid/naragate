import time
import json
from datetime import datetime
from typing import AsyncGenerator

from app.models.schemas import (
    Claim, ClaimStatus, PipelineEvent, RealityGapScore
)
from app.services.claims_store import claims_store
from app.services.claim_parser import extract_claim
from app.services.evidence_agents import get_evidence_for_claim
from app.services.skeptic import run_skeptic
from app.services.judge import evidence_judge, score_generator
from app.core.usage_tracker import record_pipeline


def make_event(event_type: str, claim_id: str, data: dict) -> PipelineEvent:
    return PipelineEvent(
        event_type=event_type,
        claim_id=claim_id,
        data=data,
        timestamp=datetime.now().isoformat(),
    )


async def run_pipeline(narrative: str) -> AsyncGenerator[PipelineEvent, None]:
    start_time = time.time()

    claim_id = await claims_store.create_claim(narrative)
    yield make_event("pipeline_started", claim_id, {"narrative": narrative})

    try:
        yield make_event("claim_parsing", claim_id, {"stage": "claim_parser"})
        claim = await extract_claim(narrative)
        claim.claim_id = claim_id
        await claims_store.update_claim(claim_id, {
            "claim": claim.model_dump(mode="json"),
            "status": ClaimStatus.PARSED.value,
        })
        yield make_event("claim_parsed", claim_id, claim.model_dump(mode="json"))

        yield make_event("evidence_fetching", claim_id, {
            "ticker": claim.ticker,
            "category": claim.category.value,
        })

        evidence = {}
        try:
            evidence = await get_evidence_for_claim(claim)
            await claims_store.update_claim(claim_id, {
                "evidence": {k: v.model_dump(mode="json") if hasattr(v, "model_dump") else v for k, v in evidence.items()},
                "status": ClaimStatus.EVIDENCE_RETRIEVED.value,
            })
        except Exception as e:
            await claims_store.update_claim(claim_id, {"evidence_error": str(e)})

        evidence_data = {}
        for k, v in evidence.items():
            if hasattr(v, "model_dump"):
                evidence_data[k] = v.model_dump(mode="json")
            else:
                evidence_data[k] = v
        yield make_event("evidence_ready", claim_id, evidence_data)

        yield make_event("skeptic_analysis", claim_id, {"stage": "skeptic"})
        skeptic = None
        try:
            skeptic = await run_skeptic(claim, evidence)
            await claims_store.update_claim(claim_id, {
                "skeptic": skeptic.model_dump(mode="json"),
                "status": ClaimStatus.SKEPTIC_REVIEWED.value,
            })
            yield make_event("skeptic_ready", claim_id, skeptic.model_dump(mode="json"))
        except Exception as e:
            yield make_event("skeptic_error", claim_id, {"error": str(e)})

        yield make_event("judge_assessment", claim_id, {"stage": "judge"})
        assessment = evidence_judge.assess(claim, evidence, skeptic)
        await claims_store.update_claim(claim_id, {
            "assessment": assessment.model_dump(mode="json"),
        })
        yield make_event("assessment_ready", claim_id, assessment.model_dump(mode="json"))

        yield make_event("score_computing", claim_id, {"stage": "scorer"})
        skeptic_score = skeptic.skepticism_score if skeptic else 50.0
        score = score_generator.compute(assessment, skeptic_score)
        await claims_store.update_claim(claim_id, {
            "score": score.model_dump(mode="json"),
            "status": ClaimStatus.SCORED.value,
        })
        yield make_event("score_computed", claim_id, score.model_dump(mode="json"))

        duration_ms = int((time.time() - start_time) * 1000)
        await claims_store.update_claim(claim_id, {
            "status": ClaimStatus.COMPLETED.value,
            "duration_ms": duration_ms,
        })
        yield make_event("pipeline_complete", claim_id, {
            "duration_ms": duration_ms,
            "verdict": score.verdict.value,
            "score": score.reality_gap_score,
        })
        record_pipeline(completed=True)

    except Exception as e:
        await claims_store.update_claim(claim_id, {"error": str(e)})
        yield make_event("pipeline_error", claim_id, {"error": str(e)})
        record_pipeline(completed=False)
