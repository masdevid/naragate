# Naragate — Agent Configuration

## Project Overview

Naragate is an AI evidence engine that detects financial claims in Indonesian market narratives and verifies them against Sectors v2 financial data.

## Opencode Sub-Agents (Development)

Use these agents when building features. Each agent has specific domain context.

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| `backend-api` | FastAPI endpoints, services, models | Adding/modifying API endpoints, Pydantic models, settings |
| `frontend-ui` | Angular 22 + Tailwind components | Building UI components, pages, SSE streaming |
| `sectors-client` | Sectors v2 API integration | API calls, caching, credit budget management |
| `agent-pipeline` | Multi-agent orchestration | Implementing claim parser, evidence agents, skeptic, judge, scorer |
| `infra` | Docker, Redis, deployment | Docker Compose, requirements.txt, .env config |

### Usage

In opencode, use `/agent backend-api` to switch context to backend development.

## Pi Coding Agent (Runtime Pipeline)

Orchestration framework at `~/.pi/agent/`. Ollama endpoint: `https://dev.idh.am/v1`. 7 agent skills defined in `.pi/skills/`:

1. **Claim Parser** — Extracts structured claims from Indonesian narratives
2. **Valuation Agent** — Retrieves valuation evidence (PE, PB, PS, PCF)
3. **Fundamental Agent** — Retrieves financial fundamentals (revenue, earnings, margins)
4. **Market Agent** — Retrieves market performance (price, volume, volatility)
5. **Skeptic Agent** — Challenges claims with negation bias
6. **Evidence Judge** — Aggregates evidence from all agents
7. **Score Generator** — Computes Reality Gap score (0-100) and verdict

## Issue Tracker

Issues live as markdown files under `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

## Triage Labels

Five canonical roles: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

## Domain Docs

Single-context layout: `CONTEXT.md` + `docs/adr/` at repo root. See `docs/agents/domain.md`.

## Key Configuration

- **Sectors API**: `https://api.sectors.app/v2/` (use trailing slash)
- **Ollama**: `https://dev.idh.am/v1` (6 models available)
- **Credit Budget**: 1,600 Sectors API credits
- **Curated Stocks**: BBCA, BBRI, BMRI, TLKM, UNVR
- **Backend Port**: 8000
