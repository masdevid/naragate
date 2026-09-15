export type NarrativeLang = 'id' | 'en';

function num(n: unknown): number | null {
  return typeof n === 'number' && Number.isFinite(n) ? n : null;
}

function fmt(n: number): string {
  const v = Math.round(n * 100) / 100;
  return String(v);
}

function sign(n: number): string {
  return n > 0 ? '+' : '';
}

const DIMENSION_LABELS: Record<string, Record<NarrativeLang, string>> = {
  valuation_gap: { id: 'valuasi', en: 'valuation' },
  peer_relative_gap: { id: 'perbandingan peer', en: 'peer comparison' },
  evidence_confidence: { id: 'keyakinan bukti', en: 'evidence confidence' },
  earnings_gap: { id: 'pertumbuhan laba', en: 'earnings' },
  policy_narrative_gap: { id: 'narasi kebijakan', en: 'policy narrative' },
  market_momentum_gap: { id: 'momentum pasar', en: 'market momentum' },
  insider_bias_gap: { id: 'aktivitas insider', en: 'insider activity' },
};

function dimensionLabel(key: string, lang: NarrativeLang): string {
  return DIMENSION_LABELS[key]?.[lang] ?? key.replace(/_/g, ' ');
}

function verdictLead(verdict: string, score: number | null, lang: NarrativeLang): string {
  const scorePart = score === null ? '?' : `${fmt(score)}/100`;
  switch (verdict) {
    case 'contradicted':
      return lang === 'en'
        ? `Measured evidence contradicts the claim (score ${scorePart}).`
        : `Bukti terukur bertentangan dengan klaim (skor ${scorePart}).`;
    case 'mixed':
      return lang === 'en'
        ? `Measured evidence is mixed and does not clearly support the claim (score ${scorePart}).`
        : `Bukti terukur bercampur dan tidak jelas mendukung klaim (skor ${scorePart}).`;
    case 'supported':
      return lang === 'en'
        ? `Measured evidence broadly supports the claim (score ${scorePart}).`
        : `Bukti terukur secara umum mendukung klaim (skor ${scorePart}).`;
    case 'strongly_supported':
      return lang === 'en'
        ? `Measured evidence strongly supports the claim (score ${scorePart}).`
        : `Bukti terukur sangat mendukung klaim (skor ${scorePart}).`;
    default:
      return lang === 'en'
        ? `Reality gap scored ${scorePart}.`
        : `Reality gap berskor ${scorePart}.`;
  }
}

function supportWord(relation: 'supports' | 'contradicts' | 'neutral', lang: NarrativeLang): string {
  if (relation === 'supports') return lang === 'en' ? 'supporting the claim' : 'mendukung klaim';
  if (relation === 'contradicts') return lang === 'en' ? 'contradicting the claim' : 'bertentangan dengan klaim';
  return lang === 'en' ? 'neutral to the claim' : 'netral terhadap klaim';
}

function relationFor(premium: number, direction: string): 'supports' | 'contradicts' | 'neutral' {
  if (direction !== 'above' && direction !== 'below') return 'neutral';
  if (direction === 'above') return premium > 0 ? 'supports' : 'contradicts';
  return premium < 0 ? 'supports' : 'contradicts';
}

function valuationPoint(ev: any, claim: any, lang: NarrativeLang): string | null {
  const valuation = ev?.valuation;
  if (!valuation) return null;
  const pe = num(valuation.metrics?.pe);
  const median = num(valuation.subsector_median?.pe);
  const premium = num(valuation.premium_pct?.pe);
  if (pe === null) return null;
  const direction = claim?.direction;
  if (premium !== null) {
    const relation = relationFor(premium, direction ?? '');
    return lang === 'en'
      ? `PE at ${fmt(pe)}x trades ${premium >= 0 ? 'a premium' : 'a discount'} of ${sign(premium)}${fmt(Math.abs(premium))}% vs the sector median${median !== null ? ` (${fmt(median)}x)` : ''}, ${supportWord(relation, lang)}.`
      : `PE ${fmt(pe)}x diperdagangkan ${premium >= 0 ? 'premium' : 'diskon'} ${sign(premium)}${fmt(Math.abs(premium))}% dibanding median sektor${median !== null ? ` (${fmt(median)}x)` : ''}, ${supportWord(relation, lang)}.`;
  }
  return lang === 'en'
    ? `PE is ${fmt(pe)}x${median !== null ? ` vs sector median ${fmt(median)}x` : ''}.`
    : `PE ${fmt(pe)}x${median !== null ? ` vs median sektor ${fmt(median)}x` : ''}.`;
}

