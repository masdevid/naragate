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

    async def merge(self, ticker: str, key: str, value, ttl: int = None):
        """Atomically merge one key into the cached entry for a ticker.

        Reads the freshest cached value, sets only `key`, and writes back —
        so a partial update can never wipe out sections cached by other agents.
        """
        if not self._redis:
            await self.connect()
        ttl = ttl or settings.EVIDENCE_CACHE_TTL_COMPANY
        current = await self.get(ticker) or {}
        current[key] = value
        await self._redis.setex(f"evidence:{ticker}", ttl, json.dumps(current))

    async def invalidate(self, ticker: str):
        if not self._redis:
            await self.connect()
        await self._redis.delete(f"evidence:{ticker}")

    # --- Sector-keyed entries (T3) -----------------------------------------
    # Policy claims resolve to a sector, not a single ticker. Their evidence is
    # gathered once per sector and reused across member claims. All methods
    # mirror the ticker-keyed semantics in a separate key namespace so the two
    # never collide.

    @staticmethod
    def _sector_key(sector: str) -> str:
        return f"evidence:sector:{sector}"

    async def get_sector(self, sector: str) -> dict | None:
        if not self._redis:
            await self.connect()
        key = self._sector_key(sector)
        data = await self._redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def set_sector(self, sector: str, data: dict, ttl: int = None):
        if not self._redis:
            await self.connect()
        ttl = ttl or settings.EVIDENCE_CACHE_TTL_COMPANY
        await self._redis.setex(self._sector_key(sector), ttl, json.dumps(data))

    async def merge_sector(self, sector: str, key: str, value, ttl: int = None):
        """Atomically merge one key into the sector-keyed entry.

        Mirrors ticker `merge`: reads the freshest cached value, sets only
        `key`, and writes back so a partial update never wipes other members'
        cached evidence.
        """
        if not self._redis:
            await self.connect()
        ttl = ttl or settings.EVIDENCE_CACHE_TTL_COMPANY
        current = await self.get_sector(sector) or {}
        current[key] = value
        await self._redis.setex(self._sector_key(sector), ttl, json.dumps(current))

    async def invalidate_sector(self, sector: str):
        if not self._redis:
            await self.connect()
        await self._redis.delete(self._sector_key(sector))

    async def is_sector_stale(self, sector: str, data_type: str) -> bool:
        cached = await self.get_sector(sector)
        if not cached or data_type not in cached:
            return True
        fetched_at = cached.get("fetched_at")
        if not fetched_at:
            return True
        ttl = settings.EVIDENCE_CACHE_TTL_DAILY if data_type == "daily_transaction" else settings.EVIDENCE_CACHE_TTL_COMPANY
        return datetime.now() > datetime.fromisoformat(fetched_at) + timedelta(seconds=ttl)

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
