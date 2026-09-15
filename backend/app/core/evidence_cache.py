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

    # --- Chunk-keyed daily series (T1) --------------------------------------
    # The 12-month daily window is fetched in deterministic 90-day epochs so a
    # re-run reuses historical chunks and only a brand-new epoch costs an API
    # call. Keys are addressed by (ticker, epoch_start), independent of the
    # sliding window, so the same chunk is hit again on every later run.

    @staticmethod
    def _chunk_key(ticker: str, epoch_start: str) -> str:
        return f"evidence:chunk:{ticker}:{epoch_start}"

    async def get_daily_chunk(self, ticker: str, epoch_start: str) -> list | None:
        if not self._redis:
            await self.connect()
        data = await self._redis.get(self._chunk_key(ticker, epoch_start))
        if data:
            return json.loads(data)
        return None

    async def set_daily_chunk(self, ticker: str, epoch_start: str, rows: list, ttl: int = None):
        if not self._redis:
            await self.connect()
        ttl = ttl or settings.EVIDENCE_CACHE_TTL_DAILY
        await self._redis.setex(self._chunk_key(ticker, epoch_start), ttl, json.dumps(rows))

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

    # --- Market-keyed entries (rankings shared across all claims) -----------
    # Universe-wide feeds (top movers) are not per-ticker. They are fetched
    # once per trading day and reused by every claim, so the cost amortises to
    # ~0 per claim instead of being paid per symbol.

    @staticmethod
    def _market_key(key: str) -> str:
        return f"evidence:market:{key}"

    async def get_market(self, key: str):
        if not self._redis:
            await self.connect()
        data = await self._redis.get(self._market_key(key))
        if data:
            return json.loads(data)
        return None

    async def set_market(self, key: str, data, ttl: int = None):
        if not self._redis:
            await self.connect()
        ttl = ttl or settings.EVIDENCE_CACHE_TTL_DAILY
        await self._redis.setex(self._market_key(key), ttl, json.dumps(data))

    # --- Index-keyed daily series (relative-strength inputs) ----------------
    # Index closes use the same deterministic 90-day epoch grid as daily
    # transactions, keyed by (index_code, epoch_start), so a re-run reuses
    # historical chunks and only a new epoch costs a call.

    @staticmethod
    def _index_chunk_key(index_code: str, epoch_start: str) -> str:
        return f"evidence:index:{index_code}:{epoch_start}"

    async def get_index_chunk(self, index_code: str, epoch_start: str) -> list | None:
        if not self._redis:
            await self.connect()
        data = await self._redis.get(self._index_chunk_key(index_code, epoch_start))
        if data:
            return json.loads(data)
        return None

    async def set_index_chunk(self, index_code: str, epoch_start: str, rows: list, ttl: int = None):
        if not self._redis:
            await self.connect()
        ttl = ttl or settings.EVIDENCE_CACHE_TTL_DAILY
        await self._redis.setex(self._index_chunk_key(index_code, epoch_start), ttl, json.dumps(rows))

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
