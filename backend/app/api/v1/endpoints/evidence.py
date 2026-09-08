from fastapi import APIRouter, HTTPException
from app.models.schemas import RealityGapScore
from app.core.evidence_cache import cache as evidence_cache
from app.core.sectors_client import sectors_client
import json

router = APIRouter()

@router.get("/", response_model=list[RealityGapScore])
async def list_evidence():
    return []

@router.get("/{ticker}", response_model=dict)
async def get_evidence(ticker: str):
    if not sectors_client.validate_ticker(ticker):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ticker format: {ticker}. Ticker must be 4 uppercase letters."
        )
    cached = await evidence_cache.get(ticker)
    if not cached:
        return {"ticker": ticker, "cached": False}
    return cached
