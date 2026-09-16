"""Sectors credentials, keyed by the logged-in **email** (not IP).

Ownership model: each Sectors account (email) has its own API key, stored in
runtime settings under `sectors_keys_by_email`. The server-side/deployment key
(env `SECTORS_API_KEY`) is the fallback when no user session is bound, so health
checks and background jobs still work. There is no IP-based ownership.
"""

import hashlib
import json
import secrets
from datetime import datetime, timezone
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


# --- per-user API tokens (bearer auth for non-web surfaces) ----------------
#
# The web UI authenticates with a signed session cookie; MCP/skills/agents have
# no cookie. A user mints an API token in Settings, hands it to their harness
# (NARAGATE_TOKEN), and the backend resolves it to the same email — so the MCP
# call uses that user's own Sectors key, evidence cache and credit ledger.
# Only the SHA-256 hash is stored; the raw token is shown once at creation.

_TOKEN_PREFIX = "nrg_"
_TOKEN_ID_LEN = 16
_LAST_USED_THROTTLE_SECONDS = 300


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _tokens(data: dict) -> dict:
    tokens = data.get("api_tokens")
    return tokens if isinstance(tokens, dict) else {}


def create_api_token(email: str, name: str = "") -> dict:
    """Mint an API token for an email. Returns the raw token exactly once."""
    email = (email or "").strip().lower()
    if not email:
        raise ValueError("email required")
    raw = _TOKEN_PREFIX + secrets.token_urlsafe(30)
    digest = _hash_token(raw)
    data = _load_runtime()
    tokens = _tokens(data)
    tokens[digest] = {
        "email": email,
        "name": (name or "").strip() or "MCP token",
        "prefix": raw[:_TOKEN_ID_LEN],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_used_at": None,
    }
    data["api_tokens"] = tokens
    _save_runtime(data)
    return {"token": raw, "id": digest[:_TOKEN_ID_LEN], **tokens[digest]}


def list_api_tokens(email: str) -> list[dict]:
    email = (email or "").strip().lower()
    out = [
        {"id": digest[:_TOKEN_ID_LEN], **rec}
        for digest, rec in _tokens(_load_runtime()).items()
        if rec.get("email") == email
    ]
    out.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    return out


def revoke_api_token(email: str, token_id: str) -> bool:
    """Revoke one token by its short id, scoped to the owning email."""
    email = (email or "").strip().lower()
    token_id = (token_id or "").strip()
    if not email or not token_id:
        return False
    data = _load_runtime()
    tokens = _tokens(data)
    match = next(
        (d for d, rec in tokens.items()
         if d[:_TOKEN_ID_LEN] == token_id and rec.get("email") == email),
        None,
    )
    if not match:
        return False
    tokens.pop(match, None)
    data["api_tokens"] = tokens
    _save_runtime(data)
    return True


def email_for_token(token: str) -> str:
    """Resolve a raw bearer token to its email ("" if unknown)."""
    if not token:
        return ""
    digest = _hash_token(token)
    data = _load_runtime()
    tokens = _tokens(data)
    rec = tokens.get(digest)
    if not rec:
        return ""
    now = datetime.now(timezone.utc)
    try:
        last = rec.get("last_used_at")
        if not last or (now - datetime.fromisoformat(last)).total_seconds() > _LAST_USED_THROTTLE_SECONDS:
            rec["last_used_at"] = now.isoformat()
            data["api_tokens"] = tokens
            _save_runtime(data)
    except Exception:  # noqa: BLE001 — timestamp bookkeeping must never block auth
        pass
    return rec.get("email") or ""


def bearer_email(request) -> str:
    """The email carried by an `Authorization: Bearer <token>` header ("" if none)."""
    header = request.headers.get("authorization") or ""
    if not header.lower().startswith("bearer "):
        return ""
    return email_for_token(header.split(" ", 1)[1].strip())
