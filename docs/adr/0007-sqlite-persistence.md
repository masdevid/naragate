---
status: accepted
---

# SQLite for Backend Persistence

The backend uses SQLite for structured data persistence (claims, settings, history) instead of relying solely on Redis. Redis is retained only for TTL-based evidence caching.

**Why**: SQLite provides durable, ACID-compliant storage without requiring a separate database server. Settings, claims, and analysis history need to survive restarts and be queryable. Redis is designed for ephemeral cache data, not structured persistence. SQLite is zero-config, file-based, and included in Python's standard library.

**Trade-off**: SQLite doesn't support concurrent writes as well as PostgreSQL. Mitigated by the single-user hackathon scope — concurrent write contention is not a concern.
