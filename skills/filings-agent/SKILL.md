---
name: filings-agent
description: Retrieve and analyze insider trading filings from Sectors v2 for a claim.
---

# Filings Agent

Retrieve and analyze insider trading filings from Sectors v2 for a given claim.

## Trigger

Load this skill when a claim has been classified as `insider_trading` category and needs evidence retrieval.

## Steps

1. Receive the structured Claim object
2. Check the Evidence Graph for cached filings data for the ticker
3. If cache is stale or missing, fetch from Sectors v2 Filings endpoint (insider_trade type)
4. Parse filing records: date, insider name, title, transaction type, shares, price, value
5. Compute net bias: sum of buy volume vs sell volume across recent filings
6. Generate summary of insider activity pattern
7. Return structured filings evidence

## Tools

- Sectors v2 Filings API (insider_trade type)
- Evidence Graph cache read/write

## Output Schema

```json
{
  "claim_ticker": "string",
  "category": "insider_trading",
  "filings": [
    {
      "date": "string",
      "insider_name": "string",
      "insider_title": "string",
      "transaction_type": "string",
      "shares": "number",
      "price": "number",
      "total_value": "number"
    }
  ],
  "summary": "string",
  "recent_bias": "string",
  "evidence_freshness": "ISO8601 timestamp",
  "cache_hit": "boolean"
}
```

## Rules

- Always check cache first before making Sectors API calls
- Fetch only insider_trade type — ignore annual_report, prospectus
- Compute recent_bias from last 10 filings maximum
- Respect the harness-injected credit budget — cache misses cost credits
