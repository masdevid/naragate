"""Email login for the app session.

Verifies the Sectors account credentials via `POST /auth/token/`, then stores
the email in a signed session cookie. Sectors API-key ownership is resolved
from this email (`sectors_config.key_for_email`), replacing the old IP model.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core import sectors_config
from app.core.identity import email_from_request
from app.core.sectors_account import login_with_password

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str
    # Optional: bind the Sectors API key now, or leave it to Settings later.
    api_key: str | None = None


class AuthStatus(BaseModel):
    authenticated: bool
    email: str | None = None
    subscription_tier: str | None = None
    credits: int | None = None
    promo_credits: int | None = None
    key_bound: bool = False


def _status(request: Request) -> AuthStatus:
    email = email_from_request(request)
    if not email:
        return AuthStatus(authenticated=False)
    key = sectors_config.key_for_email(email)
    return AuthStatus(authenticated=True, email=email, key_bound=bool(key))


@router.post("/login")
async def login(request: Request, req: LoginRequest) -> AuthStatus:
    email = (req.email or "").strip().lower()
    if not email or not req.password:
        raise HTTPException(status_code=422, detail="Email and password are required.")

    result = await login_with_password(email, req.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid Sectors email or password.")

    profile = result.get("profile") or {}
    request.session["email"] = email
    # Persist tokens so the account-usage block can self-renew, and bind
    # ownership of the Sectors API key to this email.
    sectors_config.store_oauth_login(email, req.password, result.get("access"), result.get("refresh"))
    data = sectors_config._load_runtime()
    data["sectors_key_owner_email"] = email
    sectors_config._save_runtime(data)

    # Optional API key at login; anything masked/blank is ignored (set later).
    api_key = (req.api_key or "").strip()
    if api_key and "..." not in api_key and "••••" not in api_key:
        sectors_config.bind_key_to_email(email, api_key)

    return AuthStatus(
        authenticated=True,
        email=email,
        subscription_tier=profile.get("subscription_tier"),
        credits=profile.get("credits"),
        promo_credits=profile.get("promo_credits"),
        key_bound=bool(sectors_config.key_for_email(email)),
    )


@router.post("/logout")
async def logout(request: Request) -> AuthStatus:
    request.session.pop("email", None)
    return AuthStatus(authenticated=False)


@router.get("/me")
async def me(request: Request) -> AuthStatus:
    return _status(request)
