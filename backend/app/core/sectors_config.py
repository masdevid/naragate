"""Sectors credentials, keyed by the logged-in **email** (not IP).

Ownership model: each Sectors account (email) has its own API key, stored in
runtime settings under `sectors_keys_by_email`. The server-side/deployment key
(env `SECTORS_API_KEY`) is the fallback when no user session is bound, so health
checks and background jobs still work. There is no IP-based ownership.
"""

import json
import secrets
from pathlib import Path

from app.config.settings import settings
from app.core.identity import get_current_email

SETTINGS_FILE = Path(__file__).parent.parent / "data" / "runtime_settings.json"


def _load_runtime() -> dict:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save_runtime(data: dict) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2))


def _env_key() -> str:
    return settings.SECTORS_API_KEY or ""


def keys_by_email(data: dict) -> dict:
    keys = data.get("sectors_keys_by_email")
    return keys if isinstance(keys, dict) else {}


def key_for_email(email: str) -> str:
    """The API key bound to an email, falling back to the deployment key."""
    data = _load_runtime()
    if email:
        bound = keys_by_email(data).get(email)
        if bound:
            return bound
    return data.get("sectors_api_key") or _env_key()


def bind_key_to_email(email: str, api_key: str) -> None:
    """Bind (or replace) the API key for an email and mark it the owner."""
    data = _load_runtime()
    keys = keys_by_email(data)
    keys[email] = api_key
    data["sectors_keys_by_email"] = keys
    data["sectors_key_owner_email"] = email
    # Keep a copy as the deployment/global key for server-side fallback.
    data["sectors_api_key"] = api_key
    _save_runtime(data)


def unbind_key(email: str) -> None:
    data = _load_runtime()
    keys = keys_by_email(data)
    keys.pop(email, None)
    data["sectors_keys_by_email"] = keys
    if data.get("sectors_key_owner_email") == email:
        data.pop("sectors_key_owner_email", None)
    _save_runtime(data)


def owner_email() -> str:
    return _load_runtime().get("sectors_key_owner_email") or ""


def sectors_api_key() -> str:
    """Resolve the Sectors API key for the current request's identity."""
    return key_for_email(get_current_email())


def sectors_oauth_tokens() -> dict:
    """Resolve Sectors first-party OAuth tokens (runtime settings, then env)."""
    data = _load_runtime()
    return {
        "access_token": data.get("sectors_oauth_access_token") or settings.SECTORS_OAUTH_ACCESS_TOKEN,
        "refresh_token": data.get("sectors_oauth_refresh_token") or settings.SECTORS_OAUTH_REFRESH_TOKEN,
        "client_id": data.get("sectors_oauth_client_id") or settings.SECTORS_OAUTH_CLIENT_ID,
        "client_secret": data.get("sectors_oauth_client_secret") or settings.SECTORS_OAUTH_CLIENT_SECRET,
        "email": data.get("sectors_oauth_email") or settings.SECTORS_ACCOUNT_EMAIL,
        "password": data.get("sectors_oauth_password") or settings.SECTORS_ACCOUNT_PASSWORD,
    }


def store_oauth_login(email: str, password: str | None, access: str | None, refresh: str | None) -> None:
    """Persist the login credentials/tokens so account usage can self-renew."""
    data = _load_runtime()
    data["sectors_oauth_email"] = email
    if password:
        data["sectors_oauth_password"] = password
    if access:
        data["sectors_oauth_access_token"] = access
    if refresh:
        data["sectors_oauth_refresh_token"] = refresh
    _save_runtime(data)


def clear_oauth_login() -> None:
    data = _load_runtime()
    for k in ("sectors_oauth_email", "sectors_oauth_password",
              "sectors_oauth_access_token", "sectors_oauth_refresh_token"):
        data.pop(k, None)
    _save_runtime(data)


def session_secret() -> str:
    """Signing secret for the login session cookie (generated once, persisted)."""
    data = _load_runtime()
    secret = data.get("session_secret") or settings.SESSION_SECRET
    if secret:
        return secret
    secret = secrets.token_urlsafe(48)
    data["session_secret"] = secret
    _save_runtime(data)
    return secret
