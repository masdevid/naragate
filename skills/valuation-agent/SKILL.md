---
name: valuation-agent
description: Retrieve and analyze valuation evidence (PE, PB, PS, PCF) from Sectors v2 for a claim.
---

# Valuation Agent

Retrieve and analyze valuation evidence from Sectors v2 for a given claim.

## Trigger

Load this skill when a claim has been classified as `valuation` category and needs evidence retrieval.

## Directives

### Decouple Valuation Claims from Sentiment & Flow Data

- VALUATION claims MUST be judged strictly on intrinsic/relative financial ratios.
- Market flows, analyst consensus ("Buy" target prices), and short-term capital-flow headlines MUST NOT dilute fundamental valuation evidence.
- A stock receiving high institutional interest does not make it numerically cheap — report the ratios as they are.

### Data Coverage Enforcement (banking / financial-sector tickers)

- For banking-health context, ALSO extract ROE, NIM, NPL, and loan growth from the financials section of the company report (same cache payload — no extra Sectors call).
- These indicators are reported alongside the price ratios as `health` context; they do not replace the ratio-based verdict.
- When a banking indicator is not available in the payload, record it as missing rather than guessing a value.

### Contextualize Quality Premiums

- Explicitly separate numerical valuation from a qualitative premium. A strong ROE / balance sheet explains a premium above the subsector median; it is a quality premium, not evidence of "cheapness" or "expensiveness" by itself.

## Steps

1. Receive the structured Claim object
2. **Ticker guardrail**: verify `claim.ticker` is a valid 4-letter code (`^[A-Z]{4}$`, not `UNKNOWN`/`null`/empty). If it is not valid, do NOT call Sectors — return an error and request a valid ticker.
3. Check the Evidence Graph for cached company report data for the ticker
4. If cache is stale or missing, fetch from Sectors v2 Company Report endpoint (valuation section)
5. Also fetch Subsector Report for peer median comparison
6. Extract valuation metrics: PE, PB, PS, PCF, forward PE
7. Compare against subsector median (premium = `(stock - median) / median * 100`)
8. Extract banking-health indicators (ROE, NIM, NPL, loan growth) from the financials section for context
9. Return structured valuation evidence

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
    "pcf": "number",
    "forward_pe": "number"
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
  "health": {
    "roe": "number",
    "roa": "number",
    "net_profit_margin": "number",
    "nim": "number",
    "npl": "number",
    "loan_growth": "number"
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
- Banking-health indicators are context, not substitutes for price ratios — do not let an attractive ROE override a numerically-expensive reading
- Respect the harness-injected credit budget — cache misses cost credits