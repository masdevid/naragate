import json
from pathlib import Path

from app.config.settings import settings

SETTINGS_FILE = Path(__file__).parent.parent / "data" / "runtime_settings.json"

_ROLE_MODEL_KEYS = {
    "claim_parser": "claim_parser_model",
    "skeptic": "skeptic_model",
    "scorer": "scorer_model",
    "news": "news_model",
    "chat": "chat_model",
}


def _load_runtime() -> dict:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text())
        except Exception:
            return {}
    return {}


def _normalize_endpoint(endpoint: str) -> str:
    endpoint = endpoint.rstrip("/")
    if not endpoint.endswith("/v1"):
        endpoint += "/v1"
    return endpoint


def llm_endpoint() -> str:
    runtime = _load_runtime()
    endpoint = runtime.get("llm_endpoint") or settings.OLLAMA_BASE_URL
    return _normalize_endpoint(endpoint)


def llm_harness_url() -> str:
    """Base URL for LLM calls.

    When PI_AGENT_URL is configured, LLM calls are routed through the Pi Agent
    harness gateway (which runs each agent via the Pi CLI with its skill file).
    Otherwise they go straight to the Ollama-compatible endpoint.
    """
    if settings.PI_AGENT_URL:
        return _normalize_endpoint(settings.PI_AGENT_URL)
    return llm_endpoint()


def llm_api_key() -> str:
    runtime = _load_runtime()
    return runtime.get("llm_api_key") or ""


def llm_model(role: str = "default") -> str:
    runtime = _load_runtime()
    model = runtime.get(_ROLE_MODEL_KEYS.get(role, "")) or runtime.get("llm_model")
    if not model:
        if role == "claim_parser":
            model = settings.claim_parser_model
        elif role == "skeptic":
            model = settings.skeptic_model
        elif role == "scorer":
            model = settings.scorer_model
        elif role == "news":
            model = settings.news_model
        elif role == "chat":
            model = settings.chat_model
        else:
            model = settings.OLLAMA_MODEL
    return model