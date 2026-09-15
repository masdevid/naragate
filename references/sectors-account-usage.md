# Sectors account usage (`/api/usage/`)

`GET https://api.sectors.app/api/usage/` (and `/api/credits/`) are **first-party
dashboard endpoints**, not part of the public v2 data API:

- The 64-char `SECTORS_API_KEY` authenticates `/v2/*` only. It does **not** work here.
- An authenticated web session cookie (from `POST /auth/oauth-login/`) does **not** work either.
- They require an OAuth2 **bearer token** from `api.sectors.app/oauth/`, issued via
  the authorization-code flow (the dashboard's own OAuth client). Only
  `authorization_code` and `refresh_token` grants are supported; `password` and
  `client_credentials` are rejected, and `api.sectors.app` has no dynamic client
  registration — so a registered `client_id` is mandatory.

Because the `client_id`/`redirect_uri` only exist inside the logged-in dashboard
(behind a Vercel bot checkpoint), capture them once from a real browser, then
refresh programmatically.

## One-time capture (real browser)

1. Log in at <https://sectors.app> (or <https://sectors.app/api>).
2. Open DevTools → **Network**.
3. Filter for `authorize` and copy the request URL:
   `https://api.sectors.app/oauth/authorize/?client_id=...&redirect_uri=...&response_type=code&scope=...`
   → record **`client_id`** and **`redirect_uri`**.
4. Filter for `token` and open the `POST https://api.sectors.app/oauth/token/` response:
   → record **`refresh_token`** (and **`client_secret`** only if the request body
   contained one — confidential client; public dashboards usually don't).

> The `client_id` is **not** obtainable from any user-scoped endpoint:
> `/auth/users/{id}/` returns only the profile, the refresh token JWT has no
> `aud`/`client_id` claim, and `/oauth/applications/` reports the user owns no
> apps (the dashboard client is first-party). It must come from the browser
> request above. Without it, `/oauth/token/` returns
> `{"error":"invalid_client"}` even for a valid refresh token — so the
> access token can only be used until it expires.

## Account endpoints (bearer)

| Endpoint | Method | Returns |
|----------|--------|---------|
| `/auth/users/{user_id}/` | GET | Profile: email, `subscription_tier`, `credits`, `promo_credits`, expiries |
| `/api/usage/` | GET | Per-day success/error call counts + current/previous period + credit balances |
| `/api/credits/` | POST | (not GET) |

`user_id` comes from the access-token JWT payload.

## Renewal: `POST /auth/token/` (no client_id needed)

The dashboard's own login mints tokens directly:

```bash
curl -s https://api.sectors.app/auth/token/ -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"…"}'
# => {"refresh":"eyJ…","access":"eyJ…"}
```

This bypasses the whole OAuth client problem (no `client_id`, no browser). The
backend uses `SECTORS_ACCOUNT_EMAIL` / `SECTORS_ACCOUNT_PASSWORD` to renew
automatically when the access token expires, so no manual capture is required.
A `username` field is rejected (`"email" is required`).

## Configure

Put the captured values in the repo `.env` (git-ignored):

```
SECTORS_OAUTH_CLIENT_ID=<client_id>
SECTORS_OAUTH_CLIENT_SECRET=<only if the client is confidential>
SECTORS_OAUTH_REFRESH_TOKEN=<refresh_token>
```

## View

No manual script is needed. The backend fetches this automatically
(`app/core/sectors_account.py`), caches it ~5 minutes, and exposes it at
`GET /api/v1/usage` — shown on the **Usage** page. The payload includes the
period's success/error call counts plus `credits`, `promo_credits`, and their
expiries.
