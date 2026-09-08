import asyncio
import time
import json
from datetime import datetime
from typing import AsyncGenerator, Optional

from app.models.schemas import (
    Claim, ClaimStatus, PipelineEvent, RealityGapScore
)
from app.services.claims_store import claims_store
from app.services.claim_parser import extract_claim
from app.services.evidence_agents import get_evidence_for_claim
from app.services.skeptic import run_skeptic
from app.services.judge import evidence_judge, score_generator
from app.core.usage_tracker import (
    record_pipeline, reset_session_usage, get_session_usage
)
from app.core.sectors_client import sectors_client

_active_narratives: dict[str, str] = {}


async def _find_inflight_claim(narrative: str) -> Optional[dict]:
    """Return an in-flight claim for the same narrative, or None.

    Only a claim actively running in THIS process is treated as in-flight
    (guarded by the in-process registry). A non-terminal claim found in
    storage but absent from the registry was orphaned — a client disconnected
    mid-stream, a worker restarted, or the run crashed. It is marked failed so
    a fresh run can proceed instead of bouncing the user back to a claim page
    that will never finish.
    """
    active_id = _active_narratives.get(narrative)
    if active_id:
        return {"claim_id": active_id, "status": "active"}

    existing = await claims_store.find_active_by_narrative(narrative)
    if existing:
        await claims_store.update_claim(existing["claim_id"], {
            "status": ClaimStatus.FAILED.value,
            "error": "Pipeline was interrupted; superseded by a new run.",
        })
    return None


def make_event(event_type: str, claim_id: str, data: dict) -> PipelineEvent:
    return PipelineEvent(
        event_type=event_type,
        claim_id=claim_id,
        data=data,
        timestamp=datetime.now().isoformat(),
    )


async def _run_agent_with_thinking(claim_id: str, agent: str, coro_factory, result_holder: dict):
    queue: asyncio.Queue = asyncio.Queue()

    async def on_token(piece: str):
        await queue.put(make_event("agent_thinking", claim_id, {"agent": agent, "delta": piece}))

    task = asyncio.create_task(coro_factory(on_token))
    while True:
        while not queue.empty():
            yield queue.get_nowait()
        if task.done():
            break
        await asyncio.sleep(0.02)
    while not queue.empty():
        yield queue.get_nowait()
    result_holder["result"] = task.result()


def _usage_event(claim_id: str) -> PipelineEvent:
    usage = get_session_usage()
    return make_event("usage_update", claim_id, {
        "sectors_calls": usage["sectors"],
        "sectors_cached": usage["sectors_cached"],
        "llm_calls": usage["llm"],
        "llm_input_tokens": usage["llm_input_tokens"],
        "llm_output_tokens": usage["llm_output_tokens"],
    })


async def run_pipeline(narrative: str) -> AsyncGenerator[PipelineEvent, None]:
    start_time = time.time()
    reset_session_usage()

    inflight = await _find_inflight_claim(narrative)
    if inflight:
        yield make_event("pipeline_duplicate", inflight["claim_id"], {
            "claim_id": inflight["claim_id"],
            "narrative": narrative,
            "status": inflight["status"],
        })
        return

    claim_id = await claims_store.create_claim(narrative)
    _active_narratives[narrative] = claim_id
    yield make_event("pipeline_started", claim_id, {"narrative": narrative})

    try:
        yield make_event("claim_parsing", claim_id, {"stage": "claim_parser"})
        claim_holder = {}
        async for event in _run_agent_with_thinking(
            claim_id, "claim_parser",
            lambda on_token: extract_claim(narrative, on_token=on_token),
            claim_holder,
        ):
            yield event
        claim = claim_holder["result"]
        claim.claim_id = claim_id
        await claims_store.update_claim(claim_id, {
            "claim": claim.model_dump(mode="json"),
            "status": ClaimStatus.PARSED.value,
        })
        yield make_event("claim_parsed", claim_id, claim.model_dump(mode="json"))
        yield _usage_event(claim_id)

        if claim.needs_clarification or not sectors_client.validate_ticker(claim.ticker):
            reason_id = getattr(claim, "reason_id", None) or (
                "Nilai narasi ini menyebutkan perusahaan atau kode saham tertentu (mis. BBCA, BBRI, TLKM) agar dapat dianalisis."
            )
            await claims_store.update_claim(claim_id, {
                "status": ClaimStatus.FAILED.value,
                "needs_clarification": True,
                "missing": claim.missing or ["ticker"],
                "reason": claim.reason or "No valid 4-letter ticker identified in the narrative",
                "reason_id": reason_id,
                "error": "Missing ticker — clarification required before analysis.",
            })
            yield make_event("clarification_required", claim_id, {
                "claim_id": claim_id,
                "missing": claim.missing or ["ticker"],
                "reason": claim.reason or "No valid 4-letter ticker identified in the narrative",
                "reason_id": reason_id,
                "message": "Tidak dapat mengidentifikasi kode saham dari narasi. Mohon berikan ticker saham untuk dianalisis.",
            })
            record_pipeline(completed=False)
            return

        if not await sectors_client.validate_ticker_exists(claim.ticker):
            await claims_store.update_claim(claim_id, {
                "status": ClaimStatus.FAILED.value,
                "error": f"Ticker not found: {claim.ticker}. Please check the stock symbol.",
            })
            yield make_event("pipeline_error", claim_id, {
                "error": f"Ticker not found: {claim.ticker}. Please check the stock symbol.",
            })
            record_pipeline(completed=False)
            return

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
        yield _usage_event(claim_id)

        yield make_event("skeptic_analysis", claim_id, {"stage": "skeptic"})
        skeptic = None
        try:
            skeptic_holder = {}
            async for event in _run_agent_with_thinking(
                claim_id, "skeptic",
                lambda on_token: run_skeptic(claim, evidence, on_token=on_token),
                skeptic_holder,
            ):
                yield event
            skeptic = skeptic_holder["result"]
            await claims_store.update_claim(claim_id, {
                "skeptic": skeptic.model_dump(mode="json"),
                "status": ClaimStatus.SKEPTIC_REVIEWED.value,
            })
            yield make_event("skeptic_ready", claim_id, skeptic.model_dump(mode="json"))
        except Exception as e:
            yield make_event("skeptic_error", claim_id, {"error": str(e)})
        yield _usage_event(claim_id)

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
        yield _usage_event(claim_id)

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
        message = str(e) or f"{type(e).__name__}"
        await claims_store.update_claim(claim_id, {
            "error": message,
            "status": ClaimStatus.FAILED.value,
        })
        yield make_event("pipeline_error", claim_id, {"error": message})
        record_pipeline(completed=False)
    except (asyncio.CancelledError, GeneratorExit):
        # Client disconnected mid-stream (tab closed, SSE dropped) or the task
        # was cancelled. This bypasses `except Exception`, so without this the
        # claim would sit at a non-terminal status and look "in progress"
        # forever. Mark it failed so a retry can run a fresh analysis.
        try:
            await claims_store.update_claim(claim_id, {
                "status": ClaimStatus.FAILED.value,
                "error": "Analysis was interrupted before completion.",
            })
        except BaseException:
            pass
        raise
    finally:
        _active_narratives.pop(narrative, None)