from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx
import asyncio
from datetime import datetime

from app.config.settings import settings
from app.api.v1.endpoints import claims, evidence, stream

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title="Naragate",
    description="AI evidence engine that detects financial claims in Indonesian market narratives and verifies them against Sectors v2 financial data",
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
    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            r = await client.get(
                "https://api.sectors.app/v2/company/corporate-actions/BBCA/",
                headers={"Authorization": settings.SECTORS_API_KEY}
            )
            if r.status_code == 200:
                return {"status": "ok", "endpoint": "https://api.sectors.app/v2", "key_length": len(settings.SECTORS_API_KEY)}
            return {"status": "error", "endpoint": "https://api.sectors.app/v2", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"status": "error", "endpoint": "https://api.sectors.app/v2", "error": str(e)}

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
