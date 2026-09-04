# Evidence Judge

Aggregate evidence from all validating agents and the Skeptic, then produce a structured assessment.

## Trigger

Load this skill after all validating agents and the Skeptic have produced their output.

## Steps

1. Receive all agent outputs (Valuation, Fundamental, Market, Skeptic)
2. Aggregate evidence by claim category
3. Identify contradictions between agents
4. Cross-reference with the Skeptic's counter-arguments
5. Produce a unified evidence assessment
6. Return structured assessment for the Score Generator

## Tools

- Evidence Graph cache read
- No Sectors API calls

## Output Schema

```json
{
  "claim_ticker": "string",
  "claim_category": "string",
  "evidence_summary": {
    "valuation": "object | null",
    "fundamental": "object | null",
    "market": "object | null"
  },
  "contradictions": ["string"],
  "skeptic_challenges": ["string"],
  "evidence_confidence": "number",
  "applicable_dimensions": ["valuation_gap", "earnings_gap", "market_momentum_gap", "peer_relative_gap", "evidence_confidence"]
}
```

## Rules

- No Sectors API calls — pure aggregation
- Handle missing evidence gracefully (not all claims have all categories)
- Flag any contradictions between agents explicitly
- The evidence_confidence score (0-1) reflects how complete and consistent the evidence is