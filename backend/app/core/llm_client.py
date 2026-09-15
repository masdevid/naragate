import json
from typing import Awaitable, Callable, Optional

import httpx

from app.config.settings import settings
from app.core.llm_config import llm_endpoint, llm_harness_url, llm_model, llm_api_key
from app.core.usage_tracker import record_llm_call

LANGUAGE_NAMES = {
    "id": "Indonesian (Bahasa Indonesia)",
    "en": "English",
}


def language_name(language: str) -> str:
    return LANGUAGE_NAMES.get(language, LANGUAGE_NAMES["id"])


def extract_json(raw: str) -> Optional[dict]:
    """Extract a JSON object from an LLM response.

    Tolerates markdown code fences and stray text before/after the JSON object.
    Returns None if no JSON object can be found.
    """
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1])
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


async def stream_chat(
    role: str,
    messages: list,
    response_format: Optional[dict] = None,
    on_token: Optional[Callable[[str], Awaitable[None]]] = None,
) -> str:
    if settings.PI_AGENT_URL:
        return await _stream_via_pi_agent(role, messages, on_token)
    return await _stream_direct(role, messages, response_format, on_token)


async def complete(
    prompt: str,
    system: Optional[str] = None,
    response_format: Optional[dict] = None,
    role: str = "default",
) -> str:
    """Generic one-shot completion against the configured LLM.

    Unlike `stream_chat`, this bypasses the Pi-agent role/skill routing (used by
    the MCP `llm_complete` tool, where the caller supplies the full prompt).
    """
    messages: list = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return await _stream_direct(role, messages, response_format)


async def _stream_direct(
    role: str,
    messages: list,
    response_format: Optional[dict] = None,
    on_token: Optional[Callable[[str], Awaitable[None]]] = None,
) -> str:
    payload = {
        "model": llm_model(role),
        "messages": messages,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if response_format:
        payload["response_format"] = response_format

    return await _consume_sse(
        f"{llm_endpoint()}/chat/completions",
        payload,
        llm_model(role),
        on_token,
    )


async def _stream_via_pi_agent(
    role: str,
    messages: list,
    on_token: Optional[Callable[[str], Awaitable[None]]] = None,
) -> str:
    """Route an agent call through the Pi Agent harness.

    The pi-agent service maps the role to its .pi/skills/* definition, loads it
    as the system prompt inside the Pi CLI harness, and streams the output back.
    """
    prompt = messages[-1]["content"] if messages else ""
    payload = {
        "prompt": prompt,
        "model": llm_model(role),
    }
    return await _consume_sse(
        f"{llm_harness_url()}/agents/{role}/complete",
        payload,
        llm_model(role),
        on_token,
    )


async def _consume_sse(
    url: str,
    payload: dict,
    model: str,
    on_token: Optional[Callable[[str], Awaitable[None]]] = None,
) -> str:
    full = ""
    input_tokens = 0
    output_tokens = 0

    headers = {}
    api_key = llm_api_key()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    async with httpx.AsyncClient(timeout=180.0, headers=headers) as client:
        async with client.stream(
            "POST", url, json=payload
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                usage = chunk.get("usage")
                if usage:
                    input_tokens = usage.get("prompt_tokens", input_tokens)
                    output_tokens = usage.get("completion_tokens", output_tokens)
                choices = chunk.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                reasoning = delta.get("reasoning_content") or ""
                piece = delta.get("content") or ""
                if piece:
                    full += piece
                # Surface the model's reasoning when the provider exposes it;
                # otherwise fall back to streaming the content itself.
                stream_piece = reasoning or piece
                if stream_piece and on_token:
                    await on_token(stream_piece)

    if input_tokens or output_tokens:
        record_llm_call(model, input_tokens, output_tokens)
    return full