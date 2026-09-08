import os
import json
import asyncio
import subprocess
from pathlib import Path
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI(title="Pi Agent Service")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://dev.idh.am/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3-coder:30b")
PI_API_KEY = os.getenv("PI_API_KEY", "ollama")
PI_PROVIDER = os.getenv("PI_PROVIDER", "ollama")
SKILLS_DIR = Path(os.getenv("PI_SKILLS_DIR", "/app/.pi/skills"))

# Backend agent role -> skill directory name. The skill file is the canonical
# agent definition loaded into the Pi harness as the system prompt.
ROLE_SKILLS = {
    "claim_parser": "claim-parser",
    "skeptic": "skeptic-agent",
    "news": "news-agent",
    "chat": "chat",
    "scorer": "score-generator",
    "judge": "evidence-judge",
}

# Models served by the Ollama-compatible endpoint (dev.idh.am/v1).
_KNOWN_MODELS = [
    {"id": "qwen3.8-cc:27b", "name": "Qwen 3.8 CC 27B", "contextLength": 65536},
    {"id": "glm-5.3:cloud", "name": "GLM 5.3 Cloud", "contextLength": 128000},
    {"id": "qwen3.8:27b-tuned", "name": "Qwen 3.8 27B Tuned", "contextLength": 65536},
    {"id": "qwen3-coder:30b", "name": "Qwen 3 Coder 30B", "contextLength": 128000},
    {"id": "qwen2.5:7b", "name": "Qwen 2.5 7B", "contextLength": 128000},
    {"id": "gemma4:12b", "name": "Gemma 4 12B", "contextLength": 128000},
    {"id": "llama3.2:1b", "name": "Llama 3.2 1B", "contextLength": 128000},
]


def _normalize_endpoint(endpoint: str) -> str:
    endpoint = endpoint.rstrip("/")
    if not endpoint.endswith("/v1"):
        endpoint += "/v1"
    return endpoint


def ensure_pi_config() -> None:
    """Write the Pi CLI provider config so it can reach the Ollama endpoint.

    The Pi CLI reads ~/.pi/agent/models.json for custom providers. Without it,
    the CLI only knows the built-in providers (OpenAI, etc.) and cannot route
    to the Ollama-compatible endpoint used by Naragate.
    """
    agent_dir = Path.home() / ".pi" / "agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    models_file = agent_dir / "models.json"

    models = list(_KNOWN_MODELS)
    if OLLAMA_MODEL and not any(m["id"] == OLLAMA_MODEL for m in models):
        models.append({"id": OLLAMA_MODEL, "name": OLLAMA_MODEL, "contextLength": 128000})

    config = {
        "providers": {
            PI_PROVIDER: {
                "name": "Ollama (dev.idh.am)",
                "api": "openai-completions",
                "baseUrl": _normalize_endpoint(OLLAMA_BASE_URL),
                "apiKey": PI_API_KEY,
                "models": models,
            }
        }
    }
    models_file.write_text(json.dumps(config, indent=2))


ensure_pi_config()


def _skill_prompt(role: str) -> Optional[str]:
    """Return the skill file content for a role, or None if no skill exists."""
    skill_dir = ROLE_SKILLS.get(role)
    if not skill_dir:
        return None
    skill_file = SKILLS_DIR / skill_dir / "SKILL.md"
    if not skill_file.exists():
        return None
    return skill_file.read_text(encoding="utf-8")


class AgentRequest(BaseModel):
    prompt: str
    model: Optional[str] = None


