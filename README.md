# Naragate

**AI evidence engine that detects financial claims in Indonesian market narratives and verifies them against real financial data.**

---

## Problem

Indonesian investors consume market narratives daily — from WhatsApp groups, Twitter threads, and news headlines. Claims like *"BBCA labanya jeblok"* (BBCA's profits collapsed) or *"TLKM bakal meroket"* (TLKM will skyrocket) spread fast, but verifying them requires manually checking financial reports, valuation metrics, and market data.

Most investors don't have time for this. They either trust the narrative or ignore it.

## Solution

Naragate analyzes any Indonesian market narrative in real-time and produces a **Reality Gap Score** — a 0–100 measure of how strongly the financial evidence aligns with the claim.

**Input:**
> "BBCA labanya jeblok, PE-nya masih mahal banget, mending pindah ke BBRI"

**Output:**
- Extracted claims: "BBCA profits collapsed", "BBCA PE is expensive", "BBRI is better"
- Evidence: Actual PE ratios, profit margins, quarterly financials
- Verdict: **Mixed (45/100)** — profits declined but PE is within sector average

## Who It's For

| User | How They Use It |
|------|-----------------|
| **Retail investors** | Paste a WhatsApp message, get instant fact-check |
| **Financial analysts** | Verify claims before including in reports |
| **Compliance teams** | Screen social media for misleading financial claims |
| **Hackathon judges** | See multi-agent AI orchestration in action |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Naragate Stack                        │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ Angular  │  │ FastAPI  │  │ Pi Agent │  │ Redis  │ │
│  │ Frontend │→ │ Backend  │→ │ Pipeline │  │ Cache  │ │
│  │ (nginx)  │  │ (SQLite) │  │ (7 agents│  │        │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
│                       │                                 │
│              ┌────────┴────────┐                        │
│              │   Sectors v2    │  ← Financial data      │
│              │   (1,600 cr.)   │                        │
│              └─────────────────┘                        │
└─────────────────────────────────────────────────────────┘
                       │
                ┌──────┴──────┐
                │   Ollama    │  ← User's own LLM
                │  (external) │     (or OpenRouter, etc.)
                └─────────────┘
```

### Multi-Agent Pipeline

1. **Claim Parser** — Extracts structured claims from Indonesian text
2. **Valuation Agent** — Retrieves PE, PB, PS, PCF metrics
3. **Fundamental Agent** — Retrieves revenue, earnings, margins
4. **Market Agent** — Retrieves price, volume, volatility data
5. **Skeletal Agent** — Challenges claims with negation bias
6. **Evidence Judge** — Aggregates evidence from all agents
7. **Score Generator** — Computes Reality Gap Score (0–100)

## Quick Start

### Prerequisites

- Docker + Docker Compose
- Sectors v2 API key (get one at https://sectors.app)
- Ollama running locally OR an OpenAI-compatible LLM provider

### Install

```bash
git clone https://github.com/your-org/naragate.git
cd naragate
cp .env.example .env
```

### Configure

Edit `.env`:

```bash
# Required
SECTORS_API_KEY=your_64_char_api_key

# LLM Provider (default: local Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:12b

# Or use OpenRouter
# OLLAMA_BASE_URL=https://openrouter.ai/api/v1
# OLLAMA_MODEL=meta-llama/llama-3.1-70b-instruct
```

### Run

```bash
docker-compose up
```

Open http://localhost:4200

### First Analysis

1. Type or paste an Indonesian market narrative
2. Click **Analyze**
3. Watch the pipeline execute in real-time
4. Review the Reality Gap Score and evidence breakdown

## Configuration

All settings are configurable via the web UI at `/settings`:

| Setting | Description | Default |
|---------|-------------|---------|
| Sectors API Key | Your API key | Required |
| LLM Endpoint | OpenAI-compatible URL | `http://localhost:11434` |
| LLM API Key | For paid providers | Optional (local Ollama) |
| Default Model | Model for all agents | `gemma4:12b` |
| Claim Parser Model | Override for claim extraction | Uses default |
| Skeptic Model | Override for skepticism | Uses default |
| Scorer Model | Override for scoring | Uses default |

## API

### POST /api/v1/stream/evaluate

Stream a narrative analysis via SSE.

**Request:**
```json
{
  "narrative": "BBCA labanya jeblok, PE-nya masih mahal"
}
```

**Response (SSE):**
```
data: {"type":"claim_parsed","agent":"claim_parser","data":{...}}
data: {"type":"evidence_retrieved","agent":"valuation","data":{...}}
data: {"type":"skeptic_analysis","agent":"skeptic","data":{...}}
data: {"type":"score_computed","agent":"scorer","data":{"score":45,"verdict":"Mixed"}}
```

### GET /api/v1/health

System health check.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Angular 22, Tailwind CSS |
| Backend | FastAPI, Python 3.11 |
| Orchestration | Pi Coding Agent |
| Persistence | SQLite (claims), Redis (cache) |
| LLM | Any OpenAI-compatible provider |
| Data | Sectors v2 API |
| Deployment | Docker Compose |

## Credits Budget

Naragate operates within a **1,600 credit budget** (1,000 hackathon + 600 onboarding) on the Sectors v2 API. Every API call is cached in Redis to minimize credit usage.

| Operation | Credits | Cache TTL |
|-----------|---------|-----------|
| Company report | ~5 | 24 hours |
| Quarterly financials | ~5 | 24 hours |
| Subsector report | ~3 | 24 hours |
| Daily transactions | ~2 | 1 hour |

## Development

```bash
# Backend only
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload

# Frontend only
cd frontend && npm install && ng serve

# Pi Agent only
cd pi-agent && pip install -r requirements.txt && python server.py
```

## License

MIT
