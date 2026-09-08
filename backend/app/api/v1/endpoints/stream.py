import json
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.core.client_ip import resolve_client_ip, set_client_ip
from app.core.setup import missing_setup_items
from app.services.pipeline import run_pipeline

router = APIRouter()


class NarrativeInput(BaseModel):
    narrative: str


class BulkNarrativeInput(BaseModel):
    narratives: list[str]


def _guard(request: Request):
    set_client_ip(resolve_client_ip(request))


@router.post("/evaluate")
async def evaluate_narrative(request: Request, input_data: NarrativeInput):
    _guard(request)
    missing = missing_setup_items()
    if missing:
        raise HTTPException(
            status_code=409,
            detail={"code": "setup_incomplete", "missing": missing},
        )

    async def event_generator():
        set_client_ip(resolve_client_ip(request))
        async for event in run_pipeline(input_data.narrative):
            yield {
                "event": event.event_type,
                "data": json.dumps(event.model_dump(mode="json")),
            }

    return EventSourceResponse(event_generator())


@router.post("/evaluate-bulk")
async def evaluate_bulk(request: Request, input_data: BulkNarrativeInput):
    _guard(request)
    missing = missing_setup_items()
    if missing:
        raise HTTPException(
            status_code=409,
            detail={"code": "setup_incomplete", "missing": missing},
        )

    narratives = [n.strip() for n in input_data.narratives if n.strip()]
    if not narratives:
        raise HTTPException(status_code=422, detail="No narratives provided")

    async def event_generator():
        set_client_ip(resolve_client_ip(request))
        yield {
            "event": "bulk_started",
            "data": json.dumps({"total": len(narratives)}),
        }

        processed = 0
        failed = 0
        for index, narrative in enumerate(narratives):
            yield {
                "event": "bulk_item_started",
                "data": json.dumps({
                    "index": index,
                    "total": len(narratives),
                    "narrative": narrative,
                }),
            }

            item_status = "completed"
            item_result = {}
            async for event in run_pipeline(narrative):
                if event.event_type == "pipeline_error":
                    item_status = "failed"
                    item_result = {"error": event.data.get("error", "")}
                elif event.event_type == "pipeline_complete":
                    item_result = {
                        "claim_id": event.claim_id,
                        "verdict": event.data.get("verdict", ""),
                        "score": event.data.get("score", 0),
                    }
                elif event.event_type == "pipeline_duplicate":
                    item_status = "duplicate"
                    item_result = {"claim_id": event.data.get("claim_id", "")}
                yield {
                    "event": event.event_type,
                    "data": json.dumps(event.model_dump(mode="json")),
                }

            if item_status == "failed":
                failed += 1
            else:
                processed += 1

            yield {
                "event": "bulk_item_completed",
                "data": json.dumps({
                    "index": index,
                    "total": len(narratives),
                    "status": item_status,
                    **item_result,
                }),
            }

        yield {
            "event": "bulk_complete",
            "data": json.dumps({"processed": processed, "failed": failed}),
        }

    return EventSourceResponse(event_generator())
