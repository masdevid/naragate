# Sectors account login & usage

These are **first-party account endpoints** on `api.sectors.app`, separate from
the public v2 data API (`/v2/*`). They are not part of the OpenAPI schema.

- The 64-char `SECTORS_API_KEY` authenticates `/v2/*` only — it does **not**
  work on `/auth/*` or `/api/usage/`.
- Account endpoints take an **OAuth2 bearer token** minted from credentials.

## Login: `POST /auth/token/` (email + password, no client_id)

```bash
curl -s https://api.sectors.app/auth/token/ -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"…"}'
# => {"refresh":"eyJ…","access":"eyJ…"}
```

This is the dashboard's own login. It needs **no `client_id`** and no browser —
which is why the app uses it. (`username` is rejected; the field must be
`email`.)

The `access`/`refresh` tokens are HS256 JWTs carrying `user_id`, `email`,
`subscription_tier`, `credits`, and `exp`.

## Account endpoints (bearer)

| Endpoint | Method | Returns |
|----------|--------|---------|
| `/auth/token/` | POST | `{refresh, access}` for `{email, password}` |
| `/auth/users/{user_id}/` | GET | Profile: email, `subscription_tier`, `credits`, `promo_credits`, expiries |
| `/api/usage/` | GET | Per-day success/error call counts + current/previous period + credit balances |
| `/api/credits/` | POST | (not GET) |

`user_id` comes from the access-token JWT payload.

## How the app uses it

- `backend/app/core/sectors_account.py` fetches `/auth/users/{id}/` +
  `/api/usage/` with a bearer token, caches the result ~5 minutes, and never
  raises (it degrades to "unavailable").
- It **self-renews**: `POST /auth/token/` with email/password first, then the
  OAuth `refresh_token` grant as a fallback.
- Exposed at `GET /api/v1/usage` and shown on the **Usage** page as the
  authoritative account card.
- **Login** (`/api/v1/auth/login`) stores the tokens and binds Sectors API-key
  ownership to the account **email** — not an IP address.

## Configure (`.env`, git-ignored)

```
SECTORS_ACCOUNT_EMAIL=you@example.com
SECTORS_ACCOUNT_PASSWORD=…
```

With these set, the account view heals automatically when the access token
expires. Optional overrides (normally unnecessary):

```
SECTORS_OAUTH_ACCESS_TOKEN=…    # used directly while unexpired
SECTORS_OAUTH_REFRESH_TOKEN=…
SECTORS_OAUTH_CLIENT_ID=…       # only for the OAuth refresh grant
SECTORS_OAUTH_CLIENT_SECRET=…
```

## Notes

- `/api/usage/` buckets a "day" as a **rolling 24h window** anchored at fetch
  time (all keys share the same clock time), not calendar days.
- The period `success`/`error` numbers are **call counts**, not credits
  (variable-cost endpoints bill more than one credit per call).
- Cloudflare fronts these endpoints and 1010-bans the default `python-urllib`/
  `httpx` signature, so requests send a normal browser User-Agent.
