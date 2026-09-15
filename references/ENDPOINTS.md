# Sectors v2 API — Endpoint Coverage by Market

> Source: `https://api.sectors.app` · Auth: `Authorization: <api_key>` · Spec: `https://docs.sectors.app/schema.json`

## Markets

| Market | Path prefix | Symbol format | Currency | Coverage |
|--------|------------|---------------|----------|----------|
| **IDX** (Indonesia) | `/v2/` | 4-letter alpha, e.g. `BBCA` (`.JK` optional on input) | IDR | 99.9%+ |
| **SGX** (Singapore) | `/v2/sgx/` | 3–4 char alphanumeric, e.g. `D05`, `U11` (`.SI` optional on input) | SGD | ~80% (large/mid caps) |
| **KLSE** (Malaysia) | `/v2/klse/` | 4-digit numeric, e.g. `1155`, `4197` | MYR | Limited — reports + sectors + rankings |
| **Mining** (Indonesia ext) | `/v2/mining/` | Commodity/company slugs | IDR | Mining sector only |

## Per-endpoint Cost

| Call type | Credits |
|-----------|---------|
| Most endpoints | 1 |
| Company Report (multi-section) | 1 per section (IDX default 8, SGX/KLSE default 4) |
| Subsector Report (multi-section) | 1 per section (IDX default 6) |
| Quarterly Financials | 1 per quarter returned |
| Screener — structured `where`/`order_by` | 1 |
| Screener — natural language `?q=` | 3 |
| 404 (not found) | 1 (lookup ran) |
| 400/401/403/429/5xx | 0 (server error, not billed) |

---

## IDX Endpoints (`/v2/...`)

### Company & Screener

| Endpoint | Method | Params | Returns | Used by Naragate |
|----------|--------|--------|---------|-----------------|
| `/v2/companies/` | GET | `where`, `order_by`, `q`, `limit`, `offset` | Filtered/sorted company list | ✅ ticker validation cache (`_ensure_company_cache`, `limit=10000`); screener params (❌) unused |
| `/v2/company/report/{symbol}/` | GET | `sections` (csv) | Company report: overview, valuation, future, peers, financials, dividend, management, ownership (8 sections) | ✅ `SectorsClient.get_company_report` |
| `/v2/company/get-segments/{symbol}/` | GET | `financial_year` | Sankey revenue/cost segments `{revenue_breakdown: [{value, source, target}]}` | ✅ `SectorsClient.get_segments` → FundamentalAgent (`segments.top_sources`) |
| `/v2/industries/` | GET | — | Industry list | ❌ |
| `/v2/subindustries/` | GET | — | Subindustry list | ❌ |
| `/v2/subsectors/` | GET | — | Subsector list | ✅ subsector-slug validation cache (`_ensure_subsector_cache`) |
| `/v2/tags/` | GET | — | News tag vocabulary | ❌ |
| `/v2/companies/free-float/` | GET | — | Free float data | ❌ |

### Financials

| Endpoint | Method | Params | Returns | Used by Naragate |
|----------|--------|--------|---------|-----------------|
| `/v2/financials/quarterly/{symbol}/` | GET | `n_quarters`, `report_date`, `approx` | Quarterly financial statements | ✅ `SectorsClient.get_quarterly_financials` |
| `/v2/companies/quarterly-dates/` | GET | — | Latest quarterly dates universe | ❌ |
| `/v2/company/quarterly-dates/{symbol}/` | GET | — | Quarterly dates for symbol | ❌ |

### Subsector

| Endpoint | Method | Params | Returns | Used by Naragate |
|----------|--------|--------|---------|-----------------|
| `/v2/subsector/report/{sub_sector}/` | GET | `sections` (csv) | Subsector report: statistics, market_cap, stability, valuation, growth, companies (6 sections) | ✅ `SectorsClient.get_subsector_report` |

### Daily / Transaction

