import ipaddress
import json
import httpx
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

from app.core.client_ip import resolve_client_ip, set_client_ip
from app.core.setup import missing_setup_items
from app.core.sectors_config import _migrate_runtime, dev_ips, sectors_key_for_ip

router = APIRouter()

SETTINGS_FILE = Path(__file__).parent.parent.parent.parent / "data" / "runtime_settings.json"


class RuntimeSettings(BaseModel):
    llm_provider: Optional[str] = None
    llm_endpoint: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_model: Optional[str] = None
    sectors_api_key: Optional[str] = None
    sectors_enforce_per_ip: Optional[bool] = None
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


class ManageSectorsIpsRequest(BaseModel):
    ip: str
    action: str  # "add" | "remove"


def _mask(key: str) -> str:
    """Mask a secret for display: first 4 (or 6) chars + ... + last 4."""
    if not key:
        return ""
    if len(key) <= 12:
        return key[:4] + "..." + key[-4:]
    return key[:6] + "..." + key[-4:]


def _load() -> dict:
    if SETTINGS_FILE.exists():
        try:
            return _migrate_runtime(json.loads(SETTINGS_FILE.read_text()))
        except Exception:
            return {}
    return {}


def _save(data: dict):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2))


def get_runtime_settings() -> dict:
    return _load()


def _ip_is_owner(data: dict, ip: str) -> bool:
    return ip in dev_ips() or data.get("sectors_key_owner_ip") == ip


def _authorized_ips(data: dict) -> list[str]:
    return list(data.get("sectors_authorized_ips") or [])


@router.get("/status")
async def setup_status(request: Request):
    set_client_ip(resolve_client_ip(request))
    missing = missing_setup_items()
    return {"complete": len(missing) == 0, "missing": missing}


@router.post("/validate-sectors", response_model=ValidateSectorsResponse)
async def validate_sectors(request: Request, req: ValidateSectorsRequest):
    set_client_ip(resolve_client_ip(request))
    key = req.api_key
    # A masked placeholder (e.g. "ab12...wxyz" or "ab••••••wxyz") means the
    # frontend loaded the saved key but never holds the real secret — validate
    # against the stored key instead so "Validate" works on reload.
    if "..." in key or "••••" in key:
        from app.core.sectors_config import sectors_api_key
        key = sectors_api_key()
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
async def validate_llm_endpoint(request: Request, req: ValidateEndpointRequest):
    set_client_ip(resolve_client_ip(request))
    endpoint = req.endpoint.rstrip("/")
    models_url = f"{endpoint}/v1/models" if "/v1" not in endpoint else f"{endpoint}/models"
    headers = {}
    api_key = req.api_key
    # Masked placeholder → validate with the stored key instead.
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
    ip = resolve_client_ip(request)
    set_client_ip(ip)
    owner = data.get("sectors_key_owner_ip")
    authorized = _authorized_ips(data)
    this_key = sectors_key_for_ip(data, ip)

    # Mask API keys in response; expose allowlist + detected IP + owner flag.
    masked = {}
    for k, v in data.items():
        if k == "sectors_keys_by_ip":
            continue  # legacy registry is server-side only
        if "key" in k.lower() and v and len(str(v)) > 8:
            masked[k] = _mask(str(v))
        else:
            masked[k] = v
    masked["sectors_api_key"] = _mask(this_key)
    masked["sectors_key_owner_ip"] = owner
    masked["sectors_authorized_ips"] = authorized
    masked["sectors_key_is_owner"] = _ip_is_owner(data, ip)
    # Legacy alias kept for frontend compat (any resolved key present).
    masked["sectors_key_bound_to"] = owner if owner else (ip if this_key else None)
    if ip:
        masked["client_ip"] = ip
    return masked


@router.put("")
async def update_settings(request: Request, update: RuntimeSettings):
    current = _load()
    ip = resolve_client_ip(request)
    set_client_ip(ip)

    for field_name in RuntimeSettings.model_fields:
        val = getattr(update, field_name)

        # Sectors key is a single shared key owned by the first IP that bound it.
        # Only the owner (or a dev IP) may set or replace it.
        if field_name == "sectors_api_key":
            if val is None:
                continue
            stripped = str(val)
            if stripped == "":
                if _ip_is_owner(current, ip):
                    current.pop("sectors_api_key", None)
                    current.pop("sectors_key_owner_ip", None)
                    current.pop("sectors_authorized_ips", None)
                continue
            # masked placeholder → leave the stored key as-is
            if "..." in stripped or "••••" in stripped:
                continue
            owner = current.get("sectors_key_owner_ip")
            if owner and not _ip_is_owner(current, ip):
                raise HTTPException(
                    status_code=403,
                    detail="Only the owner IP can change the Sectors API key. Ask the owner to add your IP first.",
                )
            if not owner:
                current["sectors_key_owner_ip"] = ip
            current["sectors_api_key"] = stripped
            authorized = _authorized_ips(current)
            for a in {ip, current["sectors_key_owner_ip"]}:
                if a and a not in authorized:
                    authorized.append(a)
            current["sectors_authorized_ips"] = authorized
            continue

        if val is not None:
            if "key" in field_name.lower() and ("..." in str(val) or "••••" in str(val)):
                continue
            current[field_name] = val

    _save(current)

    masked_settings = dict(current.items())
    for k, v in list(masked_settings.items()):
        if k == "sectors_keys_by_ip":
            continue
        if k == "sectors_api_key":
            masked_settings[k] = _mask(str(v))
        elif "key" in k.lower() and v and len(str(v)) > 8:
            masked_settings[k] = _mask(str(v))
    return {"status": "ok", "settings": masked_settings}


@router.post("/sectors-ips")
async def manage_sectors_ips(request: Request, req: ManageSectorsIpsRequest):
    """Add/remove an authorized IP. Only the owner IP may manage the list."""
    data = _load()
    ip = resolve_client_ip(request)
    set_client_ip(ip)

    owner = data.get("sectors_key_owner_ip")
    if not owner:
        raise HTTPException(status_code=400, detail="No Sectors API key is bound yet.")
    if not _ip_is_owner(data, ip):
        raise HTTPException(
            status_code=403,
            detail="Only the owner IP can manage the authorized IP list.",
        )

    try:
        ipaddress.ip_address(req.ip)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid IP address: {req.ip}")

    authorized = _authorized_ips(data)
    if req.action == "add":
        if req.ip not in authorized and req.ip != owner:
            authorized.append(req.ip)
    elif req.action == "remove":
        if req.ip == owner:
            raise HTTPException(status_code=400, detail="The owner IP cannot be removed.")
        authorized = [a for a in authorized if a != req.ip]
    else:
        raise HTTPException(status_code=400, detail="action must be 'add' or 'remove'")

    data["sectors_authorized_ips"] = authorized
    _save(data)
    return {"ok": True, "sectors_key_owner_ip": owner, "sectors_authorized_ips": authorized}


@router.delete("")
async def reset_settings():
    if SETTINGS_FILE.exists():
        SETTINGS_FILE.unlink()
    return {"status": "ok", "message": "Settings reset to defaults"}