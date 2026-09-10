"""Curated policy context for the T1 pre-check and downstream amplifier work.

`ENERGY_POLICY_EVENTS` is a manually anchored set of Indonesian energy /
subsidy policy announcements used to overlay market moves. Dates are in
ISO format (YYYY-MM-DD). Each event carries a subsector tag so it can later
be matched to sectors resolved by T2.

Before a live run, dates in this file must be verified against primary
sources; entries marked `verified: false` are curated placeholders for the
hackathon window and get swapped for confirmed dates at run time.
"""

from typing import TypedDict


class PolicyEvent(TypedDict):
    date: str
    title: str
    subsector: str
    description: str
    verified: bool


ENERGY_POLICY_EVENTS: list[PolicyEvent] = [
    {
        "date": "2025-10-01",
        "title": "Pertamina adjusts non-subsidized BBM prices (Oct 2025 window)",
        "subsector": "oil-gas",
        "description": "Pertamina announced October 2025 BBM prices effective 1 Oct 2025: Dexlite +Rp100 to Rp13,700 and Pertamina Dex +Rp150 to Rp14,000; subsidized Pertalite/Solar held at Rp10,000/Rp6,800. Verifiable: Pertamina release + Kepmen ESDM 245.K/MG.01/MEM.M/2022 (MediaPresisi 2025-10-01).",
        "verified": True,
    },
    {
        "date": "2025-12-01",
        "title": "HBA coal benchmark reset (Dec 2025, period I)",
        "subsector": "coal",
        "description": "HBA high-calorie (6,322 kcal/kg GAR) reset to US$98.26/ton from US$102.03 (period I December), via Kepmen ESDM 388.K/MB.01/MEM.B/2025 signed 28 Nov 2025, effective 1 Dec 2025 (Bisnis/DDTC 2025-12-02).",
        "verified": True,
    },
    {
        "date": "2026-01-22",
        "title": "APBN 2026 energy-subsidy detail published (BBM subsidy cut, electricity up)",
        "subsector": "oil-gas",
        "description": "Perpres 118/2025 (Rincian APBN 2026, signed 28 Nov 2025) energy-subsidy detail widely reported: BBM (JBT) subsidy cut 5.7% to Rp25.14T, LPG 3-kg down 7.7% to Rp80.26T, electricity subsidy up 16.6% to Rp104.64T; total energy subsidy Rp210.06T (CNBC Indonesia 2026-01-22).",
        "verified": True,
    },
    {
        "date": "2026-04-01",
        "title": "Quarterly electricity tariff adjustment window (Apr–Jun 2026)",
        "subsector": "utilities",
        "description": "ESDM set PLN tariffs for Q2 2026 (effective 1 Apr 2026) unchanged for all 13 non-subsidi + 25 subsidized groups despite formula headroom; parameters kurs Rp16,743/USD, ICP US$62.78, HBA US$70 (Kompas 2026-03-31, esdm.go.id).",
        "verified": True,
    },
    {
        "date": "2026-06-22",
        "title": "DMO policy note: ESDM keeps US$70 domestic coal cap, forms supply task force",
        "subsector": "coal",
        "description": "After a PLN coal-supply shortfall (~20 Mt, demand 154 Mt), Bahlil affirmed the DMO price for the power sector stays US$70/ton (unchanged since 2018), keeps the ≥30% domestic-obligation share from the 2026 DMO Kepmen, and formed a coal-procurement task force (CNBC Indonesia & Liputan6, 22–23 Jun 2026).",
        "verified": True,
    },
]


class CandidateName(TypedDict):
    ticker: str
    name: str
    subsector: str
    prior_price_regime: str


CANDIDATE_ENERGY_NAMES: list[CandidateName] = [
    {
        "ticker": "ADRO",
        "name": "Adaro Energy",
        "subsector": "coal",
        "prior_price_regime": "market_priced",
    },
    {
        "ticker": "ITMG",
        "name": "Indo Tambangraya Megah",
        "subsector": "coal",
        "prior_price_regime": "market_priced",
    },
    {
        "ticker": "MEDC",
        "name": "Medco Energi Internasional",
        "subsector": "oil-gas",
        "prior_price_regime": "market_priced",
    },
    {
        "ticker": "PGAS",
        "name": "Perusahaan Gas Negara",
        "subsector": "oil-gas",
        "prior_price_regime": "administered",
    },
    {
        "ticker": "PTBA",
        "name": "Bukit Asam",
        "subsector": "coal",
        "prior_price_regime": "administered",
    },
]