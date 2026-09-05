import json
import httpx
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.core.setup import missing_setup_items

router = APIRouter()

SETTINGS_FILE = Path(__file__).parent.parent.parent.parent / "data" / "runtime_settings.json"

class RuntimeSettings(BaseModel):
    llm_endpoint: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_model: Optional[str] = None
    sectors_api_key: Optional[str] = None
    claim_parser_model: Optional[str] = None
    skeptic_model: Optional[str] = None
    scorer_model: Optional[str] = None

class ValidateEndpointRequest(BaseModel):
    endpoint: str
    api_key: Optional[str] = None

class ValidateEndpointResponse(BaseModel):
    ok: bool
    endpoint: str
    models: list[str] = []
    error: Optional[str] = None

class ValidateSectorsRequest(BaseModel):
    api_key: str

class ValidateSectorsResponse(BaseModel):
    ok: bool
    error: Optional[str] = None

@router.get("/status")
async def setup_status():
    missing = missing_setup_items()
    return {"complete": len(missing) == 0, "missing": missing}

@router.post("/validate-sectors", response_model=ValidateSectorsResponse)
async def validate_sectors(req: ValidateSectorsRequest):
    headers = {"Authorization": req.api_key}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get("https://api.sectors.app/v2/daily/BBCA/", headers=headers)
            if r.status_code == 200:
                return ValidateSectorsResponse(ok=True)
            return ValidateSectorsResponse(ok=False, error=f"HTTP {r.status_code}: {r.text[:200]}")
    except httpx.ConnectError:
        return ValidateSectorsResponse(ok=False, error="Connection refused — check your network")
    except httpx.TimeoutException:
        return ValidateSectorsResponse(ok=False, error="Request timed out after 8s")
    except Exception as e:
        return ValidateSectorsResponse(ok=False, error=str(e)[:200])

@router.post("/validate-llm", response_model=ValidateEndpointResponse)
async def validate_llm_endpoint(req: ValidateEndpointRequest):
    endpoint = req.endpoint.rstrip("/")
    models_url = f"{endpoint}/v1/models" if "/v1" not in endpoint else f"{endpoint}/models"
    headers = {}
    if req.api_key:
        headers["Authorization"] = f"Bearer {req.api_key}"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(models_url, headers=headers)
            if r.status_code == 200:
                data = r.json()
                models = [m.get("id", "") for m in data.get("data", [])]
                models = [m for m in models if m]
                return ValidateEndpointResponse(ok=True, endpoint=endpoint, models=sorted(models))
            return ValidateEndpointResponse(ok=False, endpoint=endpoint, error=f"HTTP {r.status_code}: {r.text[:200]}")
    except httpx.ConnectError:
        return ValidateEndpointResponse(ok=False, endpoint=endpoint, error="Connection refused — is the server running?")
    except httpx.TimeoutException:
        return ValidateEndpointResponse(ok=False, endpoint=endpoint, error="Request timed out after 8s")
    except Exception as e:
        return ValidateEndpointResponse(ok=False, endpoint=endpoint, error=str(e)[:200])

def _load() -> dict:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text())
        except Exception:
            return {}
    return {}

def _save(data: dict):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2))

def get_runtime_settings() -> dict:
    return _load()

@router.get("")
async def get_settings():
    data = _load()
    # Mask API keys in response
    masked = {}
    for k, v in data.items():
        if "key" in k.lower() and v and len(str(v)) > 8:
            masked[k] = str(v)[:4] + "..." + str(v)[-4:]
        else:
            masked[k] = v
    return masked

@router.put("")
async def update_settings(update: RuntimeSettings):
    current = _load()
    for field_name in RuntimeSettings.model_fields:
        val = getattr(update, field_name)
        if val is not None and val == "":
            current.pop(field_name, None)
        elif val is not None and val != "":
            if "key" in field_name.lower() and "..." in str(val):
                continue
            current[field_name] = val
    _save(current)
    return {"status": "ok", "settings": current}

@router.delete("")
async def reset_settings():
    if SETTINGS_FILE.exists():
        SETTINGS_FILE.unlink()
    return {"status": "ok", "message": "Settings reset to defaults"}
