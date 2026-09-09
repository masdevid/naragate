"""T1 pre-check: does energy-policy narrative move stock prices?

The cheapest falsifiable test for the amplifier thesis. For each candidate
energy name we pull 12 months of daily transactions (Evidence Graph first, then
Sectors), compute day-to-day returns in percent, and ask two questions:

1. **Price regime** — does the name trade with real day-to-day volatility?
   (>= MIN_DAILY_VOL) -> market_priced; otherwise the price looks
   administered/quoted, i.e. mostly set by a government reference price.
2. **Policy signal** — do |returns| cluster around policy-announcement days?
   On-window mean |return| vs off-window mean |return| >= MIN_POLICY_RATIO
   means moves concentrate on policy dates (narrative -> price channel).

A name is a `market_priced_signal` when both hold. Aggregated verdict:

* PASS        -> >= 2 market_priced_signal names with ratio >= STRONG_RATIO
* CONDITIONAL -> >= 1 market_priced_signal name (narrow the beacon list)
* FAIL        -> no market-priced signal (administered pricing dominates)

All downstream sector work (T2+) restricts itself to the narrowed beacon list.
Everything here is pure & deterministic except the fetch, which is cache-first.
"""

import statistics
from dataclasses import dataclass, field

from app.core.evidence_cache import cache
from app.core.sectors_client import sectors_client
from app.core.usage_tracker import record_sectors_cache_hit
from app.config.settings import settings
from app.services.policy_dates import CANDIDATE_ENERGY_NAMES, ENERGY_POLICY_EVENTS, PolicyEvent

MIN_DAILY_VOL = 0.3          # % — daily vol floor for a "real" market
MIN_POLICY_RATIO = 1.5       # on-window / off-window mean |return| for signal
STRONG_RATIO = 2.0           # ratio for a strong beacon name
POLICY_WINDOW_DAYS = 2       # trading days on each side of an announcement


@dataclass
class NameResult:
    ticker: str
    name: str
    subsector: str
    prior_price_regime: str
    daily_vol: float
    policy_ratio: float
    on_window_returns: int
    off_window_returns: int
    price_regime: str
    policy_signal: str
    classification: str
    cache_hit: bool
    error: str | None = None
    data_days: int = 0

    @property
    def is_beacon(self) -> bool:
        return self.classification == "market_priced_signal"


@dataclass
class PrecheckReport:
    verdict: str
    rationale: str
    window_days: int
    policy_events: list[PolicyEvent]
    results: list[NameResult] = field(default_factory=list)

    @property
    def beacon_list(self) -> list[str]:
        return [r.ticker for r in self.results if r.is_beacon]


def daily_close_series(transactions: list[dict]) -> list[tuple[str, float]]:
    """Ascending (date, close) series; rows without a close are dropped."""
    rows = []
    for d in transactions or []:
        close = d.get("close")
        if close is None and d.get("price") is not None:
            close = d["price"]
        if close:
            rows.append((str(d.get("date", "")), float(close)))
    rows.sort(key=lambda r: r[0])
    return rows


def returns_in_percent(series: list[tuple[str, float]]) -> list[tuple[str, float]]:
    out = []
    for i in range(1, len(series)):
        prev = series[i - 1][1]
        if prev:
            out.append((series[i][0], (series[i][1] - prev) / prev * 100.0))
    return out


def policy_window_indices(trading_days: list[str], policy_dates: list[str], window_days: int) -> set[int]:
    """Trading-day indices within `window_days` trading days of any policy date."""
    policy_set = set(policy_dates)
    indices: set[int] = set()
    for i, day in enumerate(trading_days):
        if day in policy_set:
            for j in range(max(0, i - window_days), min(len(trading_days), i + window_days + 1)):
                indices.add(j)
    return indices


def classify_signal_for_name(
    ticker: str,
    transactions: list[dict],
    policy_dates: list[str],
    window_days: int = POLICY_WINDOW_DAYS,
    name: str = "",
    subsector: str = "",
    prior_price_regime: str = "",
    cache_hit: bool = False,
) -> NameResult:
    series = daily_close_series(transactions)
    returns = returns_in_percent(series)
    trading_days = [dt for dt, _ in series]
    window = policy_window_indices(trading_days, policy_dates, window_days)

    on = [r for i, (dt, r) in enumerate(returns, start=1) if i in window]
    off = [r for i, (dt, r) in enumerate(returns, start=1) if i not in window]

    daily_vol = statistics.pstdev([r for _, r in returns]) if len(returns) >= 2 else 0.0
    mean_on = (sum(abs(r) for r in on) / len(on)) if on else 0.0
    mean_off = (sum(abs(r) for r in off) / len(off)) if off else 0.0
    if mean_off > 0 and mean_on > 0:
        policy_ratio = mean_on / mean_off
    elif mean_on > 0:
        policy_ratio = 99.0
    else:
        policy_ratio = 0.0

    price_regime = "market_priced" if daily_vol >= MIN_DAILY_VOL else "administered"
    policy_signal = "responsive" if policy_ratio >= MIN_POLICY_RATIO else "inert"
    if price_regime == "administered":
        classification = "administered"
    elif policy_signal == "responsive":
        classification = "market_priced_signal"
    else:
        classification = "market_priced_no_signal"

    return NameResult(
        ticker=ticker,
        name=name,
        subsector=subsector,
        prior_price_regime=prior_price_regime,
        daily_vol=round(daily_vol, 4),
        policy_ratio=round(policy_ratio, 2),
        on_window_returns=len(on),
        off_window_returns=len(off),
        price_regime=price_regime,
        policy_signal=policy_signal,
        classification=classification,
        cache_hit=cache_hit,
        error=None if series else "no usable close prices",
        data_days=len(series),
    )


