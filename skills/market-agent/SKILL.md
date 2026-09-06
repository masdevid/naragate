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
2. Check the Evidence Graph for cached daily transaction data
3. If cache is stale or missing, fetch from Sectors v2 Daily Transaction API
4. Extract price and volume data across time windows (1D, 7D, 30D)
5. Compare against the claim's directional assertion
6. Return structured market evidence

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
- Map Indonesian terms: `anjlok`/`jeblok` → negative price change, `meroket`/`meledak` → strong positive change
- Respect the harness-injected credit budget
- Daily transaction data TTL: 1 hour