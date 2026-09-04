---
status: accepted
---

# 1,600-Credit Budget Optimization Strategy

The system is designed around a strict 1,600-credit budget (1,000 hackathon + 600 onboarding) with caching as the primary optimization mechanism.

**Why**: The Sectors API grant is finite and non-renewable. Every API call consumes credits. The budget constraint shapes every architectural decision: shared Evidence Graph cache, TTL-based refresh, curated stock universe (~5–10 stocks), and per-claim-package cost of ~4 API calls (allowing ~400 claim packages total).

**Budget allocation**:
- Initial company universe/discovery: 10
- Subsector metadata: 10
- Company evidence cache: 200
- Quarterly evidence: 300
- Peer/subsector evidence: 100
- News corpus: 200
- Demo/testing: 300
- Buffer: 480

**Trade-off**: The curated stock universe means claims against stocks outside the pre-cached list trigger new API calls, consuming budget faster. Mitigated by limiting the MVP to the curated set and rejecting out-of-scope claims gracefully.
