# Claim Parser

Extract structured financial claims from Indonesian market narratives using an LLM.

## Trigger

Load this skill when the user provides a narrative statement (news article, headline, or user-typed claim) and needs it converted into a structured Claim object.

## Steps

1. Receive the narrative text as input
2. Send the text to the LLM (Ollama at `https://dev.idh.am/v1`) with the extraction prompt
3. Parse the LLM response into a structured Claim object
4. Validate the extracted claim has required fields
5. Return the structured Claim

## Extraction Prompt

```
Extract a structured financial claim from this narrative. Return JSON with:
- ticker: Indonesian stock ticker (e.g., BBCA, BBRI)
- category: one of valuation, fundamental, market, peer_comparison
- assertion: the core financial claim in English
- direction: above, below, between, or neutral
- time_window: optional (e.g., "1D", "7D", "30D", "quarterly")
- magnitude: optional numeric qualifier
- confidence: 0-1

Narrative: {{narrative}}
```

## Output Schema

```json
{
  "ticker": "string",
  "category": "valuation|fundamental|market|peer_comparison",
  "assertion": "string",
  "direction": "above|below|between|neutral",
  "time_window": "string | null",
  "magnitude": "number | null",
  "confidence": "number"
}
```

## Tools

- LLM call to Ollama (`https://dev.idh.am/v1`)
- No Sectors API calls needed at this stage

## Rules

- Always return a valid JSON object, never raw text
- If the ticker is not found in the curated universe, return it anyway but flag `ticker_valid: false`
- The assertion must be in English even if the narrative is in Indonesian
- Map Indonesian terms to English: `mahal` → valuation premium, `jeblok` → deterioration, `anjlok` → negative price change, `meroket` → strong growth