| Endpoint | Method | Params | Returns | Used by Naragate |
|----------|--------|--------|---------|-----------------|
| `/v2/daily/{symbol}/` | GET | — | Daily OHLCV + market_cap (up to 90 days) | ✅ `SectorsClient.get_daily_transaction` |
| `/v2/daily/close-universe/` | GET | `date` | Full-universe daily close (paginated) | ❌ |
| `/v2/idx/total/` | GET | — | IDX total market cap history | ❌ |
| `/v2/index-daily/{index_code}/` | GET | `start`, `end` | Index daily close `[{index_code, date, price}]` (≤90d; codes `ihsg`, `lq45`, …) | ✅ `SectorsClient.get_index_daily` → MarketAgent relative strength (90-day epoch cache) |

### Rankings & Top

| Endpoint | Method | Params | Returns | Used by Naragate |
|----------|--------|--------|---------|-----------------|
| `/v2/companies/top-changes/` | GET | `classifications` (csv), `periods` (csv), `n_stock`, `sub_sector`, `min_mcap_billion` | Top gainers/losers (1d/7d/14d/30d/365d) | ✅ `SectorsClient.get_top_changes` → MarketAgent (`market_movers`); **1 credit per classification×period** — always pass explicit args (default omit = 10 credits) |
| `/v2/ranking/most-traded/` | GET | `date`, `limit` | Most traded by volume | ❌ |
| `/v2/ranking/top-tickers/` | GET | `classification`, `limit` | Top companies by classification | ❌ |

### IPO

| Endpoint | Method | Params | Returns | Used by Naragate |
|----------|--------|--------|---------|-----------------|
| `/v2/ipo/performance/{symbol}/` | GET | — | Price change since listing | ❌ |

### News & Filings

| Endpoint | Method | Params | Returns | Used by Naragate |
|----------|--------|--------|---------|-----------------|
| `/v2/news/` | GET | `symbols`, `tags`, `start_date`, `end_date`, `limit` | News articles | ✅ `SectorsClient.get_news` |
| `/v2/filings/` | GET | `symbol`, `transaction_type` | Insider trading filings | ✅ `SectorsClient.get_filings` → `FilingsAgent` (`transaction_type` ∈ buy/sell/others; `type` is rejected 400) |
| `/v2/suspensions/` | GET | — | Stock suspensions | ❌ |

### Corporate Actions

| Endpoint | Method | Params | Returns | Used by Naragate |
|----------|--------|--------|---------|-----------------|
| `/v2/company/corporate-actions/{symbol}/` | GET | — | Dividends, rights, splits | ✅ `SectorsClient.get_corporate_actions` |

### Brokers

| Endpoint | Method | Params | Returns | Used by Naragate |
|----------|--------|--------|---------|-----------------|
| `/v2/broker-activity/{broker_code}/` | GET | — | Broker trading activity | ❌ |
| `/v2/broker-summary/{symbol}/` | GET | `start`, `end`, `broker_code` | Per-broker daily rows `{data:[{date, summary:[{broker_code,bval,sval,nval,...}]}]}` (≤14d) | ✅ `SectorsClient.get_broker_summary` → MarketAgent (`flow_summary.broker_net`/`broker_bias`) |
| `/v2/broker-registry/` | GET | — | Broker registry | ❌ |
| `/v2/brokers/top/` | GET | — | Top brokers | ❌ |
| `/v2/foreign-flow/{symbol}/` | GET | `start`, `end` | Daily net foreign inflow `{data:[{date, net_foreign_inflow}]}` (≤90d) | ✅ `SectorsClient.get_foreign_flow` → MarketAgent (`flow_summary.foreign_net`/`foreign_bias`) |

---

## SGX Endpoints (`/v2/sgx/...`)

> **Not implemented — API-compatible only.** The `SectorsClient` and every
> evidence agent are IDX-only (hardcoded `/v2/...` paths, no `market` routing).
> SGX/KLSE rows below document what the Sectors API *offers*, not what Naragate
> currently consumes.

### Company & Screener

