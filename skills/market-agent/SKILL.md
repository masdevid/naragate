---
name: market-agent
description: Retrieve and analyze market performance evidence (price, volume, volatility) from Sectors v2 for a claim.
---

# Market Agent

Retrieve and analyze market performance evidence from Sectors v2 for a given claim.

## Trigger

Load this skill when a claim has been classified as `market` category and needs evidence retrieval.

## Steps

1. Receive the structured Claim object
2. **Ticker guardrail**: verify `claim.ticker` is a valid 4-letter code (`^[A-Z]{4}$`, not `UNKNOWN`/`null`/empty). If it is not valid, do NOT call Sectors — return an error and request a valid ticker.
3. Check the Evidence Graph for cached daily transaction data
4. If cache is stale or missing, fetch from Sectors v2 Daily Transaction API
5. Extract price and volume data across time windows (1D, 7D, 30D)
6. Compare against the claim's directional assertion
7. Return structured market evidence

## Tools

- Sectors v2 Daily Transaction API
- Evidence Graph cache read/write

## Output Schema

```json
{
  "claim_ticker": "string",
  "category": "market",
  "performance": {
    "1d": { "price_change_pct": "number", "volume": "number" },
    "7d": { "price_change_pct": "number", "volume": "number" },
    "30d": { "price_change_pct": "number", "volume": "number" }
  },
  "volatility": "number",
  "evidence_freshness": "ISO8601 timestamp",
  "cache_hit": "boolean"
}
```

## Rules

- Always check cache first before making Sectors API calls
- Never call Sectors with an invalid ticker — validate the 4-letter code first; a 404 against a bad ticker still costs credits
- Map Indonesian terms: `anjlok`/`jeblok` → negative price change, `meroket`/`meledak` → strong positive change
- Respect the harness-injected credit budget
- Daily transaction data TTL: 1 hour