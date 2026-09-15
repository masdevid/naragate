# E2E Tests: Dashboard Claim Templates

**Feature:** The 12 curated narrative templates on the dashboard (`app-dashboard-examples`) drive a
full analysis; the rendered claim, verdict, evidence, skeptic, and policy UI must match the claim
data each template produces.

---

## Overview

Every template is exercised as a data-driven table (`TEMPLATES` in `claim-templates.spec.ts`). Each
case mocks the whole backend:

- `POST /api/v1/stream/evaluate` → a deterministic SSE stream ending in `pipeline_complete`
  (policy templates emit `policy_sector_resolved` + `sector_evidence_ready` instead of
  `evidence_fetching`/`evidence_ready`).
- `GET /api/v1/claims/{claimId}` → the completed claim object.
- `GET /api/v1/precheck/` → policy readback for the three policy templates.
- The ticker-guardrail case (`no_ticker`) instead emits `clarification_required` and asserts the
  claim page halts with no redirect.

Because everything is mocked, runs are deterministic and cost **0 Sectors API calls / 0 LLM calls**.

**Layers under test:**

1. The template tile emits the exact i18n narrative into the scanner textarea.
2. The claim page consumes the pipeline SSE and redirects to `/results/{claimId}` on completion.
3. The results page presents: narrative quote, claim meta (ticker link to `sectors.app/idx/{ticker}`,
   category, direction label), verdict badge + score gauge + active legend band + narration, radar
   dimensions, evidence cards with formatted metrics, skeptic panel, and the policy section.

**Coherence rules enforced per case (does the result "make sense" for the narrative):**

- **Section intent:** the exact set *and order* of `app-evidence-card` titles must equal the case's
  `expectedCardTitles` — e.g. valuation → only `Bukti Valuasi`; market → only `Bukti Pasar`;
  news → `Bukti Fundamental` + `Korelasi Berita`; policy → none. `.policy` appears only when
  `expectsPolicy` is set, and a policy claim must render no evidence cards or orphan help boxes.
- **Verdict ↔ score band:** the displayed gauge score must fall inside the displayed verdict's
  band (`contradicted 0–30`, `mixed 31–60`, `supported 61–80`, `strongly_supported 81–100`), exactly
  one legend band is active, and its range text matches.
- **Narrative ↔ claim:** a ticker-based narrative must actually contain the parsed ticker, and the
  claim meta must show that ticker, its category, and the direction label.

---

## Test Case: `TMPL-E2E-001` — valuation renders the correct claim, verdict and evidence UI

**Priority:** `high` · **Tags:** `@e2e @templates`

**Description/Objective:** Template "PE BBCA mahal di 25x…" (valuation) yields a `supported` verdict
with a single valuation evidence card whose metrics are rendered with id-ID formatting.

**Key verification points:**
- Tile click fills the textarea with the exact narrative; analyze lands on `/claim` then
  `/results/tmpl-valuation`.
- `.results__quote` contains the narrative; `.results__claim` shows ticker `BBCA` with href
  `https://sectors.app/idx/bbca`, category `valuation`, direction `Naik`.
- Badge `[data-verdict="supported"]` shows `Didukung`; gauge `72`; active legend = `Didukung`;
  narration list non-empty; radar legend = 2 dimensions.
- 1 evidence card `Bukti Valuasi`: `Rasio PE 25,00`, `Rasio PB 4,10`, `Premi PE 38,9%`.

---

## Test Case: `TMPL-E2E-002` — fundamental renders the correct claim, verdict and evidence UI

**Priority:** `high` · **Tags:** `@e2e @templates`

**Description/Objective:** Template "Pendapatan TLKM terus tumbuh tapi laba…" (fundamental) yields
a `mixed` verdict and a fundamental card with IDR + trend metrics.

**Key verification points:**
- Verdict `Campuran` (`data-verdict="mixed"`), gauge `48`, direction `Turun`.
- Card `Bukti Fundamental`: `Pendapatan Rp 148,5 M`, `Tren Pendapatan Membaik`, `Tren Laba Menurun`,
  `ROE 12,40`.

---

## Test Case: `TMPL-E2E-003` — market renders the correct claim, verdict and evidence UI

**Priority:** `high` · **Tags:** `@e2e @templates`

**Description/Objective:** Template "Saham UNVR turun 15%…" (market) yields `supported` with a
market card formatted as signed percentages.

**Key verification points:**
- Gauge `78`, direction `Turun`.
- Card `Bukti Pasar`: `Perubahan 1H -1,50%`, `Perubahan 7H -15,00%`, `Perubahan 30H -20,00%`.

---

