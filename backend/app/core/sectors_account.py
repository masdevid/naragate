"""Sectors first-party account usage (authoritative credit/quota view).

`/api/usage/` and `/auth/users/{id}/` live outside the public v2 data API and
need an OAuth2 bearer token, not the API key. They are optional: when no token
(or refresh credentials) is configured, callers get `configured=False` and the
app keeps working off the local ledger.

The endpoints are Cloudflare-fronted and 1010-ban the default httpx/urllib
signature, so every request sends a normal browser User-Agent. See
references/sectors-account-usage.md.
"""

from __future__ import annotations

import base64
import json
import time
from datetime import datetime, timezone

import httpx

from app.core.sectors_config import sectors_oauth_tokens

BASE = "https://api.sectors.app"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
CACHE_TTL = 300  # seconds — poll at most once per 5 min per process

_cache: dict = {"data": None, "ts": 0.0}


def reset_cache() -> None:
    _cache["data"] = None
    _cache["ts"] = 0.0


def _jwt_claims(token: str) -> dict:
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except Exception:  # noqa: BLE001
        return {}


def _unexpired(token: str) -> bool:
    exp = _jwt_claims(token).get("exp")
    return isinstance(exp, (int, float)) and exp > time.time()


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT}


def _tokens() -> dict:
    """Runtime-settings-first OAuth tokens (env fallback)."""
    return sectors_oauth_tokens()


async def _login_access_token(client: httpx.AsyncClient) -> str | None:
    """Mint an access token via POST /auth/token/ (email + password).

    This is the dashboard's own login: it needs no client_id and returns
    `{refresh, access}`, so it is the durable renewal path.
    """
    tokens = _tokens()
    email = (tokens.get("email") or "").strip()
    password = tokens.get("password") or ""
    if not email or not password:
        return None
    try:
        resp = await client.post(
            f"{BASE}/auth/token/",
            json={"email": email, "password": password},
            headers={"User-Agent": USER_AGENT},
        )
        resp.raise_for_status()
        return resp.json().get("access")
    except Exception:  # noqa: BLE001 — best-effort; caller degrades
        return None


async def login_with_password(
    email: str, password: str, client: httpx.AsyncClient | None = None
) -> dict | None:
    """Verify account credentials via POST /auth/token/ and load the profile.

    Returns {"access", "refresh", "profile"} on success, else None.
    """
    owns_client = client is None
    client = client or httpx.AsyncClient(timeout=15.0, follow_redirects=True)
    try:
        resp = await client.post(
            f"{BASE}/auth/token/",
            json={"email": email, "password": password},
            headers={"User-Agent": USER_AGENT},
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        access = data.get("access")
        if not access:
            return None
        profile: dict = {}
        user_id = _jwt_claims(access).get("user_id")
        if user_id:
            prof = await client.get(f"{BASE}/auth/users/{user_id}/", headers=_headers(access))
            if prof.status_code == 200:
                profile = prof.json()
        return {"access": access, "refresh": data.get("refresh"), "profile": profile}
    except Exception:  # noqa: BLE001 — treated as invalid login
        return None
    finally:
        if owns_client:
            await client.aclose()


async def _refresh_grant_token(client: httpx.AsyncClient) -> str | None:
    """OAuth refresh_token grant (needs a registered client_id)."""
    tokens = _tokens()
    client_id = (tokens.get("client_id") or "").strip()
    refresh = (tokens.get("refresh_token") or "").strip()
    if not client_id or not refresh:
        return None
    data = {"grant_type": "refresh_token", "refresh_token": refresh, "client_id": client_id}
    secret = (tokens.get("client_secret") or "").strip()
    if secret:
        data["client_secret"] = secret
    try:
        resp = await client.post(
            f"{BASE}/oauth/token/", data=data, headers={"User-Agent": USER_AGENT}
        )
        resp.raise_for_status()
        return resp.json().get("access_token")
    except Exception:  # noqa: BLE001
        return None


async def _renew_access_token(client: httpx.AsyncClient) -> str | None:
    """Best-effort renewal: email/password login first, then refresh grant."""
    return await _login_access_token(client) or await _refresh_grant_token(client)


def _sum(daily: dict) -> int:
    return int(sum(v for v in daily.values() if isinstance(v, (int, float))))


def _window(daily: dict) -> tuple[str | None, str | None]:
    keys = sorted(daily) if isinstance(daily, dict) else []
    return (keys[0], keys[-1]) if keys else (None, None)


def _snapshot(profile: dict, usage: dict) -> dict:
    current = (usage.get("current") or {}) if isinstance(usage, dict) else {}
    success = current.get("success") or {}
    error = current.get("error") or {}
    since, until = _window(success)
    return {
        "configured": True,
        "ok": True,
        "error": None,
        "email": profile.get("email"),
        "subscription_tier": profile.get("subscription_tier"),
        "credits": profile.get("credits"),
        "credits_expire_at": profile.get("credits_expire_at"),
        "promo_credits": profile.get("promo_credits"),
        "promo_credits_expire_at": profile.get("promo_credits_expire_at"),
        "promo_label": profile.get("promo_label"),
        "period": {"success": _sum(success), "error": _sum(error), "since": since, "until": until},
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


async def fetch_account_snapshot(
    client: httpx.AsyncClient | None = None, use_cache: bool = True
) -> dict:
    """Best-effort authoritative account snapshot (cached in-process)."""
    now = time.time()
    if use_cache and _cache["data"] and (now - _cache["ts"]) < CACHE_TTL:
        return _cache["data"]

    owns_client = client is None
    client = client or httpx.AsyncClient(timeout=15.0, follow_redirects=True)
    try:
        tokens = _tokens()
        token = (tokens.get("access_token") or "").strip()
        if not _unexpired(token):  # covers absent, malformed, and expired
            renewed = await _renew_access_token(client)
            if renewed and _unexpired(renewed):
                token = renewed
        if not _unexpired(token):
            any_configured = bool(
                (tokens.get("access_token") or "").strip()
                or (tokens.get("refresh_token") or "").strip()
                or ((tokens.get("email") or "").strip() and tokens.get("password"))
            )
            result = {
                "configured": any_configured,
                "ok": False,
                "error": "No valid Sectors OAuth token"
                if any_configured
                else "No Sectors OAuth token configured",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
        else:
            profile: dict = {}
            user_id = _jwt_claims(token).get("user_id")
            if user_id:
                resp = await client.get(f"{BASE}/auth/users/{user_id}/", headers=_headers(token))
                if resp.status_code == 200:
                    profile = resp.json()
            usage_resp = await client.get(f"{BASE}/api/usage/", headers=_headers(token))
            if usage_resp.status_code != 200:
                result = {
                    "configured": True,
                    "ok": False,
                    "error": f"usage HTTP {usage_resp.status_code}",
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                }
            else:
                result = _snapshot(profile, usage_resp.json())
    except Exception as exc:  # noqa: BLE001 — never break the usage page
        result = {
            "configured": True,
            "ok": False,
            "error": str(exc) or type(exc).__name__,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        if owns_client:
            await client.aclose()

    _cache["data"] = result
    _cache["ts"] = now
    return result
