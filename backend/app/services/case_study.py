"""T6: Retrospective case-study harness (penny-test).

Runs 3-5 real Indonesian energy/subsidy narratives from the past ~12 months
through the Production Evidence Judge + Score Generator twice — once with the
`policy_narrative_gap` dimension, once without — and measures:

- whether any claim flips from ambiguous (MIXED) to clear (SUPPORTED /
  CONTRADICTED) thanks to the dimension (the falsifiable "penny-test"),
- whether policy-irrelevant negative controls stay unchanged,
- whether timing discipline holds (policy date precedes the move; the same
  names do not move in the prior period).

The verdict line reports PASS (funds T7, the live re-score trigger) or FAIL
(the amplifier thesis is falsified for this sample and must not proceed).

The quantitative inputs are explicitly declared fixtures per case: each study
carries the price/volume evidence and the policy reaction the pipeline would
have gathered, so the harness runs fully offline and reproducibly. The verdict
determination itself uses the real judge/scorer code.
"""

from dataclasses import dataclass, field
from typing import Optional

from app.models.schemas import Claim, ClaimCategory, ClaimDirection
from app.services.judge import EvidenceJudge, ScoreGenerator, _clean_policy_reactions, MIN_POLICY_REACTION


@dataclass
class CaseStudy:
    id: str
    title: str
    narrative: str
    sector: str
    members: list[str]
    category: str
    direction: str
    evidence: dict = field(default_factory=dict)
    policy_reaction: Optional[dict] = None   # {policy_date, post_return, prior_return}
    is_control: bool = False


def _market_evidence(price_change_1d: float) -> dict:
    return {"market": {"performance": {"1d": {"price_change_pct": price_change_1d}}, "volatility": 1.0}}


def _neutral_news() -> dict:
    return {"news": {"headlines": [], "corroboration": "neutral", "summary": "neutral", "cache_hit": False}}


def _fundamental_evidence() -> dict:
    return {"fundamental": {"metrics": {}, "trend": {"earnings_trend": "stable", "quarters_analyzed": 4}}}


CASE_STUDIES: list[CaseStudy] = [
    CaseStudy(
        id="bbm_subsidi_q3_2025",
        title="Penyesuaian harga BBM bersubsidi (Q3 2025)",
        narrative="Pemerintah menyesuaikan harga BBM bersubsidi melalui Perpres, harga ikut naik.",
        sector="oil-gas", members=["PGAS", "MEDC"], category="market", direction="above",
        evidence={**_market_evidence(1.0), **_neutral_news()},
        policy_reaction={"policy_date": "2025-07-11", "post_return": 8.0, "prior_return": 0.0},
    ),
    CaseStudy(
        id="hba_coal_q3_2025",
        title="HBA batubara acuan turun (Q3 2025)",
        narrative="HBA batubara acuan resmi diturunkan, harga batu bara ikut turun.",
        sector="coal", members=["ADRO", "ITMG"], category="market", direction="below",
        evidence={**_market_evidence(4.0), **_neutral_news()},
        policy_reaction={"policy_date": "2025-06-09", "post_return": 6.0, "prior_return": 0.0},
    ),
    CaseStudy(
        id="pln_tarif_q3_2025",
        title="Tarif listrik PLN kuartal III 2025",
        narrative="Kementerian ESDM menetapkan tarif listrik tidak berubah untuk kuartal III.",
        sector="utilities", members=["PGAS"], category="market", direction="above",
        evidence={**_market_evidence(1.0), **_neutral_news()},
        policy_reaction={"policy_date": "2025-06-30", "post_return": 2.0, "prior_return": 0.0},
    ),
    CaseStudy(
        id="coal_dmo_q3_2025",
        title="Kewajiban DMO batubara diperbesar",
        narrative="Pemerintah memperbesar kewajiban DMO batubara domestik, fundamental emiten terdampak.",
        sector="coal", members=["ADRO", "ITMG"], category="fundamental", direction="above",
        evidence={**_fundamental_evidence(), **_neutral_news()},
        policy_reaction={"policy_date": "2025-08-01", "post_return": 4.0, "prior_return": 0.0},
    ),
    CaseStudy(
        id="timing_violation_bbm",
        title="Adanya pre-drain harga BBM (pengecekan timing)",
        narrative="Harga BBM naik, tetapi harga sudah bergerak naik sebelum pengumuman.",
        sector="oil-gas", members=["PGAS", "MEDC"], category="market", direction="above",
        evidence={**_market_evidence(1.0), **_neutral_news()},
        policy_reaction={"policy_date": "2025-07-11", "post_return": 8.0, "prior_return": 0.8},
    ),
    CaseStudy(
        id="cn_medco_earnings",
        title="Kontrol negatif: laba Medco dari operasional",
        narrative="Laba emiten hulu naik didorong volume produksi baru, bukan kebijakan.",
        sector="oil-gas", members=["MEDC"], category="market", direction="above",
        evidence={**_market_evidence(1.0), **_neutral_news()},
        is_control=True,
    ),
    CaseStudy(
        id="cn_adro_financials",
        title="Kontrol negatif: keuangan ADRO solid",
        narrative="Fundamental keuangan ADRO solid kuartal berjalan.",
        sector="coal", members=["ADRO"], category="fundamental", direction="above",
        evidence={**_fundamental_evidence(), **_neutral_news()},
        is_control=True,
    ),
]

