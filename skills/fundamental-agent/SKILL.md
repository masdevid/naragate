---
name: fundamental-agent
description: Retrieve and analyze fundamental financial evidence (revenue, earnings, margins) from Sectors v2 for a claim.
---

# Fundamental Agent

Retrieve and analyze fundamental financial evidence from Sectors v2 for a given claim.

## Trigger

Load this skill when a claim has been classified as `fundamental` category and needs evidence retrieval.

## Steps

1. Receive the structured Claim object
2. **Ticker guardrail**: verify `claim.ticker` is a valid 4-letter code (`^[A-Z]{4}$`, not `UNKNOWN`/`null`/empty). If it is not valid, do NOT call Sectors — return an error and request a valid ticker.
3. Check the Evidence Graph for cached company report and quarterly financial data
4. If cache is stale or missing, fetch from Sectors v2 Company Report (financials section) and Quarterly Financials
5. Extract metrics: revenue, earnings, EPS, margins, ROE, ROA, debt metrics
6. Analyze trends over time (is earnings falling or improving?)
7. Return structured fundamental evidence

## Tools

- Sectors v2 Company Report API (financials section)
- Sectors v2 Quarterly Financials API
- Evidence Graph cache read/write

## Output Schema

```json
{
  "claim_ticker": "string",
  "category": "fundamental",
  "metrics": {
    "revenue": "number",
    "earnings": "number",
    "eps": "number",
    "gross_margin": "number",
    "roe": "number",
    "roa": "number",
    "debt_to_equity": "number"
  },
  "trend": {
    "revenue_trend": "improving|declining|stable",
    "earnings_trend": "improving|declining|stable",
    "quarters_analyzed": "number"
  },
  "evidence_freshness": "ISO8601 timestamp",
  "cache_hit": "boolean"
}
```

## Rules

- Always check cache first before making Sectors API calls
- Never call Sectors with an invalid ticker — validate the 4-letter code first; a 404 against a bad ticker still costs credits
- Use quarterly financials for temporal reasoning — distinguish "profit fell" from "profit has fallen continuously"
- Respect the harness-injected credit budget
- Cache misses cost credits