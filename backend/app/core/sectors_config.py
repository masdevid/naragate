import json
from pathlib import Path

from app.config.settings import settings
from app.core.client_ip import get_client_ip

SETTINGS_FILE = Path(__file__).parent.parent / "data" / "runtime_settings.json"


def _load_runtime() -> dict:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text())
        except Exception:
            return {}
    return {}


def _env_key() -> str:
    return settings.SECTORS_API_KEY or ""


def sectors_api_key() -> str:
    """Resolve the Sectors API key for the current request's client IP.

    Resolution (see CONTEXT.md: Evidence Graph and Credit rules):
    1. A per-IP registry entry (`sectors_keys_by_ip`) for the current client IP
       wins — each IP may save its own key via Settings.
    2. When enforcement is ON (`sectors_enforce_per_ip`, default), an IP with no
       registry entry gets NO key, so it cannot spend anyone else's credits; it
       must add its own in Settings. The legacy/env key is NOT shared.
    3. Fallback to the legacy global key / startup env key only when there is no
       request context (e.g. health probes) or enforcement is OFF.
    """
    runtime = _load_runtime()
    ip = get_client_ip()
    registry = runtime.get("sectors_keys_by_ip") or {}
    enforce = runtime.get("sectors_enforce_per_ip", True)

    if ip:
        own = registry.get(ip)
        if own:
            return own
        if enforce:
            return ""
        legacy = runtime.get("sectors_api_key")
        return legacy or _env_key()

    legacy = runtime.get("sectors_api_key")
    return legacy or _env_key()