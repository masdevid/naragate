import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.core.setup import missing_setup_items
from app.services.pipeline import run_pipeline

router = APIRouter()


class NarrativeInput(BaseModel):
    narrative: str


@router.post("/evaluate")
async def evaluate_narrative(input_data: NarrativeInput):
    missing = missing_setup_items()
    if missing:
        raise HTTPException(
            status_code=409,
            detail={"code": "setup_incomplete", "missing": missing},
        )

    async def event_generator():
        async for event in run_pipeline(input_data.narrative):
            yield {
                "event": event.event_type,
                "data": json.dumps(event.model_dump(mode="json")),
            }

    return EventSourceResponse(event_generator())