| Endpoint | Method | Params | Returns | Implemented? |
|----------|--------|--------|---------|--------------|
| `/v2/sgx/companies/` | GET | `where`, `order_by`, `q`, `limit`, `offset` | SGX company screener | ❌ |
| `/v2/sgx/company/report/{symbol}/` | GET | `sections` (csv) | Company report: overview, valuation, financials, dividend (4 sections) | ❌ |
| `/v2/sgx/sectors/` | GET | — | SGX sector slug list | ❌ |
| `/v2/sgx/subsectors/` | GET | — | SGX sector/subsector pairs | ❌ |
| `/v2/sgx/companies/top/` | GET | `classification` | Top SGX companies | ❌ |

### Daily / Transaction

| Endpoint | Method | Params | Returns | Implemented? |
|----------|--------|--------|---------|--------------|
| `/v2/sgx/daily/{symbol}/` | GET | — | Daily OHLCV (up to 90 days, SGD) | ❌ |

### News & Filings

| Endpoint | Method | Params | Returns | Implemented? |
|----------|--------|--------|---------|--------------|
| `/v2/sgx/news/` | GET | `symbols`, `tags`, `start_date`, `end_date`, `limit` | SGX news articles | ❌ |
| `/v2/sgx/filings/` | GET | `symbol`, `type` | SGX insider filings | ❌ |
| `/v2/sgx/tags/` | GET | — | SGX news tag vocabulary | ❌ |

### Unique to SGX

| Endpoint | Method | Params | Returns | Implemented? |
|----------|--------|--------|---------|--------------|
| `/v2/sgx/short-sell/` | GET | `symbol`, `start_date`, `end_date` | Short sell data | ❌ |
| `/v2/sgx/share-buybacks/` | GET | `symbol`, `start_date`, `end_date` | Share buyback data | ❌ |

### SGX Limitations

- **Annual-only** financials — no quarterly endpoint
- Some fields restricted to ~22 **big caps** only (DBS, OCBC, UOB, etc.)
- No subsector report (only sector list)
- No peer comparison endpoint
- No corporate actions endpoint

---

## KLSE Endpoints (`/v2/klse/...`)

> **Not implemented — API-compatible only** (see note above the SGX section).

### Company & Sector

| Endpoint | Method | Params | Returns | Implemented? |
|----------|--------|--------|---------|--------------|
| `/v2/klse/companies/` | GET | `sector` (slug) | Companies by sector (symbol + name) | ❌ |
| `/v2/klse/company/report/{symbol}/` | GET | `sections` (csv) | Company report: overview, valuation, financials, dividend (4 sections) | ❌ |
| `/v2/klse/top-companies/` | GET | `classification` | Top KLSE companies | ❌ |
| `/v2/klse/sectors/` | GET | — | KLSE sector slug list | ❌ |
| `/v2/klse/subsectors/` | GET | — | KLSE sector/subsector pairs | ❌ |

### KLSE Limitations

- **No screener** (no `/klse/companies/` with `where`/`order_by`)
- **No quarterly financials** endpoint
- **No daily transaction** endpoint
- **No news** endpoint
- **No filings** endpoint
- **No corporate actions** endpoint
- Company reports only (4 sections, same as SGX)

---

## Mining Extension (`/v2/mining/...`)

| Endpoint | Method | Params | Returns |
|----------|--------|--------|---------|
| `/v2/mining/companies/` | GET | `commodity`, `status`, `limit`, `offset` | Mining companies list |
| `/v2/mining/companies/{slug}/` | GET | — | Company detail |
| `/v2/mining/companies/{slug}/financials/` | GET | — | Financial statements |
| `/v2/mining/companies/{slug}/ownership/` | GET | — | Ownership structure |
| `/v2/mining/companies/{slug}/performance/` | GET | — | Performance metrics |
| `/v2/mining/commodities/` | GET | — | Commodity list |
| `/v2/mining/commodities/{commodity}/price/` | GET | — | Commodity price history |
| `/v2/mining/export-destination/` | GET | — | Export destination data |
| `/v2/mining/sites/` | GET | — | Mining sites list |
| `/v2/mining/sites/{slug}/` | GET | — | Site detail |
| `/v2/mining/contracts/` | GET | — | Mining contracts |
| `/v2/mining/licenses/` | GET | — | Mining licenses |

