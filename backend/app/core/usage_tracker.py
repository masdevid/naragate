import json
import os
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

USAGE_FILE = Path(os.environ.get("NARAGATE_USAGE_FILE", str(Path(__file__).parent.parent / "data" / "usage.json")))

# LLM pricing per 1M tokens (USD) — approximate for common providers
LLM_PRICING = {
    "gemma4:12b": {"input": 0.0, "output": 0.0},  # local Ollama = free
    "llama3.1": {"input": 0.0, "output": 0.0},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "claude-3.5-sonnet": {"input": 3.00, "output": 15.00},
    "deepseek-chat": {"input": 0.14, "output": 0.28},
}

# Default pricing for unknown models
DEFAULT_LLM_PRICING = {"input": 0.0, "output": 0.0}

# In-memory counters for the currently running pipeline (reset per run)
_session = {"sectors": 0, "sectors_cached": 0, "llm": 0, "llm_input_tokens": 0, "llm_output_tokens": 0}


def reset_session_usage():
    _session["sectors"] = 0
    _session["sectors_cached"] = 0
    _session["llm"] = 0
    _session["llm_input_tokens"] = 0
    _session["llm_output_tokens"] = 0


def get_session_usage() -> dict:
    return dict(_session)


def _load() -> dict:
    if USAGE_FILE.exists():
        try:
            return json.loads(USAGE_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save(data: dict):
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    USAGE_FILE.write_text(json.dumps(data, indent=2))


def _ensure_structure(data: dict) -> dict:
    data.setdefault("sectors", {"calls": 0, "cached_calls": 0, "daily": {}})
    data["sectors"].setdefault("cached_calls", 0)
    data.setdefault("llm", {"calls": 0, "input_tokens": 0, "output_tokens": 0, "daily": {}})
    data.setdefault("pipelines", {"total": 0, "completed": 0, "failed": 0})
    return data


def record_sectors_call(endpoint: str = "", cached: bool = False):
    if cached:
        _session["sectors_cached"] += 1
        data = _ensure_structure(_load())
        data["sectors"]["cached_calls"] = data["sectors"].get("cached_calls", 0) + 1
        _save(data)
        return
    _session["sectors"] += 1
    data = _ensure_structure(_load())
    today = datetime.now().strftime("%Y-%m-%d")
    data["sectors"]["calls"] += 1
    if "remaining" in data["sectors"]:
        data["sectors"]["remaining"] = max(data["sectors"]["remaining"] - 1, 0)
    data["sectors"]["daily"].setdefault(today, 0)
    data["sectors"]["daily"][today] += 1
    _save(data)


def record_sectors_cache_hit():
    """Count one Sectors API call avoided by serving evidence from cache."""
    record_sectors_call(cached=True)


def record_llm_call(model: str, input_tokens: int, output_tokens: int):
    _session["llm"] += 1
    _session["llm_input_tokens"] += input_tokens
    _session["llm_output_tokens"] += output_tokens
    data = _ensure_structure(_load())
    today = datetime.now().strftime("%Y-%m-%d")
    data["llm"]["calls"] += 1
    data["llm"]["input_tokens"] += input_tokens
    data["llm"]["output_tokens"] += output_tokens
    data["llm"]["daily"].setdefault(today, {"calls": 0, "input_tokens": 0, "output_tokens": 0})
    data["llm"]["daily"][today]["calls"] += 1
    data["llm"]["daily"][today]["input_tokens"] += input_tokens
    data["llm"]["daily"][today]["output_tokens"] += output_tokens
    _save(data)


def record_pipeline(completed: bool = True):
    data = _ensure_structure(_load())
    data["pipelines"]["total"] += 1
    if completed:
        data["pipelines"]["completed"] += 1
    else:
        data["pipelines"]["failed"] += 1
    _save(data)


def estimate_llm_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = LLM_PRICING.get(model, DEFAULT_LLM_PRICING)
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 6)


def get_usage_summary(budget: int = 1600) -> dict:
    data = _ensure_structure(_load())

    sectors = data["sectors"]
    llm = data["llm"]
    pipelines = data["pipelines"]

    sectors_used = sectors["calls"]
    sectors_pct = round(sectors_used / budget * 100, 1) if budget > 0 else 0
    sectors_remaining = sectors.get("remaining", max(budget - sectors_used, 0))

    model = _load_model_name()
    llm_cost = estimate_llm_cost(model, llm["input_tokens"], llm["output_tokens"])

    # Daily breakdown for last 7 days
    daily = []
    for i in range(6, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        s_daily = sectors["daily"].get(day, 0)
        l_daily = llm["daily"].get(day, {})
        daily.append({
            "date": day,
            "sectors_calls": s_daily,
            "llm_calls": l_daily.get("calls", 0) if isinstance(l_daily, dict) else 0,
            "llm_input_tokens": l_daily.get("input_tokens", 0) if isinstance(l_daily, dict) else 0,
            "llm_output_tokens": l_daily.get("output_tokens", 0) if isinstance(l_daily, dict) else 0,
        })

    return {
        "sectors": {
            "total_calls": sectors_used,
            "cached_calls": sectors.get("cached_calls", 0),
            "budget": budget,
            "budget_pct": sectors_pct,
            "remaining": sectors_remaining,
        },
        "llm": {
            "model": model,
            "total_calls": llm["calls"],
            "input_tokens": llm["input_tokens"],
            "output_tokens": llm["output_tokens"],
            "total_tokens": llm["input_tokens"] + llm["output_tokens"],
            "estimated_cost_usd": llm_cost,
        },
        "pipelines": pipelines,
        "daily": daily,
    }


def _load_model_name() -> str:
    settings_file = USAGE_FILE.parent / "runtime_settings.json"
    if settings_file.exists():
        try:
            data = json.loads(settings_file.read_text())
            return data.get("llm_model", "unknown")
        except Exception:
            pass
    return "unknown"
