"""The authenticated identity of the current request.

Sectors-key ownership is per **email** (the Sectors account), not per IP. The
login session cookie carries the email; a request middleware binds it to this
context var so deep pipeline code (which has no Request) can resolve the right
Sectors key via `sectors_api_key()`.
"""

from __future__ import annotations

import contextvars

from fastapi import Request

_current_email: contextvars.ContextVar[str] = contextvars.ContextVar("current_email", default="")


def set_current_email(email: str | None) -> None:
    _current_email.set((email or "").strip().lower())


def get_current_email() -> str:
    """The logged-in email for this request ("" when unauthenticated)."""
    return _current_email.get()


def email_from_request(request: Request) -> str:
    """Read the email from the signed session cookie ("" if absent)."""
    try:
        return (request.session.get("email") or "").strip().lower()
    except Exception:  # noqa: BLE001 — no session middleware / malformed cookie
        return ""
