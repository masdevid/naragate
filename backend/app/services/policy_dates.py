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
        "title": "Pertalite & Solar quote adjustment announced",
        "subsector": "oil-gas",
        "description": "Adjustment of subsidized fuel (BBM) reference prices for Pertalite/Solar window.",
        "verified": False,
    },
    {
        "date": "2025-12-05",
        "title": "HBA coal benchmark reset",
        "subsector": "coal",
        "description": "Monthly Indonesia Coal Price Reference (HBA) reset affecting producers.",
        "verified": False,
    },
    {
        "date": "2026-02-03",
        "title": "Subsidy budget allocation signal",
        "subsector": "oil-gas",
        "description": "Cabinet signal on energy subsidy budget for the coming fiscal year.",
        "verified": False,
    },
    {
        "date": "2026-04-15",
        "title": "Electricity tariff adjustment window",
        "subsector": "utilities",
        "description": "Quarterly electricity adjustment (tariff adjustment) announced.",
        "verified": False,
    },
    {
        "date": "2026-06-20",
        "title": "Domestic market obligation (DMO) policy note",
        "subsector": "coal",
        "description": "DMO enforcement / export-license linkage note for coal producers.",
        "verified": False,
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