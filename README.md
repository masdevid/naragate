# Naragate

**AI evidence engine that detects financial claims in Indonesian market narratives and verifies them against real financial data.**

---

## Problem

Indonesian retail investors consume market narratives daily — from WhatsApp groups, social media, YouTube videos, and news headlines. Claims like *"BBCA labanya jeblok"* (BBCA's profits collapsed), *"PE-nya masih murah"* (its price-to-earnings ratio is still cheap), or *"TLKM bakal meroket"* (TLKM will skyrocket) can spread faster than a reader can verify them.

This is especially difficult for novice retail traders who have little or no knowledge of how to read a financial report. A financial report contains unfamiliar terms, multiple reporting periods, restatements, accounting categories, and figures that only make sense when compared with the previous quarter, previous year, or another company in the same sector. A beginner may not know:

- where to find revenue, profit, debt, cash flow, or margins;
- whether a number is quarterly, annual, trailing twelve-month, or year-to-date;
- whether profit growth comes from the core business or a one-off event;
- how valuation metrics such as PE or PB should be interpreted;
- which benchmark or peer group makes a comparison meaningful; or
- whether a confident statement is supported by evidence or is simply an opinion.

The result is an information gap. Beginners may trust a persuasive narrative because they cannot quickly challenge it, reject useful information because it looks too technical, or make a decision based on a single number without understanding its context. Manually checking a claim means opening several reports, finding comparable periods, calculating changes, and deciding which evidence is relevant. That process is slow and intimidating even before a beginner reaches an investment decision.

Naragate is designed to make this first verification step easier. It translates a market narrative into specific claims, connects each claim to relevant financial evidence, and explains whether the available data supports, contradicts, or only partially supports the statement. It does not remove the need to learn or perform personal research; it gives a novice a clearer starting point and questions to investigate.

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

## Architecture

```mermaid
flowchart LR
  User[Retail investor] --> App[Naragate app]
  App --> Analysis[AI analysis]
  Analysis --> Result[Evidence and Reality Gap Score]
  Analysis --> Data[Financial data]
  Data --> Sectors[Sectors v2]
  Analysis --> Cache[Cached data]
  Analysis --> LLM[AI language model]

  subgraph Naragate[Naragate]
    App
    Analysis
    Result
    Cache
  end
```

### Multi-Agent Pipeline

1. **Claim Parser** — Extracts structured claims from Indonesian text
2. **Valuation Agent** — Retrieves PE, PB, PS, PCF metrics
3. **Fundamental Agent** — Retrieves revenue, earnings, margins
4. **Market Agent** — Retrieves price, volume, volatility data
5. **Skeletal Agent** — Challenges claims with negation bias
6. **Evidence Judge** — Aggregates evidence from all agents
7. **Score Generator** — Computes Reality Gap Score (0–100)

## Quick Start (no coding required)

Naragate runs entirely in Docker. You do **not** need to install Python, Node.js, or anything else — just Docker and Ollama.

### 1. Install Docker Desktop

- **macOS:** Download from https://www.docker.com/products/docker-desktop/ and open the app. Wait until the whale icon in your menu bar shows **"Docker Desktop is running"**.
- **Windows:** Download from https://www.docker.com/products/docker-desktop/ and open the app. Wait until it shows **"Engine running"**.

### 2. Install Ollama (for the AI model)

Download from https://ollama.com and open it. Then pull a model by opening a terminal and running:

```bash
ollama pull gemma3:12b
```

> Prefer a cloud LLM instead? You can skip Ollama and just paste an OpenAI-compatible endpoint into the web UI later.

### 3. Start Naragate

- **macOS / Linux:** double-click `start.sh` (or run `./start.sh` in a terminal).
- **Windows:** double-click `start.bat`.

The script checks Docker, copies `.env.example` to `.env` if needed, builds the containers (a few minutes the first time), and opens the app in your browser.

### 4. Complete the setup wizard

On first run, Naragate opens a short setup wizard:

1. **LLM provider** — leave the default `http://localhost:11434` if you installed Ollama, then pick a model.
2. **Sectors API key** — paste your key from https://sectors.app (get one free at https://sectors.app).

That's it. You can now paste an Indonesian market narrative and click **Analyze**.

To stop Naragate: run `stop.sh` (macOS/Linux) or `stop.bat` (Windows).

### First Analysis

1. Type or paste an Indonesian market narrative, e.g. *"BBCA labanya jeblok, PE-nya masih mahal banget, mending pindah ke BBRI"* — or click **Try an Example**.
2. Click **Analyze**.
3. Watch the pipeline execute in real-time.
4. Review the Reality Gap Score and evidence breakdown.

## Configuration

All settings are configurable via the web UI at `/settings`:

| Setting | Description | Default |
|---------|-------------|---------|
| Sectors API Key | Your API key | Required |
| LLM Provider | Local Ollama or another compatible provider | Local Ollama |
| LLM API Key | For paid providers | Optional (local Ollama) |
| Default Model | Model for all agents | Set in the setup wizard |
| Claim Parser Model | Override for claim extraction | Uses default |
| Skeptic Model | Override for skepticism | Uses default |
| Scorer Model | Override for scoring | Uses default |

Keys and models set in the web UI take precedence over `.env`. You can leave `.env` empty and configure everything from the browser.

## Troubleshooting ("I'm stuck")

| Problem | Fix |
|---------|-----|
| `Docker is not installed` | Download Docker Desktop from https://www.docker.com/products/docker-desktop/ and install it. |
| `Docker is installed but not running` | Open the Docker Desktop app and wait for it to say "Engine running". |
| "Ollama not detected" warning | Naragate still starts, but analysis needs an LLM. Install Ollama (https://ollama.com) and pull a model, or set a cloud endpoint in the setup wizard. |
| First build takes a long time | Normal — Docker is downloading images. Subsequent starts are fast. |
| Browser opens but the app says "backend not ready" | Wait a moment and refresh. If it persists, run `docker compose logs backend` to see errors. |
| Port already in use | Set different ports in `.env` (`FRONTEND_PORT`, `BACKEND_PORT`), then run `start.sh` again. |
| "No API key configured" in Settings | Paste your Sectors key in the setup wizard or Settings page and click **Validate**. |
| Model list is empty | Make sure Ollama is running and you have pulled a model (`ollama pull gemma3:12b`). |

## Quick Start (Bahasa Indonesia)

1. **Pasang Docker Desktop** dari https://www.docker.com/products/docker-desktop/ dan buka aplikasinya.
2. **Pasang Ollama** dari https://ollama.com, lalu jalankan `ollama pull gemma3:12b`.
3. **Jalankan Naragate**: klik dua kali `start.sh` (macOS/Linux) atau `start.bat` (Windows).
4. **Selesaikan wizard pengaturan**: pilih model LLM, lalu masukkan kunci API Sectors dari https://sectors.app.
5. Tempel narasi pasar, klik **Analisis Narasi Ini**, dan lihat skor Reality Gap beserta bukti keuangannya.

Untuk menghentikan: jalankan `stop.sh` atau `stop.bat`.

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

## Data Usage

Naragate routes Sectors API requests through Redis caching to reduce repeated calls. Sectors controls the current API pricing, quotas, access requirements, and usage terms; check its official documentation before deploying the application.

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
