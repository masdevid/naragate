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


def dev_ips() -> list[str]:
    """IPs that are always authorized to use the shared Sectors key.

    Development/test convenience: a known IP (e.g. "127.0.0.1" or the Docker
    bridge gateway "172.21.0.1" seen when hitting the app locally) bypasses the
    allowlist so local runs and e2e tests never trip over owner gating.
    Configure via SECTORS_DEV_IPS (comma-separated).
    """
    raw = settings.SECTORS_DEV_IPS
    return [ip.strip() for ip in raw.split(",") if ip and ip.strip()]


def _migrate_runtime(data: dict) -> dict:
    """Fold the legacy per-IP registry into the shared-key allowlist model.

    Legacy identity:
        sectors_keys_by_ip: {ip: key, ...}   (each IP bound its own key copy)
        sectors_key_bound_to: owner ip marker (first ip that bound a key)
    New identity:
        sectors_api_key            one shared key (owner's copy wins)
        sectors_key_owner_ip       the IP that first bound the key
        sectors_authorized_ips     the IPs allowed to use the shared key

    The first IP to bind acts as the owner; it is the only session that can add
    further IPs. Migration is idempotent; the legacy registry is retired from
    the loaded copy on each read (the file is cleaned on the next save).
    """
    registry = data.get("sectors_keys_by_ip")
    if registry:
        ip_list = list(registry.keys())
        owner = (
            data.get("sectors_key_owner_ip")
            or data.get("sectors_key_bound_to")
            or (ip_list[0] if ip_list else None)
        )
        if owner and owner in registry:
            data.setdefault("sectors_api_key", registry[owner])
        elif owner:
            data.setdefault("sectors_api_key", "")
        authorized = data.get("sectors_authorized_ips") or []
        for ip in ip_list:
            if ip not in authorized:
                authorized.append(ip)
        data["sectors_authorized_ips"] = authorized
        data["sectors_key_owner_ip"] = owner
        data.pop("sectors_keys_by_ip", None)
    elif data.get("sectors_key_owner_ip"):
        owner = data["sectors_key_owner_ip"]
        authorized = data.get("sectors_authorized_ips") or []
        if owner not in authorized:
            authorized.append(owner)
        data["sectors_authorized_ips"] = authorized
    return data


def sectors_ip_authorized(data: dict, ip: str) -> bool:
    """Whether an IP may use the shared Sectors key.

    Authorized when: no request context (server-side calls), the IP is a dev IP,
    per-IP enforcement is OFF, the IP is the owner, or it is on the allowlist
    that the owner maintains.
    """
    if not ip:
        return True
    if ip in dev_ips():
        return True
    if not sectors_per_ip_enforced(data):
        return True
    if data.get("sectors_key_owner_ip") == ip:
        return True
    return ip in (data.get("sectors_authorized_ips") or [])


def sectors_per_ip_enforced(data: dict) -> bool:
    """Whether the per-IP Sectors allowlist is active for the current config.

    Defaults to OFF: a key configured at the server level is shared by every
    client. Explicitly opt in via the runtime setting or SECTORS_ENFORCE_PER_IP.
    """
    return bool(data.get("sectors_enforce_per_ip", settings.SECTORS_ENFORCE_PER_IP))


def sectors_key_for_ip(data: dict, ip: str) -> str:
    """The shared Sectors key for an IP ('' when the IP is not authorized)."""
    if sectors_ip_authorized(data, ip):
        return data.get("sectors_api_key") or _env_key()
    return ""


def sectors_oauth_tokens() -> dict:
    """Resolve Sectors first-party OAuth tokens.

    Runtime settings (set via the Settings UI) take precedence over env, so a
    pasted token updates immediately without a redeploy.
    """
    data = _migrate_runtime(_load_runtime())
    return {
        "access_token": data.get("sectors_oauth_access_token") or settings.SECTORS_OAUTH_ACCESS_TOKEN,
        "refresh_token": data.get("sectors_oauth_refresh_token") or settings.SECTORS_OAUTH_REFRESH_TOKEN,
        "client_id": data.get("sectors_oauth_client_id") or settings.SECTORS_OAUTH_CLIENT_ID,
        "client_secret": data.get("sectors_oauth_client_secret") or settings.SECTORS_OAUTH_CLIENT_SECRET,
        "email": data.get("sectors_oauth_email") or settings.SECTORS_ACCOUNT_EMAIL,
        "password": data.get("sectors_oauth_password") or settings.SECTORS_ACCOUNT_PASSWORD,
    }


def sectors_api_key() -> str:
    """Resolve the Sectors API key for the current request's client IP.

    One shared key owned by the first IP that bound it (see CONTEXT.md: Credit).
    The owner can authorize more IPs via Settings. Dev IPs bypass the allowlist.
    A request with no IP context (health probes, server-side calls) falls back to
    the runtime/startup key.
    """
    data = _migrate_runtime(_load_runtime())
    return sectors_key_for_ip(data, get_client_ip())