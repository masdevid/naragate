"""Pre-check (T1) endpoint: policy→price amplifier validation report.

Serves the same report the CLI runner produces, cached-only by default so the
UI can never burn Sectors credits just by opening a page. A warm cache costs
0 API calls; a cold cache returns 503 until either the CLI has run once or a
deliberate `?refresh=true` is passed (which may hit the Sectors API).
"""

from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from app.services.policy_signal import PrecheckCacheCold, run_precheck

router = APIRouter()


@router.get("/")
async def get_precheck(refresh: bool = False):
    try:
        report = await run_precheck(cached_only=not refresh)
    except PrecheckCacheCold as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "precheck_cache_cold",
                "error": str(exc),
                "hint": "Run the T1 pre-check CLI once to backfill, or retry with ?refresh=true.",
            },
        )
    except Exception as exc:  # noqa: BLE001 — report as a structured 503
        raise HTTPException(
            status_code=503,
            detail={"code": "precheck_unavailable", "error": str(exc)},
        )
    payload = asdict(report)
    payload["beacon_list"] = report.beacon_list
    return payload