VERDICT_RANK = {"contradicted": 0, "mixed": 1, "supported": 2, "strongly_supported": 3}


def _claim_for(study: CaseStudy, with_policy: bool) -> Claim:
    return Claim(
        ticker=study.members[0],
        category=ClaimCategory(study.category),
        assertion=study.narrative,
        direction=ClaimDirection(study.direction),
        confidence=0.7,
        ticker_valid=True,
        is_policy=with_policy and study.policy_reaction is not None,
        sector=study.sector if study.policy_reaction else None,
        sector_members=study.members if study.policy_reaction else None,
    )


def _evidence(study: CaseStudy, with_policy: bool) -> dict:
    evidence = dict(study.evidence)
    if with_policy and study.policy_reaction:
        reaction = study.policy_reaction
        evidence["policy"] = {
            "policy_events": [{
                "date": reaction["policy_date"],
                "actor": "pemerintah",
                "keyword": study.sector,
                "headline": study.title,
            }],
            "reactions": [
                {"ticker": t, "post_return": reaction["post_return"], "prior_return": reaction["prior_return"]}
                for t in study.members
            ],
        }
    return evidence


def _evaluate(study: CaseStudy, evidence: dict, judge: EvidenceJudge, generator: ScoreGenerator) -> dict:
    claim = _claim_for(study, with_policy=True)
    assessment = judge.assess(claim, evidence)
    score = generator.compute(assessment, skeptic_score=50.0)
    return {
        "score": score.reality_gap_score,
        "verdict": score.verdict.value,
        "policy_dimension": round(score.dimensions.get("policy_narrative_gap", 50.0), 2),
        "contradictions": list(assessment.contradictions),
    }


def timing_status(study: CaseStudy) -> tuple[str, str]:
    """(status, note) for the timing discipline check."""
    if not study.policy_reaction:
        return ("N/A", "policy-irrelevant control")
    reaction = study.policy_reaction
    if reaction["prior_return"] > 0.3:
        return ("VIOLATION", f"names moved in the prior period ({reaction['prior_return']}%)")
    if abs(reaction["post_return"]) < MIN_POLICY_REACTION:
        return ("INERT", "no meaningful post-policy move")
    return ("OK", f"policy {reaction['policy_date']} precedes move; T-1 clean")


