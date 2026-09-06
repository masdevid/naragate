---
name: score-generator
description: Compute the Reality Gap score (0-100) and verdict from the Evidence Judge assessment.
---

# Reality Gap Score Generator

Compute the Reality Gap score (0-100) and verdict from the Evidence Judge assessment.

## Trigger

Load this skill after the Evidence Judge has produced its unified assessment.

## Steps

1. Receive the Evidence Judge assessment
2. Compute applicable evidence dimensions based on claim category
3. Calculate the composite Reality Gap score (0-100)
4. Determine the verdict band
5. Generate an explainable summary
6. Return the final verdict

## Scoring Logic

### Dimension Weights by Category

- **Valuation claim**: valuation_gap (40%), peer_relative_gap (30%), evidence_confidence (30%)
- **Fundamental claim**: earnings_gap (40%), evidence_confidence (30%), market_momentum_gap (30%)
- **Market claim**: market_momentum_gap (50%), evidence_confidence (30%), valuation_gap (20%)
- **Peer comparison**: peer_relative_gap (50%), evidence_confidence (30%), valuation_gap (20%)

### Score to Verdict Mapping

- 0–30: **Contradicted**
- 31–60: **Mixed / Partially Supported**
- 61–80: **Supported**
- 81–100: **Strongly Supported**

## Output Schema

```json
{
  "claim_ticker": "string",
  "claim_category": "string",
  "reality_gap_score": "number",
  "verdict": "contradicted|mixed|supported|strongly_supported",
  "dimensions": {
    "dimension_name": "score"
  },
  "explanation": "string",
  "confidence": "number"
}
```

## Rules

- Only compute dimensions relevant to the claim category
- The score is NOT a buy/sell recommendation — it measures narrative-reality alignment
- The explanation must be human-readable and cite specific evidence
- Respect the harness-injected credit budget — no API calls at this stage