import { test, expect } from '@playwright/test';
import { TemplateFlow, TemplateCase } from './claim-templates';
import { sseChunk, pipelineEvent, clarificationStream } from '../api-mocks';

/**
 * Drives every curated dashboard claim template through a full (mocked)
 * analysis and asserts the results page renders the correct UI for the claim
 * data that template produces.
 *
 * The evaluate SSE is entirely mocked (no LLM / Sectors API credits) and the
 * claim read-back is mocked, so each run is deterministic and costs 0 credits.
 */

const VALUATION_EVIDENCE = {
  valuation: {
    claim_ticker: 'BBCA',
    category: 'valuation',
    metrics: { pe: 25, pb: 4.1, ps: 3.2, forward_pe: 20 },
    subsector_median: { pe: 18, pb: 3, ps: 2.9 },
    premium_pct: { pe: 38.89, pb: 36.67, ps: 10.34 },
    health: { roe: 18.2, net_profit_margin: 28.5 },
    evidence_freshness: '2026-09-07',
    cache_hit: true,
  },
};

const FUNDAMENTAL_EVIDENCE = {
  fundamental: {
    claim_ticker: 'TLKM',
    category: 'fundamental',
    metrics: { revenue: 148_530_000_000, earnings: 2_100_000_000, eps: 21, net_profit_margin: 1.4, roe: 12.4, roa: 6.1, debt_to_equity: 0.9 },
    trend: { revenue_trend: 'improving', earnings_trend: 'declining', quarters_analyzed: 4 },
    evidence_freshness: '2026-09-07',
    cache_hit: true,
  },
};

const MARKET_EVIDENCE = {
  market: {
    claim_ticker: 'UNVR',
    category: 'market',
    performance: {
      '1d': { price_change_pct: -1.5, volume: 12_500_000 },
      '7d': { price_change_pct: -15, volume: 13_000_000 },
      '30d': { price_change_pct: -20, volume: 12_000_000 },
    },
    volatility: 22.4,
    evidence_freshness: '2026-09-07',
    cache_hit: false,
  },
};

