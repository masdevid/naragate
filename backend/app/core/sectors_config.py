import json
from pathlib import Path

from app.config.settings import settings

SETTINGS_FILE = Path(__file__).parent.parent / "data" / "runtime_settings.json"


def _load_runtime() -> dict:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text())
        except Exception:
            return {}
    return {}


def sectors_api_key() -> str:
    """Resolve the Sectors API key at call time.

    The web UI (runtime settings) wins whenever set; otherwise fall back to
    the startup-detected value (env, .env, or profile secrets).
    """
    runtime = _load_runtime()
    key = runtime.get("sectors_api_key")
    if key:
        return key
    return settings.SECTORS_API_KEY