function peerPoint(ev: any, lang: NarrativeLang): string | null {
  const valuation = ev?.valuation;
  if (!valuation) return null;
  const pb = num(valuation.metrics?.pb);
  const premium = num(valuation.premium_pct?.pb);
  if (pb === null || premium === null) return null;
  return lang === 'en'
    ? `PB of ${fmt(pb)}x is ${premium >= 0 ? 'above' : 'below'} peers by ${sign(premium)}${fmt(Math.abs(premium))}%.`
    : `PB ${fmt(pb)}x ${premium >= 0 ? 'di atas' : 'di bawah'} peer sebesar ${sign(premium)}${fmt(Math.abs(premium))}%.`;
}

function earningsPoint(ev: any, claim: any, lang: NarrativeLang): string | null {
  const trend = ev?.fundamental?.trend?.earnings_trend;
  if (!trend) return null;
  const direction = claim?.direction;
  const supports =
    (trend === 'improving' && direction !== 'below') || (trend === 'declining' && direction === 'below');
  const word = lang === 'en'
    ? (supports ? 'supporting the claim' : 'working against the claim')
    : (supports ? 'mendukung klaim' : 'menekan klaim');
  const trendLabel = lang === 'en'
    ? (trend === 'improving' ? 'improving' : trend === 'declining' ? 'declining' : 'stable')
    : (trend === 'improving' ? 'membaik' : trend === 'declining' ? 'menurun' : 'stabil');
  return lang === 'en'
    ? `Earnings trend is ${trendLabel}, ${word}.`
    : `Tren laba ${trendLabel}, ${word}.`;
}

function marketPoint(ev: any, claim: any, lang: NarrativeLang): string | null {
  const change = num(ev?.market?.performance?.['1d']?.price_change_pct);
  if (change === null) return null;
  const direction = claim?.direction;
  const supports =
    (direction === 'above' && change > 0) || (direction === 'below' && change < 0);
  const word = lang === 'en'
    ? (supports ? 'matching the claim' : 'against the claim')
    : (supports ? 'sejalan dengan klaim' : 'melawan klaim');
  return lang === 'en'
    ? `Price moved ${sign(change)}${fmt(change)}% over the last day, ${word}.`
    : `Harga bergerak ${sign(change)}${fmt(change)}% sehari terakhir, ${word}.`;
}

function filingsPoint(ev: any, lang: NarrativeLang): string | null {
  const filings = ev?.filings;
  if (!filings) return null;
  const bias = filings.recent_bias;
  const count = Array.isArray(filings.filings) ? filings.filings.length : null;
  if (!bias || bias === 'balanced') return null;
  const countPart = count !== null ? ` (${count} filings)` : '';
  if (bias === 'net_buying') {
    return lang === 'en'
      ? `Insiders are net buyers${countPart}, a bullish signal.`
      : `Insider cenderung net buy${countPart}, sinyal bullish.`;
  }
  return lang === 'en'
    ? `Insiders are net sellers${countPart}, a bearish signal.`
    : `Insider cenderung net sell${countPart}, sinyal bearish.`;
}

