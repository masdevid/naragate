import logging
import time

import redis.asyncio as redis
import json
from datetime import datetime, timedelta
from app.config.settings import settings

logger = logging.getLogger(__name__)


class _MemoryStore:
    """Process-local stand-in for Redis, used when no Redis is reachable.

    This is what lets the engine run with zero infrastructure (a single
    `naragate-engine` process): caching still works, it just does not survive a
    restart. A real deployment sets `REDIS_URL` and gets the shared cache.
    """

    def __init__(self):
        self._data: dict[str, tuple[float, str]] = {}

    async def get(self, key: str) -> str | None:
        item = self._data.get(key)
        if item is None:
            return None
        expires_at, value = item
        if expires_at and time.monotonic() > expires_at:
            self._data.pop(key, None)
            return None
        return value

    async def setex(self, key: str, ttl: int, value: str) -> None:
        self._data[key] = (time.monotonic() + ttl if ttl else 0.0, value)

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)


class EvidenceGraphCache:
    def __init__(self):
        self._redis: redis.Redis | None = None
        self._memory = _MemoryStore()
        self._use_memory = False

    async def connect(self):
        self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def _degrade(self, exc: Exception) -> None:
        if not self._use_memory:
            logger.warning(
                "Redis unavailable at %s (%s) — falling back to an in-process "
                "Evidence Graph cache; entries will not survive a restart.",
                settings.REDIS_URL,
                exc,
            )
        self._use_memory = True

    def _client(self) -> redis.Redis | None:
        if self._use_memory:
            return None
        if not self._redis:
            self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    async def _get(self, key: str) -> str | None:
        client = self._client()
        if client is None:
            return await self._memory.get(key)
        try:
            return await client.get(key)
        except Exception as exc:  # noqa: BLE001 — any Redis failure → local cache
            self._degrade(exc)
            return await self._memory.get(key)

    async def _setex(self, key: str, ttl: int, value: str) -> None:
        client = self._client()
        if client is None:
            await self._memory.setex(key, ttl, value)
            return
        try:
            await client.setex(key, ttl, value)
        except Exception as exc:  # noqa: BLE001
            self._degrade(exc)
            await self._memory.setex(key, ttl, value)

    async def _delete(self, key: str) -> None:
        client = self._client()
        if client is None:
            await self._memory.delete(key)
            return
        try:
            await client.delete(key)
        except Exception as exc:  # noqa: BLE001
            self._degrade(exc)
            await self._memory.delete(key)

    async def get(self, ticker: str) -> dict | None:
        data = await self._get(f"evidence:{ticker}")
        if data:
            return json.loads(data)
        return None

    async def set(self, ticker: str, data: dict, ttl: int = None):
        ttl = int(ttl or settings.EVIDENCE_CACHE_TTL_COMPANY)
        await self._setex(f"evidence:{ticker}", ttl, json.dumps(data))

    async def merge(self, ticker: str, key: str, value, ttl: int = None):
        """Atomically merge one key into the cached entry for a ticker.

        Reads the freshest cached value, sets only `key`, and writes back —
        so a partial update can never wipe out sections cached by other agents.
        """
        ttl = int(ttl or settings.EVIDENCE_CACHE_TTL_COMPANY)
        current = await self.get(ticker) or {}
        current[key] = value
        await self._setex(f"evidence:{ticker}", ttl, json.dumps(current))

    async def invalidate(self, ticker: str):
        await self._delete(f"evidence:{ticker}")

    # --- Chunk-keyed daily series (T1) --------------------------------------
    # The 12-month daily window is fetched in deterministic 90-day epochs so a
    # re-run reuses historical chunks and only a brand-new epoch costs an API
    # call. Keys are addressed by (ticker, epoch_start), independent of the
    # sliding window, so the same chunk is hit again on every later run.

    @staticmethod
    def _chunk_key(ticker: str, epoch_start: str) -> str:
        return f"evidence:chunk:{ticker}:{epoch_start}"

    async def get_daily_chunk(self, ticker: str, epoch_start: str) -> list | None:
        data = await self._get(self._chunk_key(ticker, epoch_start))
        if data:
            return json.loads(data)
        return None

    async def set_daily_chunk(self, ticker: str, epoch_start: str, rows: list, ttl: int = None):
        ttl = int(ttl or settings.EVIDENCE_CACHE_TTL_DAILY)
        await self._setex(self._chunk_key(ticker, epoch_start), ttl, json.dumps(rows))

    # --- Sector-keyed entries (T3) -----------------------------------------
    # Policy claims resolve to a sector, not a single ticker. Their evidence is
    # gathered once per sector and reused across member claims. All methods
    # mirror the ticker-keyed semantics in a separate key namespace so the two
    # never collide.

    @staticmethod
    def _sector_key(sector: str) -> str:
        return f"evidence:sector:{sector}"

    async def get_sector(self, sector: str) -> dict | None:
        data = await self._get(self._sector_key(sector))
        if data:
            return json.loads(data)
        return None

    async def set_sector(self, sector: str, data: dict, ttl: int = None):
        ttl = int(ttl or settings.EVIDENCE_CACHE_TTL_COMPANY)
        await self._setex(self._sector_key(sector), ttl, json.dumps(data))

    async def merge_sector(self, sector: str, key: str, value, ttl: int = None):
        """Atomically merge one key into the sector-keyed entry.

        Mirrors ticker `merge`: reads the freshest cached value, sets only
        `key`, and writes back so a partial update never wipes other members'
        cached evidence.
        """
        ttl = int(ttl or settings.EVIDENCE_CACHE_TTL_COMPANY)
        current = await self.get_sector(sector) or {}
        current[key] = value
        await self._setex(self._sector_key(sector), ttl, json.dumps(current))

    async def invalidate_sector(self, sector: str):
        await self._delete(self._sector_key(sector))

    # --- Market-keyed entries (rankings shared across all claims) -----------
    # Universe-wide feeds (top movers) are not per-ticker. They are fetched
    # once per trading day and reused by every claim, so the cost amortises to
    # ~0 per claim instead of being paid per symbol.

    @staticmethod
    def _market_key(key: str) -> str:
        return f"evidence:market:{key}"

    async def get_market(self, key: str):
        data = await self._get(self._market_key(key))
        if data:
            return json.loads(data)
        return None

    async def set_market(self, key: str, data, ttl: int = None):
        ttl = int(ttl or settings.EVIDENCE_CACHE_TTL_DAILY)
        await self._setex(self._market_key(key), ttl, json.dumps(data))

    # --- Index-keyed daily series (relative-strength inputs) ----------------
    # Index closes use the same deterministic 90-day epoch grid as daily
    # transactions, keyed by (index_code, epoch_start), so a re-run reuses
    # historical chunks and only a new epoch costs a call.

    @staticmethod
    def _index_chunk_key(index_code: str, epoch_start: str) -> str:
        return f"evidence:index:{index_code}:{epoch_start}"

    async def get_index_chunk(self, index_code: str, epoch_start: str) -> list | None:
        data = await self._get(self._index_chunk_key(index_code, epoch_start))
        if data:
            return json.loads(data)
        return None

    async def set_index_chunk(self, index_code: str, epoch_start: str, rows: list, ttl: int = None):
        ttl = int(ttl or settings.EVIDENCE_CACHE_TTL_DAILY)
        await self._setex(self._index_chunk_key(index_code, epoch_start), ttl, json.dumps(rows))

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