---

## Coverage Matrix — Naragate Evidence Dimensions

How each evidence dimension maps to available endpoints per market.
**SGX/KLSE columns describe Sectors API capability only — Naragate does not
implement those markets yet; only the IDX column is wired up today.**

### ValuationAgent

| Dimension | IDX | SGX | KLSE |
|-----------|-----|-----|------|
| Valuation metrics (P/E, P/B, EV/EBITDA, etc.) | ✅ Company Report → valuation section | ✅ Company Report → valuation section | ✅ Company Report → valuation section |
| Peer comparison | ✅ Company Report → peers section | ❌ No peers section | ❌ No peers section |
| Subsector benchmarks | ✅ Subsector Report | ❌ No subsector report | ❌ No subsector report |

### FundamentalAgent

| Dimension | IDX | SGX | KLSE |
|-----------|-----|-----|------|
| Revenue/profit trends | ✅ Quarterly Financials | ⚠️ Annual only (from report) | ⚠️ Annual only (from report) |
| Balance sheet health | ✅ Quarterly Financials | ⚠️ Annual only | ⚠️ Annual only |
| Dividend history | ✅ Company Report → dividend | ✅ Company Report → dividend | ✅ Company Report → dividend |
| Management & ownership | ✅ Company Report → management, ownership | ❌ Not in SGX report | ❌ Not in KLSE report |

### MarketAgent

| Dimension | IDX | SGX | KLSE |
|-----------|-----|-----|------|
| Price momentum (OHLCV) | ✅ Daily Transaction (90d) | ✅ SGX Daily (90d) | ❌ No daily endpoint |
| Volume trends | ✅ Daily Transaction | ✅ SGX Daily | ❌ |
| Market cap changes | ✅ Daily Transaction | ✅ SGX Daily | ❌ |
| Top movers | ✅ Top Changes / Rankings | ✅ SGX Top Companies | ✅ KLSE Top Companies |
| Short interest | ❌ | ✅ SGX Short Sell | ❌ |
| Buyback activity | ❌ | ✅ SGX Share Buybacks | ❌ |

### NewsAgent

| Dimension | IDX | SGX | KLSE |
|-----------|-----|-----|------|
| News articles | ✅ `/v2/news/` | ✅ `/v2/sgx/news/` | ❌ No news endpoint |
| Insider filings | ✅ `/v2/filings/` | ✅ `/v2/sgx/filings/` | ❌ |

### CorporateActionsAgent

| Dimension | IDX | SGX | KLSE |
|-----------|-----|-----|------|
| Dividends, splits, rights | ✅ Corporate Actions endpoint | ❌ No endpoint | ❌ No endpoint |

---

## Naragate Client Coverage

Current `SectorsClient` methods vs available endpoints. **All methods are IDX-only
and hit the hardcoded `/v2/...` path — there is no `market` parameter or
SGX/KLSE/Mining routing anywhere in the client or agents.**

