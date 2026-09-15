from fastapi import APIRouter
from app.core.usage_tracker import get_usage_summary, record_account_snapshot
from app.core.sectors_account import fetch_account_snapshot
from app.config.settings import settings

router = APIRouter()


@router.get("")
async def get_usage():
    # Best-effort: refresh the authoritative Sectors account snapshot (cached
    # in-process for 5 min) so the usage page shows real credits, then fall back
    # to the local "this instance" ledger.
    snapshot = await fetch_account_snapshot()
    record_account_snapshot(snapshot)
    return get_usage_summary(budget=settings.CREDIT_BUDGET + settings.HACKATHON_BUDGET)
