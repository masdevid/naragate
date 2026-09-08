import contextvars

from fastapi import Request

_current_ip: contextvars.ContextVar[str] = contextvars.ContextVar("client_ip", default="")


def set_client_ip(ip: str) -> None:
    """Bind the current request's client IP to the context.

    Sectors key resolution is per-IP, so every request that will trigger
    Sectors calls must set this before running the pipeline.
    """
    _current_ip.set(ip or "")


def get_client_ip() -> str:
    """The client IP of the current request ("" when none is set)."""
    return _current_ip.get()


def resolve_client_ip(request: Request) -> str:
    """Best-effort real client IP through Cloudflare -> Caddy -> nginx.

    Precedence: CF-Connecting-IP (set by Cloudflare) > X-Forwarded-For (first
    hop, added by the proxy chain) > X-Real-IP > direct socket peer.
    """
    headers = request.headers
    cf = headers.get("cf-connecting-ip")
    if cf:
        return cf.strip()
    xff = headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    xri = headers.get("x-real-ip")
    if xri and xri.strip():
        return xri.strip()
    if request.client:
        return request.client.host
    return ""