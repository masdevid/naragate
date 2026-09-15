# E2E Tests: Production History

Two suites cover the live `/history` ("Riwayat & Tren") page with **real backend data**
(no route mocks against the live backend).

## Read-only verification (safe, zero credits)

`history-page.spec.ts` — `@HIST-E2E-001`

Loads the real `/api/v1/claims/` + `/api/v1/claims/summary`, then asserts the presented history is
coherent:

- summary `total_analyses` == number of completed claims, `average_score` == their mean (rounded),
  and `verdict_distribution` sums to the total;
- every stored score falls inside its verdict's band (`0–30/31–60/61–80/81–100`);
- the list renders one row per claim, every completed narrative is listed as `Selesai`, the
  guardrail claim as `Gagal`, and no `undefined`/`NaN`/`{{…}}` leaks into the page;
- the trend header shows the total and average, and each verdict band shows its count;
- clicking a row opens `/results/{claim_id}` where the quote, gauge, badge and active legend
  band agree with the stored claim.

Runs in the normal suite; **skips** when the live store has no completed claims.

## Real generation (OPT-IN — spends credits)

`generate-history.spec.ts` — drives all 12 dashboard templates through the **real** pipeline
(real LLM + real Sectors API) so genuine completed claims are persisted and appear on the
production `/history` page. It is **skipped unless** `RUN_REAL_PIPELINE=1`.

```bash
RUN_REAL_PIPELINE=1 npx playwright test e2e/history -g "generate:" --reporter=list
```

Credit discipline:

- Each narrative runs once; the backend dedupes active narratives and caches evidence per
  ticker/sector/day, so repeated tickers (e.g. BBCA in valuation + future-price) reuse cache.
- Per-template failures are recorded, not retried.
- Outcomes are written to `generated-results.json` (id, status, claim_id, score, verdict).

Observed cost of a full 12-template run: **+42 Sectors calls, +12 cache hits, +34 LLM calls**
(1 pre-existing claim), total wall time ~12 min. Compare `/api/v1/usage` before and after.

`no-ticker` is the deliberate guardrail case: it never completes, so the store gains a `failed`
record for it rather than a scored result.