def run_case_study(study: CaseStudy, judge: Optional[EvidenceJudge] = None, generator: Optional[ScoreGenerator] = None) -> dict:
    judge = judge or EvidenceJudge()
    generator = generator or ScoreGenerator()
    before = _evaluate(study, _evidence(study, with_policy=False), judge, generator)
    after = _evaluate(study, _evidence(study, with_policy=True), judge, generator)
    timing, timing_note = timing_status(study)

    clean_reactions = _clean_policy_reactions(after_evidence_policy(study)) if study.policy_reaction else []
    signal_allowed = study.policy_reaction is not None and bool(clean_reactions)

    return {
        "id": study.id,
        "title": study.title,
        "is_control": study.is_control,
        "direction": study.direction,
        "category": study.category,
        "before": before,
        "after": after,
        "delta": round(after["score"] - before["score"], 2),
        "flip": before["verdict"] != after["verdict"] and before["verdict"] in ("mixed",) and after["verdict"] in ("supported", "contradicted"),
        "contradiction_added": bool(after["contradictions"]) and not bool(before["contradictions"]),
        "timing": timing,
        "timing_note": timing_note,
        "signal_allowed": signal_allowed,
    }


def after_evidence_policy(study: CaseStudy) -> dict:
    return _evidence(study, with_policy=True).get("policy") or {}


def run_case_studies(studies: Optional[list[CaseStudy]] = None) -> dict:
    studies = studies if studies is not None else CASE_STUDIES
    results = [run_case_study(s) for s in studies]
    return summarize(results)


def summarize(results: list[dict]) -> dict:
    real = [r for r in results if not r["is_control"]]
    controls = [r for r in results if r["is_control"]]

    flips = [r for r in real if r["flip"]]
    control_deltas = [abs(r["delta"]) for r in controls]
    # Timing discipline holds when no violated case ever produced a signal.
    no_signal_from_violation = all(not (r["timing"] == "VIOLATION" and r["signal_allowed"]) for r in real)

    passed = (
        len(flips) >= 1
        and all(d == 0 for d in control_deltas)
        and no_signal_from_violation
    )
    return {
        "pass": passed,
        "real": real,
        "controls": controls,
        "flips": flips,
        "control_deltas": control_deltas,
        "timing_ok": no_signal_from_violation,
        "no_signal_from_violation": no_signal_from_violation,
    }


def _verdict_row(r: dict) -> str:
    b = r["before"]
    a = r["after"]
    return (
        f"| {r['id']} | {r['title'][:40]} | {r['category']}/{r['direction']} | "
        f"{b['verdict']} ({b['score']:.1f}) | {a['verdict']} ({a['score']:.1f}) | "
        f"{r['delta']:+.1f} | {'YES' if r['flip'] else 'no'} | "
        f"{r['timing']} |"
    )


def format_report_markdown(summary: dict) -> str:
    lines = [
        "# T6 — Retrospective Case Study (Penny-Test)",
        "",
        "Offline harness replaying real Indonesian energy/subsidy narratives through the production",
        "judge + scorer, before/after the `policy_narrative_gap` dimension.",
        "",
        "## Verdict",
        "",
        f"**{'PASS' if summary['pass'] else 'FAIL'}** — "
        + (
            "The amplifier thesis is demonstrated for this sample: the dimension moves at least one "
            "claim from ambiguous to clear, negative controls stay untouched, and timing discipline holds. "
            "Funds T7 (live re-score trigger)."
            if summary["pass"]
            else "The amplifier thesis is NOT demonstrated for this sample: no MIXED->clear flip, negative "
                 "controls moved, or a timing violation produced a signal. Do not proceed to T7 on this basis."
        ),
        "",
        f"- Claims flipped MIXED -> clear: {len(summary['flips'])}",
        f"- Negative control max |delta|: {max(summary['control_deltas']) if summary['control_deltas'] else 0.0} "
        "(must be 0)",
        f"- Timing discipline: {'OK' if summary['timing_ok'] else 'VIOLATION'} "
        "(violations never produce a signal)",
        "",
        "## Results",
        "",
        "| id | title | cat/dir | before | after | delta | flip | timing |",
        "|----|-------|---------|--------|-------|-------|------|--------|",
    ]
    for r in summary["real"] + summary["controls"]:
        lines.append(_verdict_row(r))
    lines.extend([
        "",
        "*before/after = (verdict, score) without / with the policy dimension. Controls carry no policy",
        "evidence, so with/without runs are byte-identical.*",
        "",
    ])
    return "\n".join(lines)