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
| `/v2/companies/` | GET | `where`, `order_by`, `q`, `limit`, `offset` | Filtered/sorted company list | ❌ |
| `/v2/company/report/{symbol}/` | GET | `sections` (csv) | Company report: overview, valuation, future, peers, financials, dividend, management, ownership (8 sections) | ✅ `SectorsClient.get_company_report` |
| `/v2/company/segments/` | GET | `symbol` | Revenue & cost segments | ❌ |
| `/v2/industries/` | GET | — | Industry list | ❌ |
| `/v2/subindustries/` | GET | — | Subindustry list | ❌ |
| `/v2/subsectors/` | GET | — | Subsector list | ❌ |
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
| `/v2/index/daily/{index_code}/` | GET | — | Index daily transaction data | ❌ |

### Rankings & Top

| Endpoint | Method | Params | Returns | Used by Naragate |
|----------|--------|--------|---------|-----------------|
| `/v2/companies/top-changes/` | GET | `classification`, `period` | Top gainers/losers (1d/7d/14d/30d/365d) | ❌ |
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
| `/v2/filings/` | GET | `symbol`, `type` | Insider trading filings | ❌ |
| `/v2/suspensions/` | GET | — | Stock suspensions | ❌ |

### Corporate Actions

| Endpoint | Method | Params | Returns | Used by Naragate |
|----------|--------|--------|---------|-----------------|
| `/v2/company/corporate-actions/{symbol}/` | GET | — | Dividends, rights, splits | ✅ `SectorsClient.get_corporate_actions` |

### Brokers

| Endpoint | Method | Params | Returns | Used by Naragate |
|----------|--------|--------|---------|-----------------|
| `/v2/broker-activity/{broker_code}/` | GET | — | Broker trading activity | ❌ |
| `/v2/broker-summary/{symbol}/` | GET | — | Broker summary for symbol | ❌ |
| `/v2/broker-registry/` | GET | — | Broker registry | ❌ |
| `/v2/brokers/top/` | GET | — | Top brokers | ❌ |
| `/v2/foreign-flow/{symbol}/` | GET | — | Foreign investor flow | ❌ |

---

## SGX Endpoints (`/v2/sgx/...`)

### Company & Screener

| Endpoint | Method | Params | Returns | Naragate candidate |
|----------|--------|--------|---------|-------------------|
| `/v2/sgx/companies/` | GET | `where`, `order_by`, `q`, `limit`, `offset` | SGX company screener | ✅ |
| `/v2/sgx/company/report/{symbol}/` | GET | `sections` (csv) | Company report: overview, valuation, financials, dividend (4 sections) | ✅ |
| `/v2/sgx/sectors/` | GET | — | SGX sector slug list | ✅ |
| `/v2/sgx/subsectors/` | GET | — | SGX sector/subsector pairs | ✅ |
| `/v2/sgx/companies/top/` | GET | `classification` | Top SGX companies | ✅ |

### Daily / Transaction

| Endpoint | Method | Params | Returns | Naragate candidate |
|----------|--------|--------|---------|-------------------|
| `/v2/sgx/daily/{symbol}/` | GET | — | Daily OHLCV (up to 90 days, SGD) | ✅ |

### News & Filings

| Endpoint | Method | Params | Returns | Naragate candidate |
|----------|--------|--------|---------|-------------------|
| `/v2/sgx/news/` | GET | `symbols`, `tags`, `start_date`, `end_date`, `limit` | SGX news articles | ✅ |
| `/v2/sgx/filings/` | GET | `symbol`, `type` | SGX insider filings | ✅ |
| `/v2/sgx/tags/` | GET | — | SGX news tag vocabulary | ❌ |

### Unique to SGX

| Endpoint | Method | Params | Returns | Naragate candidate |
|----------|--------|--------|---------|-------------------|
| `/v2/sgx/short-sell/` | GET | `symbol`, `start_date`, `end_date` | Short sell data | ✅ |
| `/v2/sgx/share-buybacks/` | GET | `symbol`, `start_date`, `end_date` | Share buyback data | ✅ |

### SGX Limitations

- **Annual-only** financials — no quarterly endpoint
- Some fields restricted to ~22 **big caps** only (DBS, OCBC, UOB, etc.)
- No subsector report (only sector list)
- No peer comparison endpoint
- No corporate actions endpoint

---

## KLSE Endpoints (`/v2/klse/...`)

### Company & Sector

| Endpoint | Method | Params | Returns | Naragate candidate |
|----------|--------|--------|---------|-------------------|
| `/v2/klse/companies/` | GET | `sector` (slug) | Companies by sector (symbol + name) | ✅ |
| `/v2/klse/company/report/{symbol}/` | GET | `sections` (csv) | Company report: overview, valuation, financials, dividend (4 sections) | ✅ |
| `/v2/klse/top-companies/` | GET | `classification` | Top KLSE companies | ✅ |
| `/v2/klse/sectors/` | GET | — | KLSE sector slug list | ✅ |
| `/v2/klse/subsectors/` | GET | — | KLSE sector/subsector pairs | ✅ |

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

Current `SectorsClient` methods vs available endpoints:

| Current method | IDX endpoint | SGX equivalent | KLSE equivalent |
|----------------|-------------|----------------|-----------------|
| `get_company_report(ticker, sections)` | `/v2/company/report/{ticker}/` | `/v2/sgx/company/report/{symbol}/` | `/v2/klse/company/report/{symbol}/` |
| `get_quarterly_financials(ticker, n)` | `/v2/financials/quarterly/{ticker}/` | ❌ Not available | ❌ Not available |
| `get_subsector_report(sub_sector, sections)` | `/v2/subsector/report/{sub_sector}/` | ❌ No equivalent | ❌ No equivalent |
| `get_daily_transaction(ticker)` | `/v2/daily/{ticker}/` | `/v2/sgx/daily/{symbol}/` | ❌ Not available |
| `get_news(ticker, limit)` | `/v2/news/` | `/v2/sgx/news/` | ❌ Not available |
| `get_corporate_actions(ticker)` | `/v2/company/corporate-actions/{ticker}/` | ❌ No equivalent | ❌ No equivalent |

### Endpoints to Add — Priority Order

**P0 — Core evidence pipeline per market:**

| New method | IDX | SGX | KLSE | Notes |
|------------|-----|-----|------|-------|
| `get_company_report(market, symbol, sections)` | ✅ | ✅ | ✅ | All 3 markets. Sections differ: IDX=8, SGX/KLSE=4 |
| `get_daily_transaction(market, symbol)` | ✅ | ✅ | ❌ | IDX + SGX only. KLSE has no daily data |
| `get_news(market, symbols, limit)` | ✅ | ✅ | ❌ | IDX + SGX only |
| `get_screener(market, where, order_by)` | ✅ | ✅ | ❌ | IDX + SGX only |

**P1 — Enrichment endpoints (SGX unique value):**

| New method | Market | Notes |
|------------|--------|-------|
| `get_sgx_short_sell(symbol, start, end)` | SGX only | Unique SGX data, valuable for market claims |
| `get_sgx_share_buybacks(symbol, start, end)` | SGX only | Unique SGX data |
| `get_filings(market, symbol)` | IDX + SGX | Insider trading filings |

**P2 — Rankings and discovery:**

| New method | IDX | SGX | KLSE | Notes |
|------------|-----|-----|------|-------|
| `get_top_companies(market, classification)` | ✅ | ✅ | ✅ | All 3 markets |
| `get_sectors(market)` | ✅ | ✅ | ✅ | All 3 markets |
| `get_subsectors(market)` | ✅ | ✅ | ✅ | All 3 markets |

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
