---
status: accepted
---

# Flexible LLM Runtime (Not Locked to Ollama)

The pipeline uses a generic OpenAI-compatible client for LLM calls, supporting any provider (Ollama, OpenRouter, Together, Groq, etc.) that exposes the `/v1/chat/completions` endpoint. The provider endpoint, API key, and model selection are configurable at runtime via the web UI settings page.

**Why**: Users have different preferences for LLM providers — some run Ollama locally for free inference, others use OpenRouter for access to multiple models, others use paid providers for reliability. Locking to a single provider limits adoption. The OpenAI-compatible API format is the de facto standard across providers.

**Trade-off**: Generic client may miss provider-specific features (function calling, streaming modes). Mitigated by using only the common denominator (chat completions with JSON response format) and adding provider-specific adapters later if needed.
