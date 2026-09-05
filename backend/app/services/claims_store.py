import json
import uuid
from datetime import datetime
from typing import Optional
import redis.asyncio as redis

from app.config.settings import settings
from app.models.schemas import Claim, ClaimStatus

NON_TERMINAL_STATUSES = {
    s.value for s in ClaimStatus
    if s not in (ClaimStatus.COMPLETED, ClaimStatus.FAILED)
}


class ClaimsStore:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None

    async def connect(self):
        if self.redis is None:
            self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def disconnect(self):
        if self.redis:
            await self.redis.aclose()
            self.redis = None

    async def create_claim(self, narrative: str, claim: Optional[Claim] = None) -> str:
        await self.connect()
        assert self.redis is not None
        claim_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        state: dict = {
            "claim_id": claim_id,
            "narrative": narrative,
            "status": ClaimStatus.PENDING.value,
            "created_at": now,
            "updated_at": now,
        }

        if claim:
            state["claim"] = claim.model_dump(mode="json")
            state["status"] = ClaimStatus.PARSED.value

        await self.redis.hset(f"claim:{claim_id}", mapping={"state": json.dumps(state)})
        await self.redis.expire(f"claim:{claim_id}", 86400)
        return claim_id

    async def get_claim(self, claim_id: str) -> Optional[dict]:
        await self.connect()
        assert self.redis is not None
        raw = await self.redis.hget(f"claim:{claim_id}", "state")
        if raw is None:
            return None
        return json.loads(raw)

    async def update_claim(self, claim_id: str, updates: dict) -> Optional[dict]:
        await self.connect()
        assert self.redis is not None
        state = await self.get_claim(claim_id)
        if state is None:
            return None

        state.update(updates)
        state["updated_at"] = datetime.now().isoformat()

        await self.redis.hset(f"claim:{claim_id}", mapping={"state": json.dumps(state)})
        return state

    async def set_claim_status(self, claim_id: str, status: ClaimStatus) -> Optional[dict]:
        return await self.update_claim(claim_id, {"status": status.value})

    async def set_claim_data(self, claim_id: str, key: str, data: dict) -> Optional[dict]:
        return await self.update_claim(claim_id, {key: data})

    async def delete_claim(self, claim_id: str) -> bool:
        await self.connect()
        assert self.redis is not None
        deleted = await self.redis.delete(f"claim:{claim_id}")
        return deleted > 0

    async def delete_claims(self, claim_ids: list[str]) -> int:
        await self.connect()
        assert self.redis is not None
        if not claim_ids:
            return 0
        keys = [f"claim:{cid}" for cid in claim_ids]
        deleted = await self.redis.delete(*keys)
        return deleted

    async def list_claims(self, limit: int = 20) -> list[dict]:
        await self.connect()
        assert self.redis is not None
        keys = []
        async for key in self.redis.scan_iter("claim:*", count=100):
            keys.append(key)
            if len(keys) >= limit:
                break

        claims = []
        for key in keys:
            raw = await self.redis.hget(key, "state")
            if raw:
                claims.append(json.loads(raw))

        claims.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return claims

    async def find_active_by_narrative(self, narrative: str, limit: int = 50) -> Optional[dict]:
        await self.connect()
        assert self.redis is not None
        keys = []
        async for key in self.redis.scan_iter("claim:*", count=100):
            keys.append(key)
            if len(keys) >= limit:
                break

        for key in keys:
            raw = await self.redis.hget(key, "state")
            if not raw:
                continue
            state = json.loads(raw)
            if (
                state.get("narrative") == narrative
                and state.get("status") in NON_TERMINAL_STATUSES
            ):
                return state
        return None


claims_store = ClaimsStore()
