from fastapi import APIRouter
from app.core.usage_tracker import get_usage_summary
from app.config.settings import settings

router = APIRouter()


@router.get("")
async def get_usage():
    return get_usage_summary(budget=settings.CREDIT_BUDGET)
