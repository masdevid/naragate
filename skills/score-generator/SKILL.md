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

### Direction-Aware Scoring

Each dimension is scored against the **claim's direction**, not in isolation:

- `above` (e.g. "expensive", "rising"): a positive premium / price move ALIGNS with the claim and raises support.
- `below` (e.g. "cheap", "falling"): a negative premium / price move ALIGNS with the claim and raises support.
- `neutral` / `between`: support peaks when the metric sits near parity (premium ≈ 0).

A positive premium must never be punished for an `above` claim — market interest does not make a stock numerically cheap.

### Decouple Valuation Claims from Sentiment & Flow Data

- VALUATION claims MUST be judged strictly on intrinsic/relative financial ratios (PE, PB, PS, forward PE vs subsector medians).
- Market flows, analyst consensus ("Buy" targets), and news sentiment MUST NOT dilute fundamental valuation evidence.
- For valuation claims, `evidence_confidence` counts only valuation and fundamental evidence — not news, corporate actions, or insider filings.

### Guardrail: 100% Agreement Locks the Verdict

- If EVERY available valuation ratio (PE, PB, PS, forward PE) agrees on direction AND that direction matches the claim → Verdict CANNOT be "Mixed". It is at least **Supported**.
- If EVERY available valuation ratio agrees on the OPPOSITE direction → Verdict CANNOT be "Mixed". It is at most **Contradicted**.
- A Mixed / Partially Supported verdict is only valid when the valuation ratios themselves point in conflicting directions.

### Contextualize Quality Premiums

- Explicitly separate numerical valuation from a qualitative premium. A strong banking-health profile (ROE, NIM, NPL, loan growth) can explain why a bank trades above its subsector median — this is a quality premium, NOT pure overvaluation.
- Quality premiums are surfaced as explanation notes; they never depress the score of a numerically-supported claim.

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
  "claim_direction": "above|below|between|neutral",
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
- Score every dimension against the claim's direction — never assume a claim is bullish (`above`)
- The score is NOT a buy/sell recommendation — it measures narrative-reality alignment
- The explanation must be human-readable and cite specific evidence
- Respect the harness-injected credit budget — no API calls at this stage