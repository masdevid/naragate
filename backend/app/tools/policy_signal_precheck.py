"""T1 pre-check runner: prints a markdown report to stdout.

Usage (from backend/):
    SECTORS_API_KEY=<key> python -m app.tools.policy_signal_precheck

The analysis logic lives in app.services.policy_signal. This runner tries the
live Evidence Graph -> Sectors fetch. When every candidate fetch fails (no key,
network unavailable), it falls back to a clearly-labeled simulated 12-month
window so the report + verdict pipeline can be exercised offline.
"""

import asyncio

from app.services.policy_signal import format_report_markdown, run_precheck


def _simulated_report():
    import random as _random
    from datetime import date, timedelta

    from app.services.policy_dates import CANDIDATE_ENERGY_NAMES, ENERGY_POLICY_EVENTS
    from app.services.policy_signal import classify_signal_for_name, PrecheckReport, aggregate_verdict

    events = list(ENERGY_POLICY_EVENTS)
    policy_dates = [e["date"] for e in events]
    start = date.fromisoformat("2025-09-01")
    days = 260

    def make_series(vol: float, policy_move: float, seed: int) -> list[dict]:
        rng = _random.Random(seed)
        price = 1000.0
        cur = start
        out = []
        for _ in range(days):
            r = rng.gauss(0, vol)
            if cur.isoformat() in policy_dates:
                r += rng.choice([-1, 1]) * policy_move
            price = max(10.0, price * (1 + r))
            out.append({"date": cur.isoformat(), "close": round(price, 2), "volume": 1_000_000})
            cur += timedelta(days=1)
        return out

    regimes = {
        # ticker -> (daily_vol, policy_move) — market-priced names respond,
        # administered names do not move day-to-day.
        "ADRO": (0.010, 0.080),
        "ITMG": (0.012, 0.070),
        "MEDC": (0.014, 0.075),
        "PGAS": (0.0004, 0.0),
        "PTBA": (0.0004, 0.0),
    }
    results = []
    for i, c in enumerate(CANDIDATE_ENERGY_NAMES):
        vol, move = regimes[c["ticker"]]
        tx = make_series(vol, move, seed=i)
        results.append(classify_signal_for_name(
            c["ticker"], tx, policy_dates,
            name=c["name"], subsector=c["subsector"],
            prior_price_regime=c["prior_price_regime"], cache_hit=False,
        ))
    verdict, rationale = aggregate_verdict(results)
    return PrecheckReport(verdict=verdict, rationale=rationale, window_days=2, policy_events=events, results=results)


async def main() -> int:
    report = await run_precheck()
    if report.verdict == "FAIL" and all(r.classification == "fetch_failed" for r in report.results):
        print("No live Sectors data available (key missing or unavailable). Using simulated window.\n")
        report = _simulated_report()
        data_note = "Data source: SIMULATED window (no live Sectors key). Replace with `SECTORS_API_KEY` for a live run."
    else:
        data_note = "Data source: live Evidence Graph -> Sectors daily transactions (cache-first)."
    print(format_report_markdown(report, data_note))
    return 0 if report.verdict in ("PASS", "CONDITIONAL") else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))