const TEMPLATES: TemplateCase[] = [
  {
    id: 'valuation',
    claimId: 'tmpl-valuation',
    tile: 'PE BBCA mahal',
    narrative: 'PE BBCA mahal di 25x, jauh di atas rata-rata sektor 18x.',
    claim: {
      ticker: 'BBCA', category: 'valuation', assertion: 'Harga saham di atas nilai wajar',
      assertion_en: 'The stock is trading above fair value', direction: 'above',
      confidence: 0.9, ticker_valid: true,
    },
    evidence: VALUATION_EVIDENCE,
    skeptic: {
      claim_ticker: 'BBCA',
      counter_arguments: [
        { point: 'Premi tinggi bisa jadi karena kualitas pendapatan lebih baik daripada rekan sektor.', point_en: 'A high premium may reflect superior earnings quality versus peers.', evidence_ref: 'valuation', strength: 45 },
      ],
      ambiguity_points: ['Ambiguity pada definisi nilai wajar'],
      missing_evidence: ['Perbandingan forward PE antar bank'],
      skepticism_score: 45,
    },
    score: {
      claim_ticker: 'BBCA', claim_category: 'valuation', reality_gap_score: 72, verdict: 'supported',
      dimensions: { valuation_gap: 30, evidence_confidence: 80 },
      explanation: 'Bukti valuasi mendukung klaim.', explanation_en: 'Valuation evidence supports the claim.',
      confidence: 0.8, direction: 'above',
    },
    expectedCardTitles: ['Bukti Valuasi'],
    expectedMetrics: [
      { card: 'Bukti Valuasi', key: 'Rasio PE', value: '25,00' },
      { card: 'Bukti Valuasi', key: 'Rasio PB', value: '4,10' },
      { card: 'Bukti Valuasi', key: 'Premi PE', value: '38,9%' },
    ],
  },
  {
    id: 'fundamental',
    claimId: 'tmpl-fundamental',
    tile: 'TLKM',
    narrative: 'Pendapatan TLKM terus tumbuh tapi laba bersihnya menyusut setiap kuartal.',
    claim: {
      ticker: 'TLKM', category: 'fundamental', assertion: 'Laba bersih terus menyusut setiap kuartal',
      assertion_en: 'Net profit keeps shrinking every quarter', direction: 'below',
      confidence: 0.85, ticker_valid: true,
    },
    evidence: FUNDAMENTAL_EVIDENCE,
    skeptic: {
      claim_ticker: 'TLKM',
      counter_arguments: [{ point: 'Penyusutan laba bisa bersifat musiman.', evidence_ref: 'fundamental', strength: 55 }],
      ambiguity_points: [],
      missing_evidence: ['Data aliran kas per segmen'],
      skepticism_score: 50,
    },
    score: {
      claim_ticker: 'TLKM', claim_category: 'fundamental', reality_gap_score: 48, verdict: 'mixed',
      dimensions: { earnings_gap: 70, evidence_confidence: 55 },
      explanation: 'Bukti fundamental bercampur: pendapatan tumbuh tapi laba menyusut.',
      confidence: 0.7, direction: 'below',
    },
    expectedCardTitles: ['Bukti Fundamental'],
    expectedMetrics: [
      { card: 'Bukti Fundamental', key: 'Pendapatan', value: 'Rp 148,5 M' },
      { card: 'Bukti Fundamental', key: 'Tren Pendapatan', value: 'Membaik' },
      { card: 'Bukti Fundamental', key: 'Tren Laba', value: 'Menurun' },
      { card: 'Bukti Fundamental', key: 'ROE', value: '12,40' },
    ],
  },
  {
    id: 'market',
    claimId: 'tmpl-market',
    tile: 'UNVR',
    narrative: 'Saham UNVR turun 15% dalam seminggu, investor panik.',
    claim: {
      ticker: 'UNVR', category: 'market', assertion: 'Saham turun 15% dalam seminggu',
      assertion_en: 'Stock dropped 15% in a week', direction: 'below',
      confidence: 0.9, ticker_valid: true,
    },
    evidence: MARKET_EVIDENCE,
    skeptic: {
      claim_ticker: 'UNVR',
      counter_arguments: [{ point: 'Penurunan 7 hari bisa hanya koreksi teknis.', evidence_ref: 'market', strength: 40 }],
      ambiguity_points: [],
      missing_evidence: [],
      skepticism_score: 40,
    },
    score: {
      claim_ticker: 'UNVR', claim_category: 'market', reality_gap_score: 78, verdict: 'supported',
      dimensions: { market_momentum_gap: 18, evidence_confidence: 85 },
      explanation: 'Performa pasar mendukung klaim penurunan.',
      confidence: 0.85, direction: 'below',
    },
    expectedCardTitles: ['Bukti Pasar'],
    expectedMetrics: [
      { card: 'Bukti Pasar', key: 'Perubahan 1H', value: '-1,50%' },
      { card: 'Bukti Pasar', key: 'Perubahan 7H', value: '-15,00%' },
      { card: 'Bukti Pasar', key: 'Perubahan 30H', value: '-20,00%' },
    ],
  },
  {
    id: 'news',
    claimId: 'tmpl-news',
    tile: 'BMRI',
    narrative: 'BMRI disebut bank terbaik di Indonesia saat ini setelah berita laba rekor.',
    claim: {
      ticker: 'BMRI', category: 'fundamental', assertion: 'BMRI bank terbaik setelah laba rekor',
      assertion_en: 'BMRI is the best bank after record profit', direction: 'above',
      confidence: 0.88, ticker_valid: true,
    },
    evidence: {
      fundamental: {
        claim_ticker: 'BMRI', category: 'fundamental',
        metrics: { revenue: 140_000_000_000, earnings: 42_000_000_000, net_profit_margin: 30, roe: 19.8, debt_to_equity: 1.1 },
        trend: { revenue_trend: 'improving', earnings_trend: 'improving', quarters_analyzed: 4 },
        evidence_freshness: '2026-09-07', cache_hit: true,
      },
      news: {
        claim_ticker: 'BMRI', category: 'fundamental',
        headlines: [{ title: 'BMRI Cetak Laba Rekor pada Kuartal Kedua', url: 'https://market.example/bmri-rekor' }],
        corroboration: 'supports',
        summary: 'Berita terkini mendukung narasi laba rekor BMRI.',
        evidence_freshness: '2026-09-07', cache_hit: true,
      },
    },
    skeptic: {
      claim_ticker: 'BMRI',
      counter_arguments: [{ point: 'Predikat \u201cbank terbaik\u201d bersifat subjektif.', evidence_ref: 'news', strength: 35 }],
      ambiguity_points: ['Definisi \u2018terbaik\u2019 tidak terukur'],
      missing_evidence: [],
      skepticism_score: 35,
    },
    score: {
      claim_ticker: 'BMRI', claim_category: 'fundamental', reality_gap_score: 85, verdict: 'strongly_supported',
      dimensions: { earnings_gap: 15, evidence_confidence: 90 },
      explanation: 'Berita dan fundamental mendukung klaim.',
      confidence: 0.9, direction: 'above',
    },
    expectedCardTitles: ['Bukti Fundamental', 'Korelasi Berita'],
    expectedMetrics: [
      { card: 'Bukti Fundamental', key: 'Pendapatan', value: 'Rp 140,0 M' },
      { card: 'Bukti Fundamental', key: 'Tren Laba', value: 'Membaik' },
    ],
  },
  {
    id: 'policy-bbm',
    claimId: 'tmpl-policy-bbm',
    tile: 'Subsidi BBM',
    narrative: 'Subsidi BBM dipangkas — harga BBM bersubsidi naik kuartal ini.',
    claim: {
      ticker: 'PGAS', category: 'market', assertion: 'Harga BBM bersubsidi naik berdampak pada emiten energi',
      direction: 'above', confidence: 0.8, ticker_valid: true,
      is_policy: true, sector: 'oil-gas', sector_members: ['PGAS', 'MEDC', 'PSSI'],
    },
    evidence: {},
    skeptic: {
      claim_ticker: 'PGAS',
      counter_arguments: [{ point: 'Dampak kebijakan bisa tertunda beberapa kuartal.', evidence_ref: 'policy', strength: 48 }],
      ambiguity_points: [],
      missing_evidence: [],
      skepticism_score: 48,
    },
    score: {
      claim_ticker: 'PGAS', claim_category: 'market', reality_gap_score: 65, verdict: 'supported',
      dimensions: { policy_signal: 20, evidence_confidence: 70 },
      explanation: 'Amplifier kebijakan mendukung klaim.',
      confidence: 0.75, direction: 'neutral',
    },
    precheck: {
      verdict: 'PASS', rationale: 'Amplifier energi menopang harga kandidat.',
      window_days: 3,
      policy_events: [{ date: '2026-08-01', actor: 'Pemerintah', keyword: 'BBM', title: 'Subsidi BBM dipangkas' }],
      results: [
        {
          ticker: 'PGAS', name: 'Perusahaan Gas Negara', subsector: 'oil-gas', prior_price_regime: 'uptrend',
          daily_vol: 2.5, policy_ratio: 1.4, on_window_returns: 3, off_window_returns: 1,
          price_regime: 'rekonsolidasi', policy_signal: 'terikat', classification: 'market_priced_signal',
          cache_hit: true, data_days: 60,
        },
      ],
      beacon_list: ['PGAS'],
    },
    expectedCardTitles: [],
    expectsPolicy: true,
  },
  {
    id: 'policy-hba',
    claimId: 'tmpl-policy-hba',
    tile: 'ADRO',
    narrative: 'HBA batu bara ditetapkan naik untuk Q3 — untung ADRO ikut naik.',
    claim: {
      ticker: 'ADRO', category: 'market', assertion: 'HBA naik menguntungkan emiten batu bara',
      direction: 'above', confidence: 0.82, ticker_valid: true,
      is_policy: true, sector: 'coal', sector_members: ['ADRO', 'PTBA', 'ITMG'],
    },
    evidence: {},
    skeptic: {
      claim_ticker: 'ADRO',
      counter_arguments: [{ point: 'HBA acuan belum tentu sejalan dengan harga kontrak ADRO.', evidence_ref: 'policy', strength: 52 }],
      ambiguity_points: [],
      missing_evidence: [],
      skepticism_score: 52,
    },
    score: {
      claim_ticker: 'ADRO', claim_category: 'market', reality_gap_score: 61, verdict: 'supported',
      dimensions: { policy_signal: 25, evidence_confidence: 68 },
      explanation: 'Amplifier kebijakan umumnya mendukung klaim.',
      confidence: 0.72, direction: 'neutral',
    },
    precheck: {
      verdict: 'CONDITIONAL', rationale: 'Sinyal pasar batu bara bercampur; pas-pasan terhadap ambang.',
      window_days: 3,
      policy_events: [{ date: '2026-09-01', actor: 'Pemerintah', keyword: 'HBA', title: 'HBA ditetapkan naik untuk Q3' }],
      results: [
        {
          ticker: 'ADRO', name: 'Adaro Energy', subsector: 'coal', prior_price_regime: 'sideways',
          daily_vol: 3.1, policy_ratio: 0.9, on_window_returns: 2, off_window_returns: 2,
          price_regime: 'konsolidasi', policy_signal: 'netral', classification: 'weak_signal',
          cache_hit: true, data_days: 55,
        },
      ],
      beacon_list: [],
    },
    expectedCardTitles: [],
    expectsPolicy: true,
  },
  {
    id: 'policy-nickel',
    claimId: 'tmpl-policy-nickel',
    tile: 'INCO',
    narrative: 'Larangan ekspor bijih nikel diperketat — INCO untung dari hilirisasi.',
    claim: {
      ticker: 'INCO', category: 'market', assertion: 'Hilirisasi nikel menguntungkan INCO',
      direction: 'above', confidence: 0.84, ticker_valid: true,
      is_policy: true, sector: 'nickel', sector_members: ['INCO', 'NCKL'],
    },
    evidence: {},
    skeptic: {
      claim_ticker: 'INCO',
      counter_arguments: [{ point: 'Larangan ekspor juga bisa menekan volume bijih INCO.', evidence_ref: 'policy', strength: 60 }],
      ambiguity_points: [],
      missing_evidence: [],
      skepticism_score: 60,
    },
    score: {
      claim_ticker: 'INCO', claim_category: 'market', reality_gap_score: 70, verdict: 'supported',
      dimensions: { policy_signal: 22, evidence_confidence: 74 },
      explanation: 'Amplifier kebijakan nikel mendukung klaim.',
      confidence: 0.78, direction: 'neutral',
    },
    precheck: {
      verdict: 'PASS', rationale: 'Sinyal pasar nikel konsisten dengan narasi hilirisasi.',
      window_days: 3,
      policy_events: [{ date: '2026-08-15', actor: 'Kementerian ESDM', keyword: 'nikel', title: 'Larangan ekspor bijih nikel diperketat' }],
      results: [
        {
          ticker: 'INCO', name: 'Vale Indonesia', subsector: 'nickel', prior_price_regime: 'uptrend',
          daily_vol: 2.8, policy_ratio: 1.6, on_window_returns: 4, off_window_returns: 0,
          price_regime: 'trend naik', policy_signal: 'terikat kuat', classification: 'market_priced_signal',
          cache_hit: true, data_days: 62,
        },
      ],
      beacon_list: ['INCO'],
    },
    expectedCardTitles: [],
    expectsPolicy: true,
  },
  {
    id: 'no-ticker',
    claimId: 'tmpl-clarify',
    tile: 'perbankan sedang mahal',
    narrative: 'Saham perbankan sedang mahal.',
    claim: {
      ticker: 'UNKNOWN', category: 'valuation', assertion: 'Saham perbankan mahal',
      direction: 'above', confidence: 0.5, ticker_valid: false,
      needs_clarification: true, missing: ['ticker'],
      reason: 'No valid 4-letter ticker identified in the narrative',
    },
    score: {},
    clarification: true,
    expectedCardTitles: [],
  },
  {
    id: 'contradiction',
    claimId: 'tmpl-contradiction',
    tile: 'BBRI',
    narrative: 'Laba BBRI naik tapi sahamnya terus turun 20% bulan ini.',
    claim: {
      ticker: 'BBRI', category: 'market', assertion: 'Laba naik tapi saham terus turun 20%',
      assertion_en: 'Profit grows but the stock keeps falling 20%', direction: 'below',
      confidence: 0.9, ticker_valid: true,
    },
    evidence: {
      market: {
        claim_ticker: 'BBRI', category: 'market',
        performance: {
          '1d': { price_change_pct: -1.2, volume: 8_000_000 },
          '7d': { price_change_pct: -20, volume: 9_000_000 },
          '30d': { price_change_pct: -25, volume: 7_000_000 },
        },
        volatility: 18.6, evidence_freshness: '2026-09-07', cache_hit: true,
      },
    },
    skeptic: {
      claim_ticker: 'BBRI',
      counter_arguments: [
        { point: 'Penurunan harga tidak selalu menandakan fundamental buruk — bisa profit taking.', evidence_ref: 'market', strength: 80 },
      ],
      ambiguity_points: ['Pembelian kembali saham dapat menopang harga'],
      missing_evidence: ['Data arus kas kuartalan'],
      skepticism_score: 75,
    },
    score: {
      claim_ticker: 'BBRI', claim_category: 'market', reality_gap_score: 24, verdict: 'contradicted',
      dimensions: { market_momentum_gap: 85, earnings_gap: 20, evidence_confidence: 50 },
      explanation: 'Saham jatuh meski laba naik — kontradiksi nyata.',
      confidence: 0.8, direction: 'below',
    },
    expectedCardTitles: ['Bukti Pasar'],
    expectedMetrics: [
      { card: 'Bukti Pasar', key: 'Perubahan 7H', value: '-20,00%' },
      { card: 'Bukti Pasar', key: 'Perubahan 30H', value: '-25,00%' },
    ],
  },
  {
    id: 'future-price',
    claimId: 'tmpl-future',
    tile: 'BBCA akan berlipat',
    narrative: 'Harga saham BBCA akan berlipat tahun ini.',
    claim: {
      ticker: 'BBCA', category: 'valuation', assertion: 'Harga saham akan berlipat tahun ini',
      assertion_en: 'The stock will double this year', direction: 'above',
      confidence: 0.6, ticker_valid: true,
    },
    evidence: {
      valuation: {
        claim_ticker: 'BBCA', category: 'valuation',
        metrics: { pe: 22, pb: 4.0, ps: 3.1 },
        subsector_median: { pe: 18, pb: 3, ps: 2.9 },
        premium_pct: { pe: 22.22, pb: 33.33, ps: 6.9 },
        evidence_freshness: '2026-09-07', cache_hit: true,
      },
      market: {
        claim_ticker: 'BBCA', category: 'market',
        performance: { '1d': { price_change_pct: 0.5, volume: 5_000_000 } },
        volatility: 12.1, evidence_freshness: '2026-09-07', cache_hit: true,
      },
    },
    skeptic: {
      claim_ticker: 'BBCA',
      counter_arguments: [{ point: 'Klaim harga berlipat dalam setahun bersifat ekstrem.', evidence_ref: 'valuation', strength: 68 }],
      ambiguity_points: ['Tidak ada dasar fundamental untuk penggandaan harga'],
      missing_evidence: [],
      skepticism_score: 68,
    },
    score: {
      claim_ticker: 'BBCA', claim_category: 'valuation', reality_gap_score: 55, verdict: 'mixed',
      dimensions: { valuation_gap: 55, market_momentum_gap: 40, evidence_confidence: 60 },
      explanation: 'Valuasi sehat, tapi klaim berlipat tidak didukung momentum.',
      confidence: 0.65, direction: 'above',
    },
    expectedCardTitles: ['Bukti Valuasi', 'Bukti Pasar'],
  },
  {
    id: 'below-cpo',
    claimId: 'tmpl-below-cpo',
    tile: 'AALI',
    narrative: 'Harga CPO turun — laba AALI tertekan.',
    claim: {
      ticker: 'AALI', category: 'fundamental', assertion: 'Laba AALI tertekan oleh turunnya CPO',
      assertion_en: 'AALI profits are under pressure from falling CPO', direction: 'below',
      confidence: 0.9, ticker_valid: true,
    },
    evidence: {
      fundamental: {
        claim_ticker: 'AALI', category: 'fundamental',
        metrics: { revenue: 18_900_000_000, earnings: 1_200_000_000, net_profit_margin: 6.3, roe: 8.4, debt_to_equity: 0.5 },
        trend: { revenue_trend: 'declining', earnings_trend: 'declining', quarters_analyzed: 4 },
        evidence_freshness: '2026-09-07', cache_hit: true,
      },
    },
    skeptic: {
      claim_ticker: 'AALI',
      counter_arguments: [{ point: 'Laba bisa tertolong oleh efisiensi biaya dan perkebunan inti.', evidence_ref: 'fundamental', strength: 44 }],
      ambiguity_points: [],
      missing_evidence: ['Harga CPO aktual kuartalan'],
      skepticism_score: 44,
    },
    score: {
      claim_ticker: 'AALI', claim_category: 'fundamental', reality_gap_score: 74, verdict: 'supported',
      dimensions: { earnings_gap: 25, evidence_confidence: 82 },
      explanation: 'Fundamental mendukung laba yang tertekan.',
      confidence: 0.83, direction: 'below',
    },
    expectedCardTitles: ['Bukti Fundamental'],
    expectedMetrics: [
      { card: 'Bukti Fundamental', key: 'Tren Pendapatan', value: 'Menurun' },
      { card: 'Bukti Fundamental', key: 'Tren Laba', value: 'Menurun' },
    ],
  },
  {
    id: 'below-auto',
    claimId: 'tmpl-below-auto',
    tile: 'ASII',
    narrative: 'Penjualan mobil melemah kuartal ini — pendapatan ASII akan merosot.',
    claim: {
      ticker: 'ASII', category: 'fundamental', assertion: 'Pendapatan ASII akan merosot',
      assertion_en: 'ASII revenue will slide', direction: 'below',
      confidence: 0.85, ticker_valid: true,
    },
    evidence: {
      fundamental: {
        claim_ticker: 'ASII', category: 'fundamental',
        metrics: { revenue: 98_400_000_000, earnings: 8_700_000_000, net_profit_margin: 8.8, roe: 14.2, debt_to_equity: 0.7 },
        trend: { revenue_trend: 'declining', earnings_trend: 'declining', quarters_analyzed: 4 },
        evidence_freshness: '2026-09-07', cache_hit: true,
      },
    },
    skeptic: {
      claim_ticker: 'ASII',
      counter_arguments: [{ point: 'Segmen alat berat dan jasa keuangan bisa mengimbangi penurunan mobil.', evidence_ref: 'fundamental', strength: 50 }],
      ambiguity_points: [],
      missing_evidence: [],
      skepticism_score: 50,
    },
    score: {
      claim_ticker: 'ASII', claim_category: 'fundamental', reality_gap_score: 69, verdict: 'supported',
      dimensions: { earnings_gap: 28, evidence_confidence: 78 },
      explanation: 'Pendapatan yang menurun mendukung klaim.',
      confidence: 0.8, direction: 'below',
    },
    expectedCardTitles: ['Bukti Fundamental'],
    expectedMetrics: [
      { card: 'Bukti Fundamental', key: 'Tren Pendapatan', value: 'Menurun' },
      { card: 'Bukti Fundamental', key: 'Tren Laba', value: 'Menurun' },
    ],
  },
];

