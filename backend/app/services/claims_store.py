import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
import aiosqlite

from app.config.settings import settings
from app.models.schemas import Claim, ClaimStatus

NON_TERMINAL_STATUSES = {
    s.value for s in ClaimStatus
    if s not in (ClaimStatus.COMPLETED, ClaimStatus.FAILED)
}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY,
    narrative TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    state TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status);
CREATE INDEX IF NOT EXISTS idx_claims_created ON claims(created_at);
CREATE TABLE IF NOT EXISTS followup_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    category TEXT NOT NULL,
    verdict TEXT NOT NULL,
    score REAL NOT NULL,
    suggestion_id TEXT NOT NULL,
    suggestion_text TEXT NOT NULL,
    clicked_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_feedback_clicked ON followup_feedback(clicked_at);
"""


class ClaimsStore:
    def __init__(self):
        self._db: Optional[aiosqlite.Connection] = None
        # Overridable for tests (e.g. ":memory:").
        self.db_path: Optional[str] = None

    def _resolve_db_path(self) -> str:
        if self.db_path:
            return self.db_path
        url = settings.DATABASE_URL
        if url.startswith("sqlite:///"):
            path = url[len("sqlite:///"):]
            if path == ":memory:":
                return ":memory:"
            p = Path(path)
            if not p.is_absolute():
                p = Path.cwd() / p
            return str(p)
        return url

    async def connect(self):
        if self._db is None:
            self._db = await aiosqlite.connect(self._resolve_db_path())
            self._db.row_factory = aiosqlite.Row
            await self._db.execute("PRAGMA journal_mode=WAL")
            await self._db.executescript(_SCHEMA)
            await self._db.commit()

    async def disconnect(self):
        if self._db:
            await self._db.close()
            self._db = None

    async def create_claim(self, narrative: str, claim: Optional[Claim] = None) -> str:
        await self.connect()
        assert self._db is not None
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

        await self._db.execute(
            "INSERT INTO claims (claim_id, narrative, status, created_at, updated_at, state) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (claim_id, narrative, state["status"], now, now, json.dumps(state)),
        )
        await self._db.commit()
        return claim_id

    async def get_claim(self, claim_id: str) -> Optional[dict]:
        await self.connect()
        assert self._db is not None
        cur = await self._db.execute(
            "SELECT state FROM claims WHERE claim_id = ?", (claim_id,)
        )
        row = await cur.fetchone()
        await cur.close()
        if row is None:
            return None
        return json.loads(row["state"])

    async def update_claim(self, claim_id: str, updates: dict) -> Optional[dict]:
        await self.connect()
        assert self._db is not None
        state = await self.get_claim(claim_id)
        if state is None:
            return None

        state.update(updates)
        state["updated_at"] = datetime.now().isoformat()

        await self._db.execute(
            "UPDATE claims SET state = ?, status = ?, updated_at = ? WHERE claim_id = ?",
            (json.dumps(state), state.get("status", ""), state["updated_at"], claim_id),
        )
        await self._db.commit()
        return state

    async def set_claim_status(self, claim_id: str, status: ClaimStatus) -> Optional[dict]:
        return await self.update_claim(claim_id, {"status": status.value})

    async def set_claim_data(self, claim_id: str, key: str, data: dict) -> Optional[dict]:
        return await self.update_claim(claim_id, {key: data})

    async def delete_claim(self, claim_id: str) -> bool:
        await self.connect()
        assert self._db is not None
        cur = await self._db.execute(
            "DELETE FROM claims WHERE claim_id = ?", (claim_id,)
        )
        await self._db.commit()
        return cur.rowcount > 0

    async def delete_claims(self, claim_ids: list[str]) -> int:
        await self.connect()
        assert self._db is not None
        if not claim_ids:
            return 0
        placeholders = ",".join("?" * len(claim_ids))
        cur = await self._db.execute(
            f"DELETE FROM claims WHERE claim_id IN ({placeholders})", claim_ids
        )
        await self._db.commit()
        return cur.rowcount

    async def delete_all_claims(self) -> int:
        await self.connect()
        assert self._db is not None
        cur = await self._db.execute("DELETE FROM claims")
        await self._db.commit()
        return cur.rowcount

    async def list_claims(self, limit: int = 20) -> list[dict]:
        await self.connect()
        assert self._db is not None
        cur = await self._db.execute(
            "SELECT state FROM claims ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = await cur.fetchall()
        await cur.close()
        return [json.loads(r["state"]) for r in rows]

    async def list_all_claims(self) -> list[dict]:
        await self.connect()
        assert self._db is not None
        cur = await self._db.execute("SELECT state FROM claims")
        rows = await cur.fetchall()
        await cur.close()
        return [json.loads(r["state"]) for r in rows]

    async def claims_summary(self) -> dict:
        """Aggregate completed claims into a trend summary.

        Returns per-ticker score history, verdict distribution, and overall
        stats so the dashboard can render a history & trend view.
        """
        claims = await self.list_all_claims()
        completed = [
            c for c in claims
            if c.get("status") == ClaimStatus.COMPLETED.value and c.get("score")
        ]

        verdict_counts = {}
        by_ticker: dict[str, list[dict]] = {}
        total_score = 0.0

        for c in completed:
            score = c.get("score") or {}
            ticker = (c.get("claim") or {}).get("ticker", "UNKNOWN")
            verdict = score.get("verdict", "unknown")
            verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
            total_score += score.get("reality_gap_score", 0.0)

            by_ticker.setdefault(ticker, []).append({
                "claim_id": c.get("claim_id"),
                "created_at": c.get("created_at"),
                "score": score.get("reality_gap_score", 0.0),
                "verdict": verdict,
                "narrative": c.get("narrative", ""),
            })

        for ticker in by_ticker:
            by_ticker[ticker].sort(key=lambda x: x.get("created_at", ""))

        count = len(completed)
        return {
            "total_analyses": count,
            "average_score": round(total_score / count, 1) if count else 0.0,
            "verdict_distribution": verdict_counts,
            "by_ticker": by_ticker,
        }

    async def record_followup_feedback(
        self,
        claim_id: str,
        ticker: str,
        category: str,
        verdict: str,
        score: float,
        suggestion_id: str,
        suggestion_text: str,
    ) -> None:
        await self.connect()
        assert self._db is not None
        await self._db.execute(
            "INSERT INTO followup_feedback "
            "(claim_id, ticker, category, verdict, score, suggestion_id, suggestion_text, clicked_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                claim_id,
                ticker,
                category,
                verdict,
                score,
                suggestion_id,
                suggestion_text,
                datetime.now().isoformat(),
            ),
        )
        await self._db.commit()

    async def recent_followup_feedback(self, limit: int = 20) -> list[dict]:
        await self.connect()
        assert self._db is not None
        cur = await self._db.execute(
            "SELECT claim_id, ticker, category, verdict, score, suggestion_id, suggestion_text, clicked_at "
            "FROM followup_feedback ORDER BY clicked_at DESC LIMIT ?",
            (limit,),
        )
        rows = await cur.fetchall()
        await cur.close()
        return [dict(r) for r in rows]

    async def followup_topic_counts(self, field: str, limit: int = 5) -> list[dict]:
        """Count clicks grouped by a feedback field, most-clicked first.

        `field` must be one of: ticker, category, verdict.
        """
        if field not in ("ticker", "category", "verdict"):
            raise ValueError(f"Unsupported topic field: {field}")
        await self.connect()
        assert self._db is not None
        cur = await self._db.execute(
            f"SELECT {field} AS value, COUNT(*) AS clicks FROM followup_feedback "
            f"GROUP BY {field} ORDER BY clicks DESC LIMIT ?",
            (limit,),
        )
        rows = await cur.fetchall()
        await cur.close()
        return [{"value": r["value"], "clicks": r["clicks"]} for r in rows]

    async def find_active_by_narrative(self, narrative: str, limit: int = 50) -> Optional[dict]:
        await self.connect()
        assert self._db is not None
        non_terminal = list(NON_TERMINAL_STATUSES)
        placeholders = ",".join("?" * len(non_terminal))
        cur = await self._db.execute(
            f"SELECT state FROM claims "
            f"WHERE narrative = ? AND status IN ({placeholders}) "
            f"ORDER BY created_at DESC LIMIT ?",
            (narrative, *non_terminal, limit),
        )
        rows = await cur.fetchall()
        await cur.close()
        if not rows:
            return None
        return json.loads(rows[0]["state"])


claims_store = ClaimsStore()