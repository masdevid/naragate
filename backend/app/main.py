from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx
import asyncio
import time
import json
from datetime import datetime
from pathlib import Path

from app.config.settings import settings
from app.api.v1.endpoints import claims, evidence, stream
from app.api.v1.endpoints import settings as settings_router
from app.api.v1.endpoints import usage as usage_router

SETTINGS_FILE = Path(__file__).parent / "data" / "runtime_settings.json"

def _bootstrap_runtime_settings():
    """Auto-load .env values into runtime_settings.json if not already present."""
    existing = {}
    if SETTINGS_FILE.exists():
        try:
            existing = json.loads(SETTINGS_FILE.read_text())
        except Exception:
            existing = {}

    changed = False

    if settings.SECTORS_API_KEY and not existing.get("sectors_api_key"):
        existing["sectors_api_key"] = settings.SECTORS_API_KEY
        changed = True

    if settings.OLLAMA_BASE_URL and not existing.get("llm_endpoint"):
        endpoint = settings.OLLAMA_BASE_URL
        if not endpoint.endswith("/v1") and not endpoint.endswith("/v1/"):
            endpoint = endpoint.rstrip("/") + "/v1"
        existing["llm_endpoint"] = endpoint
        changed = True

    if settings.OLLAMA_MODEL and not existing.get("llm_model"):
        existing["llm_model"] = settings.OLLAMA_MODEL
        changed = True

    if changed:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(existing, indent=2))

# ── Healthcheck cache ──────────────────────────────────────────────
_sectors_cache: dict = {"result": None, "ts": 0.0}
_HEALTHCHECK_TTL = 86400  # 1 day

@asynccontextmanager
async def lifespan(app: FastAPI):
    _bootstrap_runtime_settings()
    yield

app = FastAPI(
    title="Naragate",
    description="AI evidence engine for Indonesian market narratives",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(claims.router, prefix="/api/v1/claims", tags=["claims"])
app.include_router(evidence.router, prefix="/api/v1/evidence", tags=["evidence"])
app.include_router(stream.router, prefix="/api/v1/stream", tags=["stream"])
app.include_router(settings_router.router, prefix="/api/v1/settings", tags=["settings"])
app.include_router(usage_router.router, prefix="/api/v1/usage", tags=["usage"])

async def check_ollama() -> dict:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{settings.OLLAMA_BASE_URL}/models")
            if r.status_code == 200:
                data = r.json()
                models = [m["id"] for m in data.get("data", [])]
                return {"status": "ok", "endpoint": settings.OLLAMA_BASE_URL, "models": models, "model_count": len(models)}
            return {"status": "error", "endpoint": settings.OLLAMA_BASE_URL, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"status": "error", "endpoint": settings.OLLAMA_BASE_URL, "error": str(e)}

async def check_sectors() -> dict:
    now = time.monotonic()
    if _sectors_cache["result"] and (now - _sectors_cache["ts"]) < _HEALTHCHECK_TTL:
        return _sectors_cache["result"]

    result: dict
    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            r = await client.get(
                "https://api.sectors.app/v2/company/corporate-actions/BBCA/",
                headers={"Authorization": settings.SECTORS_API_KEY}
            )
            if r.status_code == 200:
                result = {"status": "ok", "endpoint": "https://api.sectors.app/v2", "key_length": len(settings.SECTORS_API_KEY)}
            else:
                result = {"status": "error", "endpoint": "https://api.sectors.app/v2", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        result = {"status": "error", "endpoint": "https://api.sectors.app/v2", "error": str(e)}

    if result["status"] == "ok":
        _sectors_cache["result"] = result
        _sectors_cache["ts"] = now
    return result

@app.get("/health")
async def health():
    ollama_task = asyncio.create_task(check_ollama())
    sectors_task = asyncio.create_task(check_sectors())
    ollama, sectors = await asyncio.gather(ollama_task, sectors_task)

    return {
        "status": "healthy" if ollama["status"] == "ok" and sectors["status"] == "ok" else "degraded",
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "ollama": ollama,
            "sectors_api": sectors,
        },
        "config": {
            "credit_budget": settings.CREDIT_BUDGET,
            "curated_stocks": settings.CURATED_STOCKS,
            "cache_ttl_company": settings.EVIDENCE_CACHE_TTL_COMPANY,
            "cache_ttl_daily": settings.EVIDENCE_CACHE_TTL_DAILY,
        }
    }
