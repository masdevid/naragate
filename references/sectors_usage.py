#!/usr/bin/env python3
"""Fetch Sectors first-party account usage (`/api/usage/`, `/api/credits/`).

These dashboard endpoints need an OAuth2 bearer token — the v2 API key and the
web session cookie do not work. Capture the client id + refresh token once from
a logged-in browser, put them in the repo `.env`, then run this script.

See references/sectors-account-usage.md for the capture steps and why this is
separate from the public data API.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
BASE = "https://api.sectors.app"
ACCOUNT_PATHS = ("/api/usage/",)  # /api/credits/ is POST-only; balances come from usage
# Cloudflare fronts the first-party endpoints and 1010-bans the default
# python-urllib signature; send a normal browser UA (the v2 data API doesn't care).
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def load_env() -> None:
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _post_form(path: str, data: dict) -> dict:
    req = urllib.request.Request(
        BASE + path,
        data=urllib.parse.urlencode(data).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def refresh_access_token(client_id: str, refresh_token: str, client_secret: str) -> dict:
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
    }
    if client_secret:
        data["client_secret"] = client_secret
    return _post_form("/oauth/token/", data)


def fetch(path: str, access_token: str) -> tuple[int, object]:
    req = urllib.request.Request(
        BASE + path,
        headers={"Authorization": f"Bearer {access_token}", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as exc:  # noqa: BLE001 — surface status + body
        return exc.code, exc.read().decode()[:300]


def jwt_claims(token: str) -> dict:
    """Best-effort decode of a JWT payload; {} if unparseable."""
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except Exception:  # noqa: BLE001
        return {}


def jwt_exp(token: str) -> int | None:
    exp = jwt_claims(token).get("exp")
    return int(exp) if isinstance(exp, (int, float)) else None


def resolve_access_token() -> str | None:
    """Prefer a still-valid SECTORS_OAUTH_ACCESS_TOKEN; else refresh one."""
    access = os.environ.get("SECTORS_OAUTH_ACCESS_TOKEN", "").strip()
    if access:
        exp = jwt_exp(access)
        if exp is None or exp > int(time.time()):
            return access
        print("SECTORS_OAUTH_ACCESS_TOKEN expired; attempting refresh...", file=sys.stderr)

    client_id = os.environ.get("SECTORS_OAUTH_CLIENT_ID", "").strip()
    client_secret = os.environ.get("SECTORS_OAUTH_CLIENT_SECRET", "").strip()
    refresh_token = os.environ.get("SECTORS_OAUTH_REFRESH_TOKEN", "").strip()
    if not client_id or not refresh_token:
        print(
            "No valid access token and no refresh credentials. Set "
            "SECTORS_OAUTH_ACCESS_TOKEN, or SECTORS_OAUTH_CLIENT_ID + "
            "SECTORS_OAUTH_REFRESH_TOKEN, in .env (see references/sectors-account-usage.md).",
            file=sys.stderr,
        )
        return None

    try:
        token = refresh_access_token(client_id, refresh_token, client_secret)
    except urllib.error.HTTPError as exc:  # noqa: BLE001
        print(f"token request failed: HTTP {exc.code} {exc.read().decode()[:300]}", file=sys.stderr)
        return None
    except Exception as exc:  # noqa: BLE001
        print(f"token request failed: {exc}", file=sys.stderr)
        return None

    access_token = token.get("access_token")
    if not access_token:
        print(f"no access_token in response: {token}", file=sys.stderr)
        return None
    if token.get("refresh_token") and token["refresh_token"] != refresh_token:
        print(f"NOTE: rotated refresh_token — update .env:\n  SECTORS_OAUTH_REFRESH_TOKEN={token['refresh_token']}")
    return access_token


PROFILE_FIELDS = (
    "id", "email", "subscription_tier", "credits", "credits_expire_at",
    "promo_credits", "promo_credits_expire_at", "promo_label",
)


def main() -> int:
    load_env()
    access_token = resolve_access_token()
    if not access_token:
        return 2

    claims = jwt_claims(access_token)
    print(f"token: user_id={claims.get('user_id')} exp={claims.get('exp')}")

    user_id = claims.get("user_id")
    if user_id:
        status, body = fetch(f"/auth/users/{user_id}/", access_token)
        print(f"=== GET /auth/users/{user_id}/ -> HTTP {status} ===")
        if isinstance(body, dict):
            print(json.dumps({k: body.get(k) for k in PROFILE_FIELDS}, indent=2))
        else:
            print(body)

    for path in ACCOUNT_PATHS:
        status, body = fetch(path, access_token)
        print(f"=== GET {path} -> HTTP {status} ===")
        print(json.dumps(body, indent=2) if isinstance(body, (dict, list)) else body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