function completedClaim(c: TemplateCase): Record<string, any> {
  return {
    claim_id: c.claimId,
    narrative: c.narrative,
    status: 'completed',
    created_at: '2026-09-08T07:23:02.866054',
    updated_at: '2026-09-08T07:23:10.795340',
    claim: c.claim,
    evidence: c.evidence ?? {},
    skeptic: c.skeptic ?? { claim_ticker: c.claim.ticker, counter_arguments: [], ambiguity_points: [], missing_evidence: [], skepticism_score: 50 },
    score: c.score,
    duration_ms: 1500,
  };
}

function claimStream(c: TemplateCase): string {
  const claim = { ...c.claim, claim_id: c.claimId };
  const events: string[] = [
    sseChunk('pipeline_started', pipelineEvent('pipeline_started', c.claimId, { narrative: c.narrative })),
    sseChunk('claim_parsing', pipelineEvent('claim_parsing', c.claimId, { stage: 'claim_parser' })),
    sseChunk('claim_parsed', pipelineEvent('claim_parsed', c.claimId, claim)),
  ];

  if (claim.is_policy) {
    events.push(sseChunk('policy_sector_resolved', pipelineEvent('policy_sector_resolved', c.claimId, {
      sector: claim.sector,
      members: claim.sector_members,
    })));
    events.push(sseChunk('sector_evidence_ready', pipelineEvent('sector_evidence_ready', c.claimId, {
      policy: { policy_events: c.precheck?.policy_events ?? [], reactions: [] },
    })));
  } else {
    events.push(sseChunk('evidence_fetching', pipelineEvent('evidence_fetching', c.claimId, {
      ticker: claim.ticker,
      category: claim.category,
    })));
    events.push(sseChunk('evidence_ready', pipelineEvent('evidence_ready', c.claimId, c.evidence ?? {})));
  }

  events.push(
    sseChunk('skeptic_analysis', pipelineEvent('skeptic_analysis', c.claimId, { stage: 'skeptic' })),
    sseChunk('skeptic_ready', pipelineEvent('skeptic_ready', c.claimId, c.skeptic ?? { claim_ticker: claim.ticker, counter_arguments: [], ambiguity_points: [], missing_evidence: [], skepticism_score: 50 })),
    sseChunk('judge_assessment', pipelineEvent('judge_assessment', c.claimId, { stage: 'judge' })),
    sseChunk('assessment_ready', pipelineEvent('assessment_ready', c.claimId, { assessment: 'aligned', confidence: 0.7 })),
    sseChunk('score_computing', pipelineEvent('score_computing', c.claimId, { stage: 'scorer' })),
    sseChunk('score_computed', pipelineEvent('score_computed', c.claimId, c.score)),
    sseChunk('pipeline_complete', pipelineEvent('pipeline_complete', c.claimId, {
      duration_ms: 1500,
      verdict: c.score.verdict,
      score: c.score.reality_gap_score,
    })),
  );
  return events.join('');
}

