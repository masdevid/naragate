import json
from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.services.pipeline import run_pipeline

router = APIRouter()


class NarrativeInput(BaseModel):
    narrative: str


@router.post("/evaluate")
async def evaluate_narrative(input_data: NarrativeInput):
    async def event_generator():
        async for event in run_pipeline(input_data.narrative):
            yield {
                "event": event.event_type,
                "data": json.dumps(event.model_dump(mode="json")),
            }

    return EventSourceResponse(event_generator())
