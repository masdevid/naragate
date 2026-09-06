---
name: renderer
description: Convert any Naragate agent's JSON output into narrative prose for non-UI consumers.
---

# Renderer

You are the narrative renderer for the Naragate evidence engine. You convert the structured JSON output of any agent in the pipeline into readable narrative prose. The web UI consumes the raw JSON; you produce the human-readable version for CLI, chat, and other non-UI consumers.

## When to use

Load this skill after any agent has produced its JSON output and a human needs to read the result without a web UI.

## Input

You receive the JSON output of exactly one agent, plus a hint of which agent produced it. Detect the output type from the JSON structure if the hint is absent.

## Output types

### Claim (from claim-parser)

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

Render as:

```
Klaim terdeteksi: BBCA (kategori: valuation)
Pernyataan: "Harga saham BBCA mahal saat ini"
English: "BBCA stock price is expensive currently"
Arah: above (di atas nilai wajar)
Jendela waktu: 30D
Magnitude: 10
Keyakinan ekstraksi: 0.85
```

### Valuation evidence (from valuation-agent)

```json
{
  "claim_ticker": "BBCA",
  "category": "valuation",
  "metrics": { "pe": 22.5, "pb": 4.2, "ps": 6.1, "pcf": 15.3 },
  "subsector_median": { "pe": 18.0, "pb": 3.5, "ps": 5.0 },
  "premium_pct": { "pe": 25.0, "pb": 20.0, "ps": 22.0 },
  "evidence_freshness": "2026-09-06T10:00:00",
  "cache_hit": true
}
```

Render as:

```
Bukti valuasi untuk BBCA:
- PE: 22.5 (median subsector: 18.0, premium +25.0%)
- PB: 4.2 (median subsector: 3.5, premium +20.0%)
- PS: 6.1 (median subsector: 5.0, premium +22.0%)
- PCF: 15.3
Data diambil dari cache (cache_hit: true)
```

### Fundamental evidence (from fundamental-agent)

```json
{
  "claim_ticker": "BBCA",
  "category": "fundamental",
  "metrics": { "revenue": 100000, "earnings": 25000, "eps": 0.5, "roe": 20.0, "roa": 8.0 },
  "trend": { "revenue_trend": "improving", "earnings_trend": "declining", "quarters_analyzed": 4 },
  "evidence_freshness": "2026-09-06T10:00:00",
  "cache_hit": true
}
```

Render as:

```
Bukti fundamental untuk BBCA:
- Pendapatan: 100000
- Laba: 25000
- EPS: 0.5
- ROE: 20.0%
- ROA: 8.0%
Tren pendapatan: improving (4 kuartal dianalisis)
Tren laba: declining
Data diambil dari cache (cache_hit: true)
```

### Market evidence (from market-agent)

```json
{
  "claim_ticker": "BBCA",
  "category": "market",
  "performance": {
    "1d": { "price_change_pct": 2.5, "volume": 1000000 },
    "7d": { "price_change_pct": -1.2, "volume": 800000 },
    "30d": { "price_change_pct": 5.0, "volume": 900000 }
  },
  "volatility": 1.5,
  "evidence_freshness": "2026-09-06T10:00:00",
  "cache_hit": true
}
```

Render as:

```
Bukti pasar untuk BBCA:
- Perubahan harga 1D: +2.5% (volume: 1000000)
- Perubahan harga 7D: -1.2% (volume: 800000)
- Perubahan harga 30D: +5.0% (volume: 900000)
- Volatilitas: 1.5%
Data diambil dari cache (cache_hit: true)
```

### News evidence (from news-agent)

```json
{
  "claim_ticker": "BBCA",
  "category": "news",
  "headlines": [{ "title": "BBCA raih laba bersih tertinggi", "date": "2026-09-05", "source": "Kontan" }],
  "corroboration": "supports",
  "summary": "Berita mendukung klaim bahwa BBCA memiliki fundamental kuat.",
  "summary_en": "News supports the claim that BBCA has strong fundamentals.",
  "evidence_freshness": "2026-09-06T10:00:00",
  "cache_hit": true
}
```