function corporateActionsPoint(ev: any, lang: NarrativeLang): string | null {
  const ca = ev?.corporate_actions;
  if (!ca) return null;
  const events = Array.isArray(ca.relevant_events) ? ca.relevant_events : [];
  const raw = Array.isArray(ca.actions) ? ca.actions : [];
  const count = events.length || raw.length;
  if (!count) return null;
  const label = events.length ? events.slice(0, 2).join(', ') : `${count} event(s)`;
  return lang === 'en'
    ? `Corporate actions detected: ${label}.`
    : `Aksi korporasi terdeteksi: ${label}.`;
}

function newsPoint(ev: any, lang: NarrativeLang): string | null {
  const headlines = ev?.news?.headlines;
  if (!Array.isArray(headlines) || !headlines.length) return null;
  return lang === 'en'
    ? `${headlines.length} recent headline${headlines.length > 1 ? 's' : ''} relevant to the narrative.`
    : `${headlines.length} berita terbaru relevan dengan narasi.`;
}

function skepticPoint(data: any, lang: NarrativeLang): string | null {
  const args = data?.skeptic?.counter_arguments;
  if (!Array.isArray(args) || !args.length) return null;
  const strongest = args.reduce((a, b) =>
    (num(b?.strength) ?? 0) > (num(a?.strength) ?? 0) ? b : a, args[0]);
  const text = lang === 'en' ? strongest?.point_en : strongest?.point;
  if (!text) return null;
  return lang === 'en' ? `Skeptic review challenges the reading: "${text}".` : `Tinjauan skeptis menantang pembacaan: "${text}".`;
}

function contradictionPoints(data: any, lang: NarrativeLang): string[] {
  const i18n = data?.assessment?.contradictions_i18n;
  if (Array.isArray(i18n) && i18n.length) {
    return i18n
      .slice(0, 2)
      .map((c: any) => c?.[lang] || c?.en)
      .filter((c: unknown): c is string => typeof c === 'string' && c.length > 0)
      .map((c: string) => (lang === 'en' ? `Flag: ${c}.` : `Catatan: ${c}.`));
  }
  const list = Array.isArray(data?.assessment?.contradictions) ? data.assessment.contradictions : [];
  return list.slice(0, 2).map((c: string) =>
    lang === 'en' ? `Flag: ${c}.` : `Catatan: ${c}.`
  );
}

function weakestDimension(data: any, lang: NarrativeLang): string | null {
  const dimensions = data?.score?.dimensions;
  if (!dimensions || typeof dimensions !== 'object') return null;
  const entries = Object.entries(dimensions).filter(([, v]) => Number.isFinite(v as number));
  if (!entries.length) return null;
  const [key, value] = entries.reduce((a, b) => ((b[1] as number) < (a[1] as number) ? b : a));
  return lang === 'en'
    ? `Weakest axis ${dimensionLabel(key, lang)} (${fmt(value as number)}/100) — improving it would most lift the score.`
    : `Sumbu terlemah ${dimensionLabel(key, lang)} (${fmt(value as number)}/100) — memperbaikinya paling berpotensi menaikkan skor.`;
}

export function buildVerdictNarrative(data: any, lang: NarrativeLang): string[] {
  if (!data?.score) return [];
  const score = data.score;
  const points: string[] = [verdictLead(score.verdict, num(score.reality_gap_score), lang)];

  const claim = data.claim;
  const detail: (string | null)[] = [
    valuationPoint(data.evidence, claim, lang),
    peerPoint(data.evidence, lang),
    earningsPoint(data.evidence, claim, lang),
    marketPoint(data.evidence, claim, lang),
    filingsPoint(data.evidence, lang),
    corporateActionsPoint(data.evidence, lang),
    newsPoint(data.evidence, lang),
  ];
  for (const d of detail) {
    if (d && points.length < 7) points.push(d);
  }

  const skeptic = skepticPoint(data, lang);
  if (skeptic && points.length < 7) points.push(skeptic);
  for (const c of contradictionPoints(data, lang)) {
    if (points.length < 8) points.push(c);
  }
  const weakest = weakestDimension(data, lang);
  if (weakest && points.length < 8) points.push(weakest);

  return points;
}