from fastapi import APIRouter
from app.models.schemas import RealityGapScore
from app.core.evidence_cache import cache as evidence_cache
import json

router = APIRouter()

@router.get("/", response_model=list[RealityGapScore])
async def list_evidence():
    return []

@router.get("/{ticker}", response_model=dict)
async def get_evidence(ticker: str):
    cached = await evidence_cache.get(ticker)
    if not cached:
        return {"ticker": ticker, "cached": False}
    return cached
