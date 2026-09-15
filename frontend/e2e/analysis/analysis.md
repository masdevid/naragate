# E2E Tests: Analysis Edge Cases

**Feature:** Analysis pipeline edge cases (ticker guardrail & stuck-claim recovery)

---

## Test Case: `ANALYSIS-E2E-001` — Narrative without a ticker halts before evidence

**Priority:** `critical`

**Tags:**
- type → @e2e
- feature → @analysis

**Description/Objective:** A narrative that yields no valid 4-letter ticker must halt the pipeline
at the clarification guardrail — before any credit-consuming evidence call — and surface the
clarification signal in the UI.

**Preconditions:**
- Frontend up (default `http://localhost:4273`), configured to a running backend (`/api` proxied).
- The `/api/v1/stream/evaluate` SSE endpoint is mocked to emit the clarification flow.

### Flow Steps:
1. Open the dashboard and enter a narrative with no ticker (e.g. "Saham perbankan mahal").
2. Click the analyze button, landing on `/claim`.
3. The mocked stream emits `pipeline_started`, `claim_parsing`, `claim_parsed` (with
   `needs_clarification` + `missing: ["ticker"]`), then `clarification_required`.

### Expected Result:
- The clarification message ("… Mohon berikan ticker saham …") is shown in the error block.
- The pipeline never reaches the evidence stage; the claim page stays on `/claim`.

### Key verification points:
- `.claim__error` contains the clarification message.
- `.claim__error` shows the clarification message; the page stays on `/claim`.

### Notes:
- The evaluate endpoint is mocked so the test is deterministic and hits no real Sectors/LLM calls.
- Also exercises the backend `clarification_required` SSE contract end-to-end.

---

## Test Case: `ANALYSIS-E2E-002` — Stuck "parsed" claim retry runs a fresh analysis

**Priority:** `high`

**Tags:**
- type → @e2e
- feature → @analysis

**Description/Objective:** A claim stored at a non-terminal status (`parsed`/`evidence_retrieved`)
must not show "Still Processing" forever or bounce on retry. Clicking "Coba Lagi" supersedes the
stuck claim and runs a fresh pipeline that lands on the new completed result.

**Preconditions:**
- A claim in storage with `status: "parsed"` (read back via `/api/v1/claims/{id}`).
- The `/api/v1/stream/evaluate` endpoint mocked to emit a full success stream that completes with a
  new `claim_id`.

### Flow Steps:
1. Open `/results/stuck-claim` directly.
2. Assert the "Still Processing" banner (`.results__status`) is shown.
3. Click the retry button (`Coba Lagi`).
4. The app navigates to `/claim?narrative=…`, runs the mocked fresh pipeline, and redirects to
   `/results/new-claim` on `pipeline_complete`.
5. The new claim is stored as `completed` and rendered without the status banner.

### Expected Result:
- Retry does not loop back to the stuck claim — it lands on the new completed analysis.
- No "Still Processing" banner on the final results page.

### Key verification points:
- `expectStillProcessing()` passes on the stuck claim and `expectCompleted()` on the rerun.
- URL ends at `/results/new-claim`.

### Notes:
- Mirrors the backend fix: a non-terminal claim not running in-process is superseded (marked failed)
  so the fresh run proceeds instead of emitting `pipeline_duplicate`.