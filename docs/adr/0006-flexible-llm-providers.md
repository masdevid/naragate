---
status: accepted
---

# Flexible LLM Provider Configuration

The system supports any OpenAI-compatible LLM provider (Ollama, OpenRouter, Together, Groq, etc.) through a generic `/v1/chat/completions` client. The provider endpoint, API key, and model selection are configurable at runtime via the web UI settings page.

**Why**: Users have different preferences for LLM providers — some run Ollama locally for free inference, others use OpenRouter for access to multiple models, others use paid providers for reliability. Locking to a single provider limits adoption. The OpenAI-compatible API format is the de facto standard across providers.

**Trade-off**: Generic client may miss provider-specific features (function calling, streaming modes). Mitigated by using only the common denominator (chat completions with JSON response format) and adding provider-specific adapters later if needed.
