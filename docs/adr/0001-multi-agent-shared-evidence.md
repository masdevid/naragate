---
status: accepted
---

# Multi-Agent Architecture with Shared Evidence Store

The pipeline uses a multi-agent architecture where 7 specialized agents (Claim Parser, Valuation Agent, Fundamental Agent, Market Agent, Skeptic Agent, Evidence Judge, Reality Gap Score Generator) share a per-stock Evidence Graph cache rather than each agent fetching independently.

**Why**: Independent fetching would exhaust the 1,600-credit budget quickly. A shared cache ensures each stock's data is fetched once and reused across all agents and claims. The Skeptic Agent, in particular, must challenge the same evidence the validating agents already retrieved — fetching separate counter-evidence would double the API cost.

**Trade-off**: Agents are coupled to the cache's freshness model. If the Evidence Graph is stale, all agents work with potentially outdated data. Mitigated by TTL-based refresh per data type (24h for company reports, 1h for daily transaction data).
