import redis.asyncio as redis
import json
from datetime import datetime, timedelta
from app.config.settings import settings

class EvidenceGraphCache:
    def __init__(self):
        self._redis: redis.Redis | None = None

    async def connect(self):
        self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def get(self, ticker: str) -> dict | None:
        if not self._redis:
            await self.connect()
        data = await self._redis.get(f"evidence:{ticker}")
        if data:
            return json.loads(data)
        return None

    async def set(self, ticker: str, data: dict, ttl: int = None):
        if not self._redis:
            await self.connect()
        ttl = ttl or settings.EVIDENCE_CACHE_TTL_COMPANY
        await self._redis.setex(f"evidence:{ticker}", ttl, json.dumps(data))

    async def invalidate(self, ticker: str):
        if not self._redis:
            await self.connect()
        await self._redis.delete(f"evidence:{ticker}")

    async def is_stale(self, ticker: str, data_type: str) -> bool:
        cached = await self.get(ticker)
        if not cached or data_type not in cached:
            return True
        fetched_at = cached.get("fetched_at")
        if not fetched_at:
            return True
        ttl = settings.EVIDENCE_CACHE_TTL_DAILY if data_type == "daily_transaction" else settings.EVIDENCE_CACHE_TTL_COMPANY
        return datetime.now() > datetime.fromisoformat(fetched_at) + timedelta(seconds=ttl)

cache = EvidenceGraphCache()
