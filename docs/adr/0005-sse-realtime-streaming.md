---
status: accepted
---

# SSE for Realtime Pipeline Streaming

The backend streams pipeline stages to the frontend via Server-Sent Events (SSE) rather than polling or WebSocket.

**Why**: The multi-agent pipeline produces intermediate results at each stage (claim parsed, evidence retrieved, skeptic challenged, score computed). SSE provides a natural, lightweight push mechanism from the FastAPI backend to the Angular frontend. It's simpler than WebSocket (no bidirectional protocol overhead) and fits the one-way server-to-client streaming pattern of the pipeline.

**Trade-off**: SSE is unidirectional — the frontend can't push back through the same connection. For interactive features (cancelling a claim evaluation, switching models), a separate REST endpoint is needed. Mitigated by keeping the pipeline read-only from the client side and using REST for control operations.
