import os
import json
import subprocess
import asyncio
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx

app = FastAPI(title="Pi Agent Service")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "")

class NarrativeRequest(BaseModel):
    narrative: str
    claim_parser_model: str | None = None
    skeptic_model: str | None = None
    scorer_model: str | None = None

class PipelineEvent(BaseModel):
    type: str
    agent: str
    data: dict

async def run_pi_agent(narrative: str, models: dict) -> AsyncGenerator[str, None]:
    """Run Pi Agent pipeline and yield SSE events."""
    # Build the prompt for Pi Agent
    prompt = f"""Analyze this Indonesian market narrative and extract financial claims, then verify them against Sectors v2 data.

Narrative: {narrative}

Pipeline steps:
1. Claim Parser: Extract structured claims from the narrative
2. Valuation Agent: Retrieve valuation evidence (PE, PB, PS, PCF)
3. Fundamental Agent: Retrieve financial fundamentals (revenue, earnings, margins)
4. Market Agent: Retrieve market performance (price, volume, volatility)
5. Skeptic Agent: Challenge claims with negation bias
6. Evidence Judge: Aggregate evidence from all agents
7. Score Generator: Compute Reality Gap score (0-100) and verdict

For each step, output a JSON event with type, agent, and data fields."""

    try:
        # Use Pi CLI to run the pipeline
        process = await asyncio.create_subprocess_exec(
            "pi", "run", "--prompt", prompt,
            "--model", models.get("claim_parser", OLLAMA_MODEL),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "OLLAMA_BASE_URL": OLLAMA_BASE_URL}
        )

        # Read output and convert to SSE events
        if process.stdout:
            async for line in process.stdout:
                if line:
                    try:
                        data = json.loads(line.decode())
                        event = PipelineEvent(
                            type=data.get("type", "unknown"),
                            agent=data.get("agent", "pi-agent"),
                            data=data.get("data", {})
                        )
                        yield f"data: {event.model_dump_json()}\n\n"
                    except json.JSONDecodeError:
                        # Non-JSON output, wrap as log event
                        event = PipelineEvent(
                            type="log",
                            agent="pi-agent",
                            data={"message": line.decode().strip()}
                        )
                        yield f"data: {event.model_dump_json()}\n\n"

        # Wait for process to complete
        await process.wait()

        if process.returncode != 0 and process.stderr:
            stderr = await process.stderr.read()
            event = PipelineEvent(
                type="error",
                agent="pi-agent",
                data={"message": f"Pi Agent failed: {stderr.decode()}"}
            )
            yield f"data: {event.model_dump_json()}\n\n"

    except FileNotFoundError:
        event = PipelineEvent(
            type="error",
            agent="pi-agent",
            data={"message": "Pi CLI not found. Install with: npm install -g @earendil-works/pi-coding-agent"}
        )
        yield f"data: {event.model_dump_json()}\n\n"
    except Exception as e:
        event = PipelineEvent(
            type="error",
            agent="pi-agent",
            data={"message": str(e)}
        )
        yield f"data: {event.model_dump_json()}\n\n"

@app.post("/evaluate")
async def evaluate(request: NarrativeRequest):
    """Evaluate a narrative through the Pi Agent pipeline."""
    models = {
        "claim_parser": request.claim_parser_model or OLLAMA_MODEL,
        "skeptic": request.skeptic_model or OLLAMA_MODEL,
        "scorer": request.scorer_model or OLLAMA_MODEL,
    }

    return StreamingResponse(
        run_pi_agent(request.narrative, models),
        media_type="text/event-stream"
    )

@app.get("/health")
async def health():
    """Health check endpoint."""
    # Check if Pi CLI is available
    pi_available = False
    try:
        result = subprocess.run(["pi", "--version"], capture_output=True, text=True)
        pi_available = result.returncode == 0
    except FileNotFoundError:
        pass

    # Check Ollama connectivity
    ollama_available = False
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5.0)
            ollama_available = response.status_code == 200
    except Exception:
        pass

    return {
        "status": "healthy" if pi_available and ollama_available else "degraded",
        "pi_agent": pi_available,
        "ollama": ollama_available,
        "ollama_url": OLLAMA_BASE_URL,
        "default_model": OLLAMA_MODEL,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
