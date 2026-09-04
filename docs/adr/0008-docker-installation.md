---
status: accepted
---

# Docker Installation with Pi Agent Service

The system is distributed as a Docker Compose setup with three services: backend (FastAPI), frontend (Angular), and Pi Agent (orchestration). Ollama is NOT included in Docker — users run it separately (locally or on a remote server) and configure the endpoint via the web UI.

**Why**: Docker provides single-command installation (`docker-compose up`) while keeping services isolated. Ollama is excluded because it requires GPU access for local inference, and users may prefer their own setup (local Ollama, OpenRouter, paid provider). Pi Agent is included because it's the orchestration layer that the backend delegates pipeline execution to.

**Trade-off**: Users must install Docker and Docker Compose. Mitigated by Docker Desktop being widely available and the setup being well-documented.

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Docker Compose                                 │
│                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Frontend │  │ Backend  │  │  Pi Agent    │  │
│  │ (Angular │→ │ (FastAPI │→ │  (Orchestr.) │  │
│  │  + nginx)│  │  + SQLite│  │              │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
│                     │                           │
│               ┌─────┴─────┐                     │
│               │   Redis   │                     │
│               │  (cache)  │                     │
│               └───────────┘                     │
└─────────────────────────────────────────────────┘
                     │
              ┌──────┴──────┐
              │   Ollama    │  ← User's own setup
              │ (external)  │
              └─────────────┘
```

## Settings Flow

1. User configures settings via web UI (`/settings`)
2. Backend stores settings in SQLite
3. Backend pushes config to Pi Agent on startup
4. Pi Agent uses configured LLM endpoint for pipeline execution
