from fastapi import APIRouter, HTTPException
from app.models.schemas import ClaimCreate, Claim, ClaimStatus, ClaimBulkDelete
from app.services.claims_store import claims_store

router = APIRouter()


@router.post("/", response_model=dict)
async def create_claim(claim_input: ClaimCreate):
    claim_id = await claims_store.create_claim(claim_input.narrative)
    return {"claim_id": claim_id, "narrative": claim_input.narrative, "status": "pending"}


@router.get("/", response_model=list)
async def list_claims(limit: int = 20):
    return await claims_store.list_claims(limit=limit)


@router.delete("/", response_model=dict)
async def delete_claims(payload: ClaimBulkDelete):
    deleted = await claims_store.delete_claims(payload.claim_ids)
    return {"deleted": deleted}


@router.get("/{claim_id}")
async def get_claim(claim_id: str):
    state = await claims_store.get_claim(claim_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    return state


@router.delete("/{claim_id}")
async def delete_claim(claim_id: str):
    deleted = await claims_store.delete_claim(claim_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {"claim_id": claim_id, "deleted": True}


@router.get("/{claim_id}/status")
async def get_claim_status(claim_id: str):
    state = await claims_store.get_claim(claim_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {"claim_id": claim_id, "status": state.get("status")}
