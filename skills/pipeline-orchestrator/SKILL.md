---
name: pipeline-orchestrator
description: Define the Naragate Reality Gap pipeline as a standalone 5-stage workflow any harness can invoke.
---

# Pipeline Orchestrator

You are the orchestrator for the Naragate Reality Gap pipeline. You define and drive the agent sequence that turns an Indonesian market narrative into a Reality Gap score. This skill is harness-agnostic: any LLM/agent harness can invoke it without the Python backend.

## Pipeline stages

Run these stages in order. Each stage consumes the previous stage's JSON output.

### Stage 1: claim-parser

Invoke the `claim-parser` skill with the raw narrative text.

Input: the narrative (Indonesian market commentary).

Output: a structured Claim JSON:

```json
{
  "ticker": "BBCA",
  "category": "valuation",
  "assertion": "Harga saham BBCA mahal saat ini",
  "assertion_en": "BBCA stock price is expensive currently",
  "direction": "above",
  "time_window": "30D",
  "magnitude": 10,
  "confidence": 0.85
}
```

### Stage 2: evidence agents

Select the evidence agent by the claim's `category`:

- `valuation` → `valuation-agent`
- `fundamental` → `fundamental-agent`
- `market` → `market-agent`
- `peer_comparison` → `valuation-agent` (peer comparison uses valuation evidence)

Also run `news-agent` to corroborate or contradict the claim via recent headlines.

Each evidence agent reads the Evidence Graph cache first (via `evidence_cache_get`), fetches from Sectors v2 only if stale or missing, and writes back via `evidence_cache_merge`.

Output: an Evidence object per agent, keyed by category:

```json
{
  "valuation": { "claim_ticker": "BBCA", "category": "valuation", "metrics": {}, "subsector_median": {}, "premium_pct": {}, "evidence_freshness": "...", "cache_hit": true },
  "news": { "claim_ticker": "BBCA", "category": "news", "headlines": [], "corroboration": "neutral", "summary": "...", "evidence_freshness": "...", "cache_hit": true }
}
```

### Stage 3: skeptic

Invoke the `skeptic-agent` skill with the claim and all evidence.

Output: a Skeptic JSON with counter-arguments, ambiguity points, missing evidence, and a skepticism score:

```json
{
  "claim_ticker": "BBCA",
  "counter_arguments": [],
  "ambiguity_points": [],
  "missing_evidence": [],
  "skepticism_score": 55.0
}
```

### Stage 4: evidence-judge

Invoke the `evidence-judge` skill with the claim, all evidence, and the skeptic output.

Output: an assessment JSON:

```json
{
  "claim_ticker": "BBCA",
  "claim_category": "valuation",
  "evidence_summary": {},
  "contradictions": [],
  "skeptic_challenges": [],
  "evidence_confidence": 0.85,
  "applicable_dimensions": []
}
```

### Stage 5: score-generator

Invoke the `score-generator` skill with the assessment and the skeptic's skepticism score.

Output: the Reality Gap score JSON:

```json
{
  "claim_ticker": "BBCA",
  "claim_category": "valuation",
  "reality_gap_score": 72.0,
  "verdict": "supported",
  "dimensions": {},
  "explanation": "...",
  "confidence": 0.85
}
```

## Data flow

```
narrative
   │
   ▼
claim-parser ──► Claim JSON
   │
   ▼
evidence agents (category-based + news + corporate_actions) ──► Evidence JSON
   │
   ▼
skeptic ──► Skeptic JSON
   │
   ▼
evidence-judge ──► Assessment JSON
   │
   ▼
score-generator ──► Reality Gap Score JSON
```

## Output modes

- **Web UI**: emit each stage's JSON as-is (the UI renders it).
- **CLI / no-UI**: after each stage, chain the `renderer` skill to convert the JSON into narrative prose.

## Rules

- Run stages strictly in order; never skip a stage
- Pass the previous stage's JSON output as input to the next stage
- The claim's `category` determines which evidence agent runs in Stage 2
- Always run news-agent in Stage 2 regardless of category
- Preserve the Evidence Graph cache discipline: read before fetch, merge after fetch
- Do not hardcode Sectors API keys, credit budgets, or LLM providers — the harness injects those