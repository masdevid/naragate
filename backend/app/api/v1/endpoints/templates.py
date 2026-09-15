"""Curated demo templates endpoint (shared by the web dashboard and non-web clients)."""

from fastapi import APIRouter

from app.services.templates import TEMPLATES

router = APIRouter()


@router.get("")
async def list_templates():
    return {"templates": TEMPLATES}
