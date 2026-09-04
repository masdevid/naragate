# Naragate

The domain of an evidence engine that detects financial claims in Indonesian market narratives and verifies them against Sectors v2 financial data.

## Language

**Claim**: A structured financial proposition extracted from a narrative, with a ticker, category, assertion, and direction. _Avoid_: opinion, statement, sentiment.

**Narrative**: Indonesian market text — a headline, news article, or user-typed statement — that contains one or more financial claims. _Avoid_: article, post, feed item.

**Evidence**: Sectors v2 data retrieved to verify a claim — valuation metrics, financials, transaction data, or peer benchmarks. _Avoid_: data, payload, result.

**Evidence Graph**: A per-stock cache of accumulated Sectors data (company report, quarterly financials, subsector report, daily transaction). Claims reuse the graph; stale sections trigger background refresh. _Avoid_: cache, database, store.

**Reality Gap Score**: A 0–100 quantitative measure of how strongly the financial evidence aligns with the narrative claim. Not a buy/sell recommendation — a consistency score. _Avoid_: confidence, accuracy, rating.

**Verdict**: The derived label from the Reality Gap Score band: *Contradicted* (0–30), *Mixed* (31–60), *Supported* (61–80), *Strongly Supported* (81–100). _Avoid_: result, output, classification.

**Claim Category**: The type of financial claim — one of *valuation*, *fundamental*, *market*, or *peer comparison*. Determines which evidence dimensions are computed. _Avoid_: type, class, kind.

**Agent**: A specialized sub-agent in the multi-agent pipeline, each responsible for a specific reasoning type. _Avoid_: worker, service, module.

**Claim Parser**: The agent that extracts structured claims from narratives using an LLM. _Avoid_: extractor, NLP model, parser service.

**Skeptic**: The agent that re-interprets the same evidence with a negation bias to challenge the claim. It does not fetch new data — it challenges what the validating agents already retrieved. _Avoid_: critic, validator, checker.

**Sectors**: The data source — Sectors v2 API providing company reports, quarterly financials, subsector reports, daily transaction data, and news for Indonesian stocks. _Avoid_: API, data provider, source.

**LLM Provider**: The LLM runtime used for claim extraction and skeptical re-interpretation. Supports any OpenAI-compatible provider (Ollama, OpenRouter, Together, Groq, etc.). The endpoint, API key, and model selection are configurable at runtime via the web UI settings page. _Avoid_: AI service, model host, Ollama.

**Pi Coding Agent**: The agentic orchestration framework that manages sub-agent lifecycle, message routing, realtime streaming, and the skill harness for the multi-agent pipeline. Runs as a Docker service alongside the backend. _Avoid_: orchestrator, framework, engine.

**Skill**: A tailored capability definition for a Pi Coding Agent sub-agent — comprising a prompt template, tool definitions (Sectors API calls, evidence cache queries), and an output schema. _Avoid_: prompt, template, instruction.

**Harness**: The infrastructure layer that manages agent lifecycle, message routing, state management (evidence graph updates), and the SSE streaming layer. _Avoid_: server, backend, runtime.

**Evidence Dimension**: A specific gap measured for the Reality Gap Score — *valuation gap*, *earnings gap*, *market momentum gap*, *peer relative gap*, or *evidence confidence*. Only dimensions relevant to the claim category are computed. _Avoid_: metric, factor, indicator.

**Credit**: A unit of Sectors API usage. The project operates within a 1,600-credit budget (1,000 hackathon + 600 onboarding). Each API call consumes credits; caching is mandatory to stay within budget. _Avoid_: token, point, quota.

**Settings**: Runtime configuration stored in SQLite, editable via the web UI settings page. Includes Sectors API key, LLM provider endpoint, API key, model selection (global and per-agent), and other system parameters. _Avoid_: config, preferences, options.

**Docker Compose**: The installation mechanism — a single `docker-compose up` command starts the backend, frontend, Pi Agent, and Redis. Ollama is NOT included; users run it separately (locally or on a remote server) and configure the endpoint via the web UI. _Avoid_: deployment, installation, setup.

## Rules

- Input language is **Indonesian**; domain model language is **English**. Indonesian terms (`mahal`, `jeblok`, `anjlok`, `meroket`, `labanya jeblok`) are surface lexical variants that map to canonical English domain concepts.
- The Reality Gap Score is never a buy/sell recommendation. It measures narrative-reality alignment only.
- All Sectors API calls must be routed through the Evidence Graph cache first. Direct API calls without cache-check are forbidden.
- The system supports any OpenAI-compatible LLM provider — users are not locked to Ollama.
- Settings are persisted in SQLite and editable via the web UI at runtime (no restart required).
