# Skeptic Agent

Challenge a claim by re-interpreting the same evidence with a negation bias.

## Trigger

Load this skill after the validating agents (Valuation, Fundamental, Market) have produced their evidence. The Skeptic always runs.

## Steps

1. Receive the original Claim and all validating agent evidence
2. Do NOT fetch new data — re-interpret the existing Evidence Graph
3. Send the evidence to the LLM (Ollama at `https://dev.idh.am/v1`) with a negation-focused prompt
4. Identify counter-evidence that would disprove the claim
5. Assess the strength of the counter-argument
6. Return structured skeptical analysis

## Prompt

```
You are a skeptical financial analyst. Given the following evidence for a claim, 
find arguments that would DISPROVE or WEAKEN the claim.

Claim: {{assertion}} ({{ticker}})
Category: {{category}}
Evidence: {{evidence}}

Identify:
1. What evidence contradicts the claim?
2. What evidence is ambiguous or could be interpreted differently?
3. What missing evidence would change the verdict?
4. Overall skepticism score: 0-100 (higher = stronger counter-argument)
```

## Output Schema

```json
{
  "claim_ticker": "string",
  "counter_arguments": [
    {
      "point": "string",
      "evidence_ref": "string",
      "strength": "number"
    }
  ],
  "ambiguity_points": ["string"],
  "missing_evidence": ["string"],
  "skepticism_score": "number"
}
```

## Rules

- NEVER fetch new Sectors API data — this is the most cost-critical rule
- Re-interpret the same Evidence Graph that the validating agents used
- The skepticism score feeds into the Reality Gap calculation
- Use a faster Ollama model for efficiency