async function mockTemplateBackend(page: import('@playwright/test').Page, c: TemplateCase): Promise<void> {
  await page.route('**/api/v1/stream/evaluate', route => route.fulfill({
    status: 200,
    contentType: 'text/event-stream',
    body: c.clarification ? clarificationStream(c.claimId, c.narrative) : claimStream(c),
  }));
  if (c.precheck) {
    await page.route('**/api/v1/precheck/**', route => route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(c.precheck),
    }));
  }
  if (!c.clarification) {
    await page.route(`**/api/v1/claims/${c.claimId}`, route => route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(completedClaim(c)),
    }));
  }
}

async function expectPolicySection(page: import('@playwright/test').Page, c: TemplateCase): Promise<void> {
  const policy = page.locator('.policy');
  if (!c.precheck) {
    await expect(policy).toHaveCount(0);
    return;
  }
  await expect(policy).toBeVisible();
  await expect(policy.locator('.policy__verdict').first()).toHaveText(c.precheck.verdict);

  // Orphan section-help boxes must be hidden when a section has no data.
  await expect(page.locator('.evidence .metric')).toHaveCount(0);
  await expect(page.locator('.evidence .section-help')).toHaveCount(0);
  await expect(page.locator('.news .section-help')).toHaveCount(0);
  await expect(page.locator('.filings .section-help')).toHaveCount(0);

  const first = c.precheck.results?.[0];
  if (first) {
    const row = page.locator('.policy__table tbody tr').filter({ hasText: first.ticker });
    await expect(row).toHaveCount(1);
    await expect(row).toContainText(first.subsector);
    await expect(row).toContainText(first.policy_signal);
    await expect(row).toContainText(first.classification);
  }
  for (const ev of c.precheck.policy_events ?? []) {
    await expect(page.locator('.policy__event')).toContainText([ev.title]);
  }
  if (c.precheck.beacon_list?.length) {
    await expect(policy.locator('.policy__beacon-list')).toContainText(c.precheck.beacon_list.join(', '));
  }
}