| Current method | Endpoint(s) | Consumer |
|----------------|-------------|----------|
| `validate_ticker_exists` → `_ensure_company_cache` | `/v2/companies/` (`limit=10000`, 24h in-process cache) | `pipeline.py` pre-check |
| `validate_subsector` → `_ensure_subsector_cache` | `/v2/subsectors/` (24h in-process cache) | subsector-slug guard |
| `get_company_report(ticker, sections)` | `/v2/company/report/{ticker}/` | ValuationAgent, FundamentalAgent |
| `get_quarterly_financials(ticker, n)` | `/v2/financials/quarterly/{ticker}/` | FundamentalAgent |
| `get_subsector_report(sub_sector, sections)` | `/v2/subsector/report/{sub_sector}/` | ValuationAgent |
| `get_daily_transaction(ticker, start, end)` | `/v2/daily/{ticker}/` | MarketAgent, `policy_signal.py`, `main.py` health check |
| `get_news(ticker, limit)` | `/v2/news/` | NewsAgent |
| `get_filings(ticker, transaction_type)` | `/v2/filings/` | FilingsAgent |
| `get_corporate_actions(ticker)` | `/v2/company/corporate-actions/{ticker}/` | CorporateActionsAgent |
| `get_foreign_flow(ticker, start, end)` | `/v2/foreign-flow/{ticker}/` | MarketAgent (Evidence Graph `foreign_flow`, daily TTL) |
| `get_broker_summary(ticker, start, end)` | `/v2/broker-summary/{ticker}/` | MarketAgent (Evidence Graph `broker_summary`, daily TTL) |
| `get_top_changes(classifications, periods, n_stock)` | `/v2/companies/top-changes/` | MarketAgent (market-wide day cache `top-changes:{date}:1d`) |
| `get_segments(ticker, financial_year)` | `/v2/company/get-segments/{ticker}/` | FundamentalAgent (Evidence Graph `segments`) |
| `get_index_daily(index_code, start, end)` | `/v2/index-daily/{index_code}/` | MarketAgent relative strength (`evidence:index:{code}:{epoch}`) |

Available SGX/KLSE equivalents (`/v2/sgx/...`, `/v2/klse/...`) are **not**
implemented — they would require a `market`-aware client and agent routing.

### Endpoints to Add — Priority Order

**P0 — Core evidence pipeline:** ✅ done for IDX (all methods above).
Multi-market routing (`market` param on the client + `/v2/sgx`, `/v2/klse`
dispatch) remains unbuilt.

**P1 — Enrichment endpoints (SGX unique value):**

| New method | Market | Notes |
|------------|--------|-------|
| `get_sgx_short_sell(symbol, start, end)` | SGX only | Unique SGX data, valuable for market claims |
| `get_sgx_share_buybacks(symbol, start, end)` | SGX only | Unique SGX data |

**P2 — Rankings and discovery:**

| New method | IDX | SGX | KLSE | Notes |
|------------|-----|-----|------|-------|
| `get_top_companies(market, classification)` | ✅ | ✅ | ✅ | All 3 markets |
| `get_sectors(market)` | ✅ | ✅ | ✅ | All 3 markets |
| `get_subsectors(market)` | ✅ | ✅ | ✅ | All 3 markets (IDX slug cache exists) |

---

## Unused IDX Endpoints — Enrichment Assessment

Endpoints Naragate does **not** call today, and whether each can enrich features.
Scored against the existing evidence dimensions (valuation, fundamental, market,
news, filings, corporate actions) and the Reality Gap Score.

### ✅ Implemented (high-value slices)

| Endpoint | Credits | Enriches | Status |
|----------|---------|----------|--------|
| `/v2/foreign-flow/{symbol}/` | 1 | MarketAgent | ✅ `get_foreign_flow` → Evidence Graph `foreign_flow`, normalised into `flow_summary.foreign_net` / `foreign_bias`. |
| `/v2/broker-summary/{symbol}/` | 1 | MarketAgent | ✅ `get_broker_summary` → Evidence Graph `broker_summary`, normalised into `flow_summary.broker_net` / `broker_bias`. |
| `/v2/companies/top-changes/` | 1 per class×period | MarketAgent | ✅ `get_top_changes` → day-keyed market cache, surfaces `market_movers` (rank + classification). |
| `/v2/company/get-segments/{symbol}/` | 1 | FundamentalAgent | ✅ `get_segments` → Evidence Graph `segments`, summarised to `top_sources` with share %. |
| `/v2/index-daily/{index_code}/` | 1 | MarketAgent | ✅ `get_index_daily` → 90-day epoch cache, produces `relative_strength` (stock − index) per window. |

