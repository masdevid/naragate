---
status: accepted
---

# Pi Coding Agent as Docker Service

The multi-agent pipeline uses Pi Coding Agent as a Docker service that the backend communicates with via HTTP. The backend POSTs narratives to Pi Agent, which orchestrates the 7 skills and returns results via SSE.

**Why**: Building a custom orchestrator from scratch would consume significant development time and introduce reliability risks for a hackathon project. Pi Coding Agent provides the harness — agent spawning, message routing, state management, and the streaming layer — out of the box, letting the team focus on the evidence pipeline logic and Sectors integration.

**Trade-off**: Dependency on a specific framework limits portability. If Pi Coding Agent's API changes or the project outgrows its capabilities, migration to a custom orchestrator would be required. Mitigated by keeping the agent skill definitions framework-agnostic (prompt templates + tool definitions + output schemas) so they can be ported if needed.

## Docker Integration

Pi Agent runs as a Docker service alongside the backend and frontend:

```yaml
pi-agent:
  build: ./pi-agent
  ports:
    - "3000:3000"
  environment:
    - OLLAMA_BASE_URL=${OLLAMA_BASE_URL}
    - OLLAMA_MODEL=${OLLAMA_MODEL:-qwen3-coder:30b}
  volumes:
    - ./.pi:/app/.pi
```

The backend pushes settings to Pi Agent on startup and delegates pipeline execution to it.
