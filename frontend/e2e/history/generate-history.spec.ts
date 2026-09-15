import { test, expect } from '@playwright/test';
import { writeFileSync, mkdirSync, readFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';

/**
 * REAL pipeline runs — this spec is SKIPPED by default and only runs when
 * RUN_REAL_PIPELINE=1. It drives each dashboard template through the live
 * backend (real LLM + real Sectors API) so genuine, completed claims are
 * persisted and appear on the production /history page.
 *
 * Credit discipline:
 *  - Each narrative runs exactly once (the backend dedupes active narratives and
 *    caches evidence per ticker/sector/day), so repeated templates reuse cache.
 *  - Record the /api/v1/usage delta before/after to prove the cost.
 *  - Per-template failures are recorded, not retried, so a flaky run never
 *    re-spends credits or blocks the rest of the batch.
 */

const RUN = process.env.RUN_REAL_PIPELINE === '1';
const OUT = join(process.cwd(), 'e2e', 'history', 'generated-results.json');

test.skip(!RUN, 'set RUN_REAL_PIPELINE=1 to spend real Sectors/LLM credits');

interface TemplateInput {
  id: string;
  tile: string;
  narrative: string;
  clarify?: boolean;
}

export const TEMPLATE_INPUTS: TemplateInput[] = [
  { id: 'valuation', tile: 'PE BBCA mahal', narrative: 'PE BBCA mahal di 25x, jauh di atas rata-rata sektor 18x.' },
  { id: 'fundamental', tile: 'TLKM', narrative: 'Pendapatan TLKM terus tumbuh tapi laba bersihnya menyusut setiap kuartal.' },
  { id: 'market', tile: 'UNVR', narrative: 'Saham UNVR turun 15% dalam seminggu, investor panik.' },
  { id: 'news', tile: 'BMRI', narrative: 'BMRI disebut bank terbaik di Indonesia saat ini setelah berita laba rekor.' },
  { id: 'policy-bbm', tile: 'Subsidi BBM', narrative: 'Subsidi BBM dipangkas — harga BBM bersubsidi naik kuartal ini.' },
  { id: 'policy-hba', tile: 'ADRO', narrative: 'HBA batu bara ditetapkan naik untuk Q3 — untung ADRO ikut naik.' },
  { id: 'policy-nickel', tile: 'INCO', narrative: 'Larangan ekspor bijih nikel diperketat — INCO untung dari hilirisasi.' },
  { id: 'no-ticker', tile: 'perbankan sedang mahal', narrative: 'Saham perbankan sedang mahal.', clarify: true },
  { id: 'contradiction', tile: 'BBRI', narrative: 'Laba BBRI naik tapi sahamnya terus turun 20% bulan ini.' },
  { id: 'future-price', tile: 'BBCA akan berlipat', narrative: 'Harga saham BBCA akan berlipat tahun ini.' },
  { id: 'below-cpo', tile: 'AALI', narrative: 'Harga CPO turun — laba AALI tertekan.' },
  { id: 'below-auto', tile: 'ASII', narrative: 'Penjualan mobil melemah kuartal ini — pendapatan ASII akan merosot.' },
];

interface GeneratedResult {
  id: string;
  status: 'completed' | 'failed' | 'clarified';
  claimId?: string;
  score?: string | null;
  verdict?: string | null;
  error?: string | null;
}

function record(results: GeneratedResult[]): void {
  mkdirSync(dirname(OUT), { recursive: true });
  writeFileSync(OUT, JSON.stringify(results, null, 2));
}

// Authoritative read-back: poll the live store for the claim of a narrative.
async function findByNarrative(request: any, narrative: string, timeoutMs: number): Promise<any | null> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const claims = await (await request.get('/api/v1/claims/?limit=50')).json();
    const claim = claims.find((c: any) => c.narrative === narrative);
    if (claim && (claim.status === 'completed' || claim.status === 'failed')) return claim;
    await new Promise((r) => setTimeout(r, 3000));
  }
  return null;
}

// Merge with prior batches so separate invocations accumulate.
const allResults: GeneratedResult[] = existsSync(OUT) ? JSON.parse(readFileSync(OUT, 'utf8')) : [];
function upsert(r: GeneratedResult): void {
  const i = allResults.findIndex(x => x.id === r.id);
  if (i >= 0) allResults[i] = r;
  else allResults.push(r);
  record(allResults);
}

// No serial mode: a slow/failed template must not skip the rest.
test.describe('Real pipeline history generation', () => {
  test.setTimeout(900_000);

  for (const t of TEMPLATE_INPUTS) {
    test(`generate: ${t.id}`, async ({ page, request }, testInfo) => {
      await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
      await page.locator('.examples__card').filter({ hasText: t.tile }).first().click();
      await expect(page.locator('textarea.input-section__field')).toHaveValue(t.narrative);
      await page.locator('button.input-section__btn').click();
      await expect(page).toHaveURL(/\/claim/);

      if (t.clarify) {
        await expect(page.locator('.claim__error')).toBeVisible({ timeout: 120_000 });
        upsert({ id: t.id, status: 'clarified' });
        return;
      }

      // Give the real UI a generous window to finish; a policy run can take
      // several minutes. If it is still going, fall through to the authoritative
      // API read so a slow pipeline never fails the batch.
      try {
        await expect(page).toHaveURL(/\/results\//, { timeout: 480_000 });
      } catch {
        /* recorded from the API below */
      }

      const claim = await findByNarrative(request as any, t.narrative, 180_000);
      if (claim && claim.status === 'completed') {
        const result: GeneratedResult = {
          id: t.id,
          status: 'completed',
          claimId: claim.claim_id,
          score: String(claim.score?.reality_gap_score ?? ''),
          verdict: claim.score?.verdict ?? null,
        };
        upsert(result);
        await testInfo.attach(`result-${t.id}.json`, { body: JSON.stringify(result), contentType: 'application/json' });
      } else {
        upsert({ id: t.id, status: 'failed', claimId: claim?.claim_id, error: claim?.status ?? 'no claim found' });
      }
    });
  }
});