def aggregate_verdict(results: list[NameResult]) -> tuple[str, str]:
    beacons = [r for r in results if r.is_beacon]
    strong = [r for r in beacons if r.policy_ratio >= STRONG_RATIO]
    if len(strong) >= 2:
        verdict = "PASS"
        rationale = (
            f"{len(strong)} names clear the strong threshold (ratio >= {STRONG_RATIO}): "
            + ", ".join(r.ticker for r in strong)
            + ". The narrative->price channel is real; proceed to sector resolution."
        )
    elif strong or len(beacons) >= 2:
        verdict = "CONDITIONAL"
        narrowed = ", ".join(r.ticker for r in (strong or beacons))
        rationale = (
            f"Signal found but weaker than ideal ({len(strong)} strong, {len(beacons)} total "
            f"beacons). Narrow the beacon set to: {narrowed}."
        )
    elif beacons:
        verdict = "CONDITIONAL"
        narrow = ", ".join(r.ticker for r in beacons)
        rationale = f"One beacon ({narrow}); narrow the beacon set but validate more names."
    else:
        verdict = "FAIL"
        rationale = (
            "No market-priced name reacts to policy dates (administered pricing dominates or "
            "policy announcements are not market-moving). The amplifier thesis is falsified "
            "for this window; do not proceed to sector resolution."
        )
    return verdict, rationale


async def fetch_daily_transaction(ticker: str) -> tuple[list | None, bool]:
    """Cache-first daily transactions for a ticker. Returns (data, cache_hit)."""
    cached = await cache.get(ticker)
    if cached and "daily_transaction" in cached:
        record_sectors_cache_hit()
        return cached["daily_transaction"], True
    data = await sectors_client.get_daily_transaction(ticker)
    await cache.merge(ticker, "daily_transaction", data, ttl=settings.EVIDENCE_CACHE_TTL_DAILY)
    return data, False


async def run_precheck(policy_events: list[PolicyEvent] | None = None, window_days: int = POLICY_WINDOW_DAYS) -> PrecheckReport:
    events = list(policy_events or ENERGY_POLICY_EVENTS)
    policy_dates = [e["date"] for e in events]
    results: list[NameResult] = []

    for candidate in CANDIDATE_ENERGY_NAMES:
        try:
            tx, cache_hit = await fetch_daily_transaction(candidate["ticker"])
            results.append(classify_signal_for_name(
                candidate["ticker"],
                tx or [],
                policy_dates,
                window_days=window_days,
                name=candidate["name"],
                subsector=candidate["subsector"],
                prior_price_regime=candidate["prior_price_regime"],
                cache_hit=cache_hit,
            ))
        except Exception as exc:  # noqa: BLE001 — keep the pre-check running
            results.append(NameResult(
                ticker=candidate["ticker"],
                name=candidate["name"],
                subsector=candidate["subsector"],
                prior_price_regime=candidate["prior_price_regime"],
                daily_vol=0.0,
                policy_ratio=0.0,
                on_window_returns=0,
                off_window_returns=0,
                price_regime="unknown",
                policy_signal="inert",
                classification="fetch_failed",
                cache_hit=False,
                error=str(exc),
            ))

    verdict, rationale = aggregate_verdict(results)
    return PrecheckReport(
        verdict=verdict,
        rationale=rationale,
        window_days=window_days,
        policy_events=events,
        results=results,
    )


def _fmt_row(r: NameResult) -> str:
    status = r.error or r.classification
    return (
        f"| {r.ticker} | {r.name} | {r.subsector} | {r.daily_vol:.2f}% | "
        f"{r.policy_ratio if r.data_days else '—'} | {r.on_window_returns} / {r.off_window_returns} | "
        f"{r.price_regime} | {r.policy_signal} | {status} |"
    )


def format_report_markdown(report: PrecheckReport, data_note: str) -> str:
    lines = [
        "# T1 Pre-check: does energy-policy narrative move stock prices?",
        "",
        f"**Verdict:** {report.verdict}",
        "",
        f"**Rationale:** {report.rationale}",
        "",
        f"**Beacon list (narrowed, market-priced):** {', '.join(report.beacon_list) or '—'}",
        "",
        f"Window: {report.window_days} trading days each side of an announcement. "
        "Daily vol floor for market pricing: {:.2f}% — ratio threshold: {:.1f}x — strong: {:.1f}x.".format(
            MIN_DAILY_VOL, MIN_POLICY_RATIO, STRONG_RATIO
        ),
        "",
        data_note,
        "",
        "## Candidate names",
        "",
        "| Ticker | Name | Subsector | Daily vol | Policy ratio | On/Off returns | Price regime | Policy signal | Classification |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    lines.extend(_fmt_row(r) for r in report.results)
    lines += ["", "## Policy events overlaid", ""]
    lines += [
        f"- **{e['date']}** — {e['title']} ({e['subsector']}{'' if e.get('verified') else ', UNVERIFIED placeholder'})"
        for e in report.policy_events
    ]
    return "\n".join(lines) + "\n"