test.describe('Dashboard claim templates', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem('naragate_setup_dismissed', '1'));
  });

  for (const c of TEMPLATES) {
    const seq = String(TEMPLATES.indexOf(c) + 1).padStart(3, '0');
    test(`@TMPL-E2E-${seq} ${c.id} renders the correct claim, verdict and evidence UI`,
      { tag: ['@e2e', '@templates'] },
      async ({ page }) => {
        await mockTemplateBackend(page, c);
        const flow = new TemplateFlow(page);

        await flow.goto();
        await flow.chooseTemplate(c);
        await flow.analyze();

        if (c.clarification) {
          // Ticker guardrail: halts on /claim, never reaches evidence or results.
          await expect(page.locator('.claim__error')).toContainText(/kode saham/i);
          await page.waitForTimeout(1_500);
          await expect(page).toHaveURL(/\/claim/);
          return;
        }

        await flow.waitForResults(c.claimId);
        await flow.expectNarrativeQuote(c);
        await flow.expectClaimMeta(c);
        await flow.expectScore(c);
        await flow.expectSections(c);
        await expectPolicySection(page, c);
        await flow.expectSkeptic(c);
      });
  }

  test('@TMPL-E2E-013 news template renders the news card with corroboration badge and headline link',
    { tag: ['@e2e', '@templates'] },
    async ({ page }) => {
      const c = TEMPLATES.find(t => t.id === 'news')!;
      await mockTemplateBackend(page, c);
      const flow = new TemplateFlow(page);

      await flow.goto();
      await flow.chooseTemplate(c);
      await flow.analyze();
      await flow.waitForResults(c.claimId);

      const newsCard = flow.evidenceCard('Korelasi Berita');
      await expect(newsCard).toBeVisible();
      await expect(newsCard.locator('.news__badge')).toHaveText('Berita Mendukung Klaim');
      await expect(newsCard.locator('.news__summary')).toContainText('laba rekor');
      const link = newsCard.locator('.news__link');
      await expect(link).toHaveText('BMRI Cetak Laba Rekor pada Kuartal Kedua');
      await expect(link).toHaveAttribute('href', 'https://market.example/bmri-rekor');
      await expect(newsCard.locator('.news__source')).toHaveText('market.example');
    });
});