import json
from typing import Awaitable, Callable, Optional

import httpx

from app.core.llm_config import llm_endpoint, llm_model
from app.core.usage_tracker import record_llm_call

LANGUAGE_NAMES = {
    "id": "Indonesian (Bahasa Indonesia)",
    "en": "English",
}


def language_name(language: str) -> str:
    return LANGUAGE_NAMES.get(language, LANGUAGE_NAMES["id"])


async def stream_chat(
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

    full = ""
    input_tokens = 0
    output_tokens = 0

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST", f"{llm_endpoint()}/chat/completions", json=payload
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
                piece = delta.get("content") or ""
                if piece:
                    full += piece
                    if on_token:
                        await on_token(piece)

    if input_tokens or output_tokens:
        record_llm_call(llm_model(role), input_tokens, output_tokens)
    return full