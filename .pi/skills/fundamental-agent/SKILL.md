# Fundamental Agent

Retrieve and analyze fundamental financial evidence from Sectors v2 for a given claim.

## Trigger

Load this skill when a claim has been classified as `fundamental` category and needs evidence retrieval.

## Steps

1. Receive the structured Claim object
2. Check the Evidence Graph for cached company report and quarterly financial data
3. If cache is stale or missing, fetch from Sectors v2 Company Report (financials section) and Quarterly Financials
4. Extract metrics: revenue, earnings, EPS, margins, ROE, ROA, debt metrics
5. Analyze trends over time (is earnings falling or improving?)
6. Return structured fundamental evidence

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
- Use quarterly financials for temporal reasoning — distinguish "profit fell" from "profit has fallen continuously"
- Respect the 1,600-credit budget
- Cache misses cost credits