## Test Case: `TMPL-E2E-004` — news emits both fundamental and news evidence cards

**Priority:** `high` · **Tags:** `@e2e @templates`

**Description/Objective:** Template "BMRI disebut bank terbaik…" emits fundamental + news evidence;
both evidence cards render, with the news corroboration badge and headline link.

**Key verification points:**
- Verdict `Sangat Didukung` (`strongly_supported`), gauge `85`.
- 2 evidence cards: `Bukti Fundamental` (`Pendapatan Rp 140,0 M`) and `Korelasi Berita`
  (`Berita Mendukung Klaim`, summary + `link` to `https://market.example/bmri-rekor`,
  source `market.example`).

---

## Test Cases: `TMPL-E2E-005..007` — policy templates render the policy section and no evidence cards

**Priority:** `high` · **Tags:** `@e2e @templates`

**Description/Objective:** `policy_bbm`, `policy_hba`, `policy_nickel` claims complete with
`is_policy: true`, empty `evidence`, and a mocked `/api/v1/precheck/` payload. The results page must
show the policy section (verdict chip, rationale, beacon list, results table, event agenda) and must
NOT render orphaned evidence/news/filings cards or section-help boxes.

**Key verification points (per template):**
- Verdict badge (BBM `Didukung`/65, HBA `Didukung`/61, Nickel `Didukung`/70), narration present.
- `.policy` visible; `.policy__verdict` = `PASS`, `CONDITIONAL`, `PASS` respectively; table rows
  show ticker, subsector, policy signal, classification; `.policy__event` shows the event title;
  `.policy__beacon-list` = `INCO` for nickel.
- `.evidence .metric`, `.evidence/.news/.filings .section-help` all count `0`.
- Non-policy templates assert `.policy` does not exist.

---

## Test Case: `TMPL-E2E-008` — no-ticker halts at the clarification guardrail

**Priority:** `critical` · **Tags:** `@e2e @templates`

**Description/Objective:** Template "Saham perbankan sedang mahal." has no valid ticker; the stream
ends with `clarification_required`, the claim page shows the guardrail error, and no results
redirect occurs.

**Key verification points:**
- `.claim__error` mentions `kode saham`; `.claim__event-data` contains `needs_clarification` and no
  `evidence_ready`; URL remains `/claim`.

---

## Test Case: `TMPL-E2E-009` — contradiction renders a contradicted verdict

**Priority:** `high` · **Tags:** `@e2e @templates`

**Description/Objective:** Template "Laba BBRI naik tapi sahamnya terus turun…" yields the
`contradicted` band and a market card.

**Key verification points:**
- Badge `Bertentangan` (`data-verdict="contradicted"`), gauge `24`, direction `Turun`.
- Card `Bukti Pasar`: `Perubahan 7H -20,00%`, `Perubahan 30H -25,00%`.
- Skeptic panel shows 1 counter-argument (`80%`), 1 ambiguity section, 1 missing-evidence section.

---

## Test Case: `TMPL-E2E-010` — future-price combines valuation and market cards

**Priority:** `high` · **Tags:** `@e2e @templates`

**Description/Objective:** Template "Harga saham BBCA akan berlipat…" emits valuation + market
evidence → `mixed` verdict with exactly 2 evidence cards.

**Key verification points:**
- Verdict `Campuran` (`mixed`), gauge `55`; `app-evidence-card` count = 2; radar legend = 3
  dimensions.

---

## Test Cases: `TMPL-E2E-011..012` — below-CPO / below-auto fundamental pushes (declining trend)

**Priority:** `high` · **Tags:** `@e2e @templates`

**Description/Objective:** Templates "Harga CPO turun — laba AALI tertekan." and "Penjualan mobil
melemah…" yield `supported` verdicts with a fundamental card showing declining trends.

**Key verification points:**
- AALI: verdict `Didukung`, gauge `74`; ASII: verdict `Didukung`, gauge `69`.
- Both cards show `Tren Pendapatan Menurun`, `Tren Laba Menurun`.

---

## Notes

- Fixtures live in `claim-templates.spec.ts` (`TEMPLATES`, `claimStream`, `completedClaim`,
  `mockTemplateBackend`) and the page helpers in `claim-templates.ts` (`TemplateFlow`).
- Formatted-value expectations use verified id-ID output from `format.service.ts`
  (e.g. `-1,50%`, `Rp 148,5 M`).
- Matches the "hard constraint" that every test that touches Sectors is credit-efficient: the
  evaluate stream and claim readback are fully mocked, so the same rules that keep `analysis`
  zero-credit apply here by construction (assert on presentation, never on live credits).