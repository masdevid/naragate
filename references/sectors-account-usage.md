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

## Configure

Put the captured values in the repo `.env` (git-ignored):

```
SECTORS_OAUTH_CLIENT_ID=<client_id>
SECTORS_OAUTH_CLIENT_SECRET=<only if the client is confidential>
SECTORS_OAUTH_REFRESH_TOKEN=<refresh_token>
```

## Fetch

```
python3 references/sectors_usage.py
```

The script uses `SECTORS_OAUTH_ACCESS_TOKEN` directly while it is unexpired, and
otherwise refreshes it from the refresh token, then prints `/api/usage/`. The
usage payload includes the running success/error counts plus `credits`,
`promo_credits`, and their expiry. (`/api/credits/` is POST-only.) Refresh
tokens often rotate — if the response includes a new `refresh_token`, update
`.env`.

Raw equivalent:

```bash
source /dev/stdin <<< "$(grep -E '^SECTORS_OAUTH_' .env | sed 's/^/export /')"
ACCESS=$(curl -s https://api.sectors.app/oauth/token/ \
  -d grant_type=refresh_token -d "refresh_token=$SECTORS_OAUTH_REFRESH_TOKEN" \
  -d "client_id=$SECTORS_OAUTH_CLIENT_ID" | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
curl -s https://api.sectors.app/api/usage/ -H "Authorization: Bearer $ACCESS"
```