All are cache-first (0 credits on a warm graph) and tolerate API failures
without failing the claim. Parity is exposed via `sectors/*` REST + MCP tools
(`skills/{market,fundamental}-agent/tools.yaml`). The judge then consumes
`flow_summary` (±10 pts), `market_movers` (±5 pts), and `relative_strength`
(replaces the raw 1d move when present) inside `market_momentum_gap`. Because
the modifiers sum on one dimension (±15 pts ⇒ up to ±6 on a market claim's
total), the explanation emits a bilingual "propped up by flow despite index
underperformance" note whenever the beta-adjusted move opposes the claim while
flow/movers support it — keeping the tension visible in the human-facing summary.

### High value — still unused

| Endpoint | Credits | Enriches | Why it fits Naragate |
|----------|---------|----------|----------------------|
| `/v2/broker-activity/{broker_code}/` | 1 | MarketAgent | Complements broker summary; per-broker net buy/sell context (chained off `broker-summary`). |
| `/v2/ranking/top-tickers/` | 1 | Peer/ranking discovery | Classification-based top lists give peer sets when no peers section exists. |

### Medium value — new feature surface or better filtering

| Endpoint | Credits | Enriches | Why |
|----------|---------|----------|-----|
| `/v2/ranking/most-traded/` | 1 | MarketAgent | Liquidity/volume context; supports "ramai diperdagangkan" claims. |
| `/v2/ipo/performance/{symbol}/` | 1 | New IPO dimension | Only way to verify "IPO naik X%" narratives. |
| `/v2/suspensions/` | 1 | News/risk context | Verifies "di-suspend" claims and flags halted stocks before scoring. |
| `/v2/news/` `tags` param | 0 extra | NewsAgent | Already using `/v2/news/`; passing `tags` (from `/v2/tags/`) sharpens relevance. |
| `/v2/daily/close-universe/` | paginated | Pre-check / screening | Universe-wide close for cheap relative screening without per-ticker calls. |
| `/v2/companies/quarterly-dates/{symbol}/` | 1 | Freshness scheduling | Know whether a new quarter exists before refetching financials — can *reduce* credits, not just enrich. |

### Low value — discovery/vocabulary, no narrative enrichment

| Endpoint | Why it does not enrich claims |
|----------|-------------------------------|
| `/v2/industries/`, `/v2/subindustries/` | Static taxonomy; subsector slugs already come from the company report overview. |
| `/v2/tags/` | Vocabulary only; useful as an input to news filtering, not as evidence. |
| `/v2/companies/free-float/` | Ownership data already reachable via the company report's ownership section. |
| `/v2/broker-registry/`, `/v2/brokers/top/` | Reference data for the broker endpoints above; no standalone claim signal. |
| `/v2/companies/quarterly-dates/` (universe) | Scheduling helper, superseded by the per-symbol variant. |
| `/v2/idx/total/` | Aggregate market-cap history; index-level only, weak per-claim relevance. |
| `/v2/ipo/performance/` (when not an IPO claim) | Niche; only fires on the IPO claim type. |
| Mining extension (`/v2/mining/...`) | Separate commodity dataset oriented to mining supply chains, not equity-claim verification. |

### Credit note

The shipped slices follow the cache discipline required by repo `AGENTS.md`:
`foreign-flow`/`broker-summary`/`segments` merge under the ticker key,
`top-changes` is cached per trading day in a market-wide namespace, and
`index-daily` is chunked on the same fixed 90-day grid as `/v2/daily/`. Any
remaining candidate must do the same and prove a warm run costs 0 credits.

---

## Symbol Format Reference

| Market | Format | Example | Suffix on input | Suffix in response |
|--------|--------|---------|-----------------|-------------------|
| IDX | 4-letter alpha | `BBCA`, `BBRI`, `TLKM` | `.JK` optional | Always without suffix |
| SGX | 3–4 char alphanumeric | `D05`, `U11`, `Z74`, `TCPD` | `.SI` optional | Always with `.SI` |
| KLSE | 4-digit numeric | `1155`, `4197`, `5225` | None | Without suffix |

---

## Currency Reference

| Market | Currency | Formatting |
|--------|----------|------------|
| IDX | IDR | `RpX` or raw number |
| SGX | SGD | `$X.XX` or raw number |
| KLSE | MYR | `RMX` or raw number |