async def _run_pi_cli(system_prompt: str, user_prompt: str, model: str) -> AsyncGenerator[dict, None]:
    """Run the Pi CLI harness and yield parsed JSON events."""
    cmd = [
        "pi",
        "-p",
        "--no-session",
        "--mode", "json",
        "--no-tools",
        "--provider", PI_PROVIDER,
        "--model", f"{PI_PROVIDER}/{model}",
        "--api-key", PI_API_KEY,
        "--system-prompt", system_prompt,
        user_prompt,
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    assert process.stdout is not None
    async for raw in process.stdout:
        line = raw.decode("utf-8", errors="replace").strip()
        if not line.startswith("{"):
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue
    await process.wait()
    if process.returncode != 0 and process.stderr is not None:
        stderr = await process.stderr.read()
        raise RuntimeError(f"Pi CLI exited {process.returncode}: {stderr.decode(errors='replace')[:500]}")


def _extract_text_delta(event: dict) -> str:
    """Extract the incremental text delta from a Pi JSON event."""
    etype = event.get("type")
    if etype not in ("message_start", "message_end", "message_update"):
        return ""
    message = event.get("message") or {}
    if message.get("role") != "assistant":
        return ""
    content = message.get("content")
    if not isinstance(content, list):
        return ""
    text = ""
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            text += block.get("text") or ""
    return text


def _extract_usage(event: dict) -> Optional[dict]:
    """Extract token usage from a Pi JSON event."""
    message = event.get("message") or {}
    usage = message.get("usage")
    if not isinstance(usage, dict):
        return None
    return {
        "prompt_tokens": usage.get("input", 0),
        "completion_tokens": usage.get("output", 0),
        "total_tokens": usage.get("totalTokens", 0),
    }


async def _stream_chat_completions(system_prompt: str, user_prompt: str, model: str) -> AsyncGenerator[str, None]:
    """Run Pi and translate its JSON events into OpenAI chat-completions SSE."""
    first_sent = False
    full_text = ""
    usage = None
    try:
        async for event in _run_pi_cli(system_prompt, user_prompt, model):
            delta = _extract_text_delta(event)
            if delta:
                if not first_sent:
                    # First chunk carries the opening delta.
                    yield _sse_chunk(delta)
                    full_text = delta
                    first_sent = True
                elif event.get("type") == "message_end":
                    # Final chunk carries the full text; emit only the remainder.
                    remainder = delta[len(full_text):] if delta.startswith(full_text) else delta
                    if remainder:
                        yield _sse_chunk(remainder)
                    full_text = delta
            u = _extract_usage(event)
            if u:
                usage = u
    except Exception as e:
        yield _sse_chunk("", error=str(e))

    if not first_sent:
        yield _sse_chunk("")
    yield _sse_done(usage)


def _sse_chunk(delta: str, error: Optional[str] = None) -> str:
    finish = "stop" if error is None else None
    payload = {
        "id": "pi-agent",
        "object": "chat.completion.chunk",
        "choices": [{"index": 0, "delta": {"content": delta}, "finish_reason": finish}],
    }
    if error:
        payload["error"] = error
    return f"data: {json.dumps(payload)}\n\n"


def _sse_done(usage: Optional[dict]) -> str:
    payload = {
        "id": "pi-agent",
        "object": "chat.completion.chunk",
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    if usage:
        payload["usage"] = usage
    return f"data: {json.dumps(payload)}\n\ndata: [DONE]\n\n"


@app.post("/v1/agents/{role}/complete")
async def complete(role: str, request: AgentRequest):
    """Run a single agent through the Pi harness and stream its output.

    The role maps to a skill file in .pi/skills/ which becomes the agent's
    system prompt inside the Pi CLI harness.
    """
    skill_prompt = _skill_prompt(role)
    if not skill_prompt:
        raise HTTPException(status_code=404, detail=f"No skill defined for role '{role}'")

    model = request.model or OLLAMA_MODEL
    return StreamingResponse(
        _stream_chat_completions(skill_prompt, request.prompt, model),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    pi_available = False
    try:
        result = subprocess.run(["pi", "--version"], capture_output=True, text=True, timeout=10)
        pi_available = result.returncode == 0
    except Exception:
        pass

    skills = sorted({d.name for d in SKILLS_DIR.iterdir() if (d / "SKILL.md").exists()}) if SKILLS_DIR.exists() else []

    return {
        "status": "healthy" if pi_available else "degraded",
        "pi_agent": pi_available,
        "ollama_url": OLLAMA_BASE_URL,
        "default_model": OLLAMA_MODEL,
        "skills": skills,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)