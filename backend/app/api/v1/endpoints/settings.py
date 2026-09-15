import json
import httpx
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

from app.core.setup import missing_setup_items
from app.core import sectors_config
from app.core.identity import email_from_request

router = APIRouter()

SETTINGS_FILE = Path(__file__).parent.parent.parent.parent / "data" / "runtime_settings.json"

# Never returned verbatim to clients.
_SENSITIVE_KEYS = {
    "sectors_keys_by_email",
    "session_secret",
    "sectors_oauth_access_token",
    "sectors_oauth_refresh_token",
    "sectors_oauth_client_secret",
    "sectors_oauth_password",
    "sectors_oauth_email",
}


class RuntimeSettings(BaseModel):
    llm_provider: Optional[str] = None
    llm_endpoint: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_model: Optional[str] = None
    sectors_api_key: Optional[str] = None
    claim_parser_model: Optional[str] = None
    skeptic_model: Optional[str] = None
    scorer_model: Optional[str] = None
    news_model: Optional[str] = None
    chat_model: Optional[str] = None
    follow_up_model: Optional[str] = None


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


def _mask(key: str) -> str:
    """Mask a secret for display: first 4/6 chars + ... + last 4."""
    if not key:
        return ""
    if len(key) <= 12:
        return key[:4] + "..." + key[-4:]
    return key[:6] + "..." + key[-4:]


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


@router.get("/status")
async def setup_status():
    missing = missing_setup_items()
    return {"complete": len(missing) == 0, "missing": missing}


@router.post("/validate-sectors", response_model=ValidateSectorsResponse)
async def validate_sectors(req: ValidateSectorsRequest):
    key = req.api_key
    # A masked placeholder means the frontend never holds the real secret —
    # validate against the stored key instead so "Validate" works on reload.
    if "..." in key or "••••" in key:
        key = sectors_config.sectors_api_key()
    headers = {"Authorization": key}
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
    api_key = req.api_key
    if api_key and ("..." in api_key or "••••" in api_key):
        from app.core.llm_config import llm_api_key
        api_key = llm_api_key()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
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


@router.get("")
async def get_settings(request: Request):
    data = _load()
    email = email_from_request(request)

    masked = {k: v for k, v in data.items() if k not in _SENSITIVE_KEYS}
    masked.pop("sectors_api_key", None)
    # Only surface the caller's own bound key; never the deployment key to anon.
    masked["sectors_api_key"] = _mask(sectors_config.key_for_email(email) if email else "")
    masked["sectors_key_owner_email"] = sectors_config.owner_email()
    masked["authenticated"] = bool(email)
    masked["email"] = email or None
    return masked


@router.put("")
async def update_settings(request: Request, update: RuntimeSettings):
    current = _load()
    email = email_from_request(request)

    for field_name in RuntimeSettings.model_fields:
        val = getattr(update, field_name)
        if val is None:
            continue

        if field_name == "sectors_api_key":
            stripped = str(val)
            # masked placeholder → leave the stored key as-is
            if "..." in stripped or "••••" in stripped:
                continue
            if not email:
                raise HTTPException(status_code=401, detail="Sign in to bind a Sectors API key.")
            keys = current.get("sectors_keys_by_email")
            keys = dict(keys) if isinstance(keys, dict) else {}
            if stripped == "":
                keys.pop(email, None)
                current["sectors_keys_by_email"] = keys
                if current.get("sectors_key_owner_email") == email:
                    current.pop("sectors_key_owner_email", None)
            else:
                keys[email] = stripped
                current["sectors_keys_by_email"] = keys
                current["sectors_key_owner_email"] = email
                current["sectors_api_key"] = stripped
            continue

        # Don't let a masked key overwrite a stored secret.
        if "key" in field_name.lower() and ("..." in str(val) or "••••" in str(val)):
            continue
        current[field_name] = val

    _save(current)

    masked_settings = {k: v for k, v in current.items() if k not in _SENSITIVE_KEYS}
    masked_settings.pop("sectors_api_key", None)
    if "llm_api_key" in masked_settings:
        masked_settings["llm_api_key"] = _mask(str(masked_settings["llm_api_key"]))
    return {"status": "ok", "settings": masked_settings}


@router.delete("")
async def reset_settings():
    if SETTINGS_FILE.exists():
        SETTINGS_FILE.unlink()
    return {"status": "ok", "message": "Settings reset to defaults"}
