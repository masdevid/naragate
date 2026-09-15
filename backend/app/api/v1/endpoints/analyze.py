"""Synchronous analyze endpoint.

Non-streaming counterpart to `/api/v1/stream/evaluate`: runs the same pipeline
to completion and returns the finished claim record. This is the single entry
point non-web clients (the MCP server, scripts, harnesses) call, so they share
the exact web-UI pipeline, evidence cache and credit accounting.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.setup import missing_setup_items
from app.services.claims_store import claims_store
from app.services.pipeline import run_pipeline

router = APIRouter()


class AnalyzeInput(BaseModel):
    narrative: str


@router.post("")
async def analyze(input_data: AnalyzeInput):
    missing = missing_setup_items()
    if missing:
        raise HTTPException(
            status_code=409,
            detail={"code": "setup_incomplete", "missing": missing},
        )

    narrative = (input_data.narrative or "").strip()
    if not narrative:
        raise HTTPException(status_code=422, detail="Narrative cannot be empty")

    claim_id: str | None = None
    error: str | None = None
    clarification: str | None = None

    async for event in run_pipeline(narrative):
        data = event.data or {}
        if event.claim_id:
            claim_id = event.claim_id
        if data.get("claim_id"):
            claim_id = data["claim_id"]
        if event.event_type == "pipeline_error":
            error = data.get("error") or "pipeline error"
        elif event.event_type == "clarification_required":
            clarification = data.get("message") or data.get("reason") or "needs clarification"

    state = await claims_store.get_claim(claim_id) if claim_id else None

    if state is None:
        if clarification:
            return {
                "claim_id": claim_id,
                "narrative": narrative,
                "status": "needs_clarification",
                "message": clarification,
            }
        raise HTTPException(
            status_code=502,
            detail={"code": "pipeline_error", "error": error or "pipeline produced no result"},
        )

    state["clarification"] = clarification
    return state