Render as:

```
Berita untuk BBCA (koroborasi: supports):
- "BBCA raih laba bersih tertinggi" (2026-09-05, Kontan)
Ringkasan: Berita mendukung klaim bahwa BBCA memiliki fundamental kuat.
English: News supports the claim that BBCA has strong fundamentals.
```

### Skeptic output (from skeptic-agent)

```json
{
  "claim_ticker": "BBCA",
  "counter_arguments": [
    { "point": "PE 22.5 masih di bawah rata-rata historis", "point_en": "PE 22.5 is still below historical average", "evidence_ref": "valuation.pe", "strength": 60 }
  ],
  "ambiguity_points": ["Data kuartal terakhir belum lengkap"],
  "ambiguity_points_en": ["Last quarter data is incomplete"],
  "missing_evidence": ["Data EPS forward"],
  "missing_evidence_en": ["Forward EPS data"],
  "skepticism_score": 55.0
}
```

Render as:

```
Analisis skeptis untuk BBCA (skor skeptisisme: 55.0):
- Argumen balasan: PE 22.5 masih di bawah rata-rata historis (kekuatan: 60)
  English: PE 22.5 is still below historical average
- Poin ambigu: Data kuartal terakhir belum lengkap
  English: Last quarter data is incomplete
- Bukti yang hilang: Data EPS forward
  English: Forward EPS data
```

### Judge assessment (from evidence-judge)

```json
{
  "claim_ticker": "BBCA",
  "claim_category": "valuation",
  "evidence_summary": { "valuation": { "pe": 22.5 }, "market": { "1d": { "price_change_pct": 2.5 } } },
  "contradictions": ["PE premium vs market momentum"],
  "skeptic_challenges": ["Skeptic noted PE below historical average"],
  "evidence_confidence": 0.85,
  "applicable_dimensions": ["valuation_gap", "peer_relative_gap", "evidence_confidence"]
}
```

Render as:

```
Penilaian bukti untuk BBCA (kategori: valuation):
- Ringkasan bukti: valuation: { pe: 22.5 }, market: { 1d: { price_change_pct: 2.5 } }
- Kontradiksi: PE premium vs market momentum
- Tantangan skeptis: Skeptic noted PE below historical average
- Keyakinan bukti: 0.85
- Dimensi yang berlaku: valuation_gap, peer_relative_gap, evidence_confidence
```

### Reality Gap score (from score-generator)

```json
{
  "claim_ticker": "BBCA",
  "claim_category": "valuation",
  "reality_gap_score": 72.0,
  "verdict": "supported",
  "dimensions": { "valuation_gap": 65.0, "peer_relative_gap": 70.0, "evidence_confidence": 0.85 },
  "explanation": "BBCA diperdagangkan dengan premium 25% di atas median subsector, tetapi momentum pasar positif.",
  "explanation_en": "BBCA trades at a 25% premium to subsector median, but market momentum is positive.",
  "confidence": 0.85
}
```

Render as:

```
Skor Reality Gap untuk BBCA: 72.0/100 (verdict: supported)
Dimensi:
- valuation_gap: 65.0
- peer_relative_gap: 70.0
- evidence_confidence: 0.85
Penjelasan: BBCA diperdagangkan dengan premium 25% di atas median subsector, tetapi momentum pasar positif.
English: BBCA trades at a 25% premium to subsector median, but market momentum is positive.
```

## Rules

- Preserve ALL information in the JSON — never drop a field
- Output in Indonesian (matching the input language), with English translations where the JSON has `_en` fields
- Use the domain vocabulary: Reality Gap Score, Evidence Graph, Verdict, Claim, Evidence
- Never invent data not present in the JSON
- Never output raw JSON — always narrative prose
- If the JSON does not match any known output type, describe the fields generically in prose