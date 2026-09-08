---
name: valuation-agent
description: Retrieve and analyze valuation evidence (PE, PB, PS, PCF) from Sectors v2 for a claim.
---

# Valuation Agent

Retrieve and analyze valuation evidence from Sectors v2 for a given claim.

## Trigger

Load this skill when a claim has been classified as `valuation` category and needs evidence retrieval.

## Steps

1. Receive the structured Claim object
2. **Ticker guardrail**: verify `claim.ticker` is a valid 4-letter code (`^[A-Z]{4}$`, not `UNKNOWN`/`null`/empty). If it is not valid, do NOT call Sectors — return an error and request a valid ticker.
3. Check the Evidence Graph for cached company report data for the ticker
4. If cache is stale or missing, fetch from Sectors v2 Company Report endpoint (valuation section)
5. Also fetch Subsector Report for peer median comparison
6. Extract valuation metrics: PE, PB, PS, PCF
7. Compare against subsector median
8. Return structured valuation evidence

## Tools

- Sectors v2 Company Report API (valuation section)
- Sectors v2 Subsector Report API
- Evidence Graph cache read/write

## Output Schema

```json
{
  "claim_ticker": "string",
  "category": "valuation",
  "metrics": {
    "pe": "number",
    "pb": "number",
    "ps": "number",
    "pcf": "number"
  },
  "subsector_median": {
    "pe": "number",
    "pb": "number",
    "ps": "number"
  },
  "premium_pct": {
    "pe": "number",
    "pb": "number",
    "ps": "number"
  },
  "evidence_freshness": "ISO8601 timestamp",
  "cache_hit": "boolean"
}
```

## Rules

- Always check cache first before making Sectors API calls
- Never call Sectors with an invalid ticker — validate the 4-letter code first; a 404 against a bad ticker still costs credits
- Use only the exact sections needed (valuation, subsector) — never fetch broad payloads
- Calculate premium as `(stock_metric - subsector_median) / subsector_median * 100`
- Respect the harness-injected credit budget — cache misses cost credits