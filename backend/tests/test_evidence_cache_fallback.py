"""Zero-infra guarantee: the Evidence Graph cache degrades to an in-process
store when no Redis is reachable, so `naragate-engine` runs as a single process.
"""

import pytest
import redis

from app.core.evidence_cache import EvidenceGraphCache


class _BrokenRedis:
    async def get(self, *args, **kwargs):
        raise redis.ConnectionError("redis down")

    async def setex(self, *args, **kwargs):
        raise redis.ConnectionError("redis down")

    async def delete(self, *args, **kwargs):
        raise redis.ConnectionError("redis down")


@pytest.mark.asyncio
async def test_falls_back_to_memory_when_redis_unreachable(monkeypatch):
    cache = EvidenceGraphCache()
    monkeypatch.setattr(cache, "_redis", _BrokenRedis())

    await cache.set("BBCA", {"valuation": {"pe": 25}})
    assert await cache.get("BBCA") == {"valuation": {"pe": 25}}
    assert cache._use_memory is True

    # merge still preserves sections cached by other agents
    await cache.merge("BBCA", "news", {"corroboration": "supports"})
    merged = await cache.get("BBCA")
    assert merged is not None
    assert merged["valuation"]["pe"] == 25
    assert merged["news"]["corroboration"] == "supports"

    # after degrading, Redis is bypassed entirely (no second attempt)
    await cache.invalidate("BBCA")
    assert await cache.get("BBCA") is None


@pytest.mark.asyncio
async def test_memory_cache_honours_ttl(monkeypatch):
    cache = EvidenceGraphCache()
    monkeypatch.setattr(cache, "_redis", _BrokenRedis())

    await cache.set_daily_chunk("BBCA", "2026-01-01", [{"close": 1}], ttl=-1)
    assert await cache.get_daily_chunk("BBCA", "2026-01-